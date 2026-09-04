# store.py - Mini Redis의 두뇌. 데이터 + LRU + TTL을 관리한다.
#
# [전체 그림]
#   ChainedHashMap   : key -> Entry 저장 (빠른 찾기 담당)
#   DoublyLinkedList : 사용 순서 기록 (맨 앞 = 방금 쓴 것, 맨 뒤 = 가장 오래된 것)
#   MinHeap          : 만료 예약 목록 ((만료시각, 키) - 제일 급한 게 맨 위)
#
# [used_memory 공식] = Σ( len(utf8(키)) + len(utf8(값)) )  <- 요구사항 고정
# [LRU 규칙] SET 후 메모리 초과면 -> 이하가 될 때까지 '맨 뒤(가장 오래 안 쓴)'부터 제거
#
# ※ 제약 준수: dict / set / collections 사용 금지. 전부 우리가 만든 자료구조를 쓴다.

import math
import time

from .doubly_linked_list import DoublyLinkedList, Node
from .hashmap import ChainedHashMap
from .heap import MinHeap


class OOMError(Exception):
    """메모리가 부족해서 저장할 수 없을 때 발생시키는 오류."""


class Entry:
    """저장소에 실제로 들어가는 데이터 한 덩어리.

    key       : 키 문자열
    value     : 값 문자열
    lru_node  : LRU 줄에서 내 위치 (O(1) 이동/제거용 꼬리표)
    expire_at : 만료되는 시각(초). 만료 설정이 없으면 None
    """

    def __init__(self, key: str, value: str, lru_node: Node):
        self.key = key
        self.value = value
        self.lru_node = lru_node
        self.expire_at = None

    def byte_size(self) -> int:
        """요구사항 공식대로 이 엔트리의 메모리 사용량을 계산한다."""
        return len(self.key.encode("utf-8")) + len(self.value.encode("utf-8"))


class RedisStore:
    """Mini Redis의 핵심 저장소 클래스."""

    def __init__(self):
        self.data_map = ChainedHashMap()      # key -> Entry
        self.lru_list = DoublyLinkedList()    # 최신순 줄 (맨 앞이 가장 최근)
        self.ttl_heap = MinHeap()             # 만료 예약 더미
        self.used_memory = 0                  # 현재 메모리 사용량
        self.maxmemory = 0                    # 0 = 무제한
        self.evicted_keys = 0                 # LRU로 밀려난 키 누적 수

    # ------------------------------------------------------------------
    # 만료(TTL) 처리
    # ------------------------------------------------------------------

    def purge_if_expired(self, key: str) -> bool:
        """키가 이미 만료됐으면 지워버리고 True를 돌려준다.

        모든 '키 기반 명령'은 일을 보기 전에 이 함수를 먼저 불러야 한다.
        만료된 키는 '없는 키'와 똑같이 처리하기 때문이다.
        """
        entry = self.data_map.get(key)
        if entry is None:
            return False                       # 애초에 없는 키
        if entry.expire_at is not None and time.time() >= entry.expire_at:
            self._remove_entry(entry)          # 유통기한 지남 -> 완전 삭제
            return True
        return False

    # ------------------------------------------------------------------
    # 내부 도우미
    # ------------------------------------------------------------------

    def _remove_entry(self, entry: Entry) -> None:
        """엔트리를 모든 구조(지도/줄)에서 빼고 메모리 사용량도 줄인다.

        TTL 더미(heap)는 굳이 건드리지 않는다(lazy deletion).
        나중에 pop 됐을 때 "실제로 없는 키면 무시"하면 되기 때문.
        """
        self.lru_list.remove_node(entry.lru_node)  # LRU 줄에서 제거 O(1)
        self.data_map.remove(entry.key)            # 해시맵에서 제거
        self.used_memory -= entry.byte_size()      # 메모리 사용량 차감

    def _evict_until_under_limit(self) -> None:
        """maxmemory를 넘는 동안 가장 오래 안 쓴 키부터 계속 지운다."""
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            if self.lru_list.is_empty():
                break                              # 지울 게 없으면 중단
            victim_entry = self.lru_list.tail.data  # 맨 뒤 = 가장 오래 안 쓴 것
            self._remove_entry(victim_entry)
            self.evicted_keys += 1                 # 요구사항: 누적 카운트

    # ------------------------------------------------------------------
    # String 명령어 구현
    # ------------------------------------------------------------------

    def set_key(self, key: str, value: str) -> str:
        """SET 명령. 성공 시 OK, 메모리 부족이면 OOM 오류 발생."""
        new_size = len(key.encode("utf-8")) + len(value.encode("utf-8"))
        # 단일 엔트리 자체가 한계를 넘으면 아예 받지 않는다 (요구사항)
        if self.maxmemory > 0 and new_size > self.maxmemory:
            raise OOMError(
                f"OOM command not allowed when used_memory > '{self.maxmemory}'"
            )

        old_entry = self.data_map.get(key)
        if old_entry is not None:
            # 기존 키 덮어쓰기: 이전 값의 메모리를 빼고, TTL은 초기화한다
            self.used_memory -= old_entry.byte_size()
            old_entry.value = value
            old_entry.expire_at = None             # 요구사항: 덮어쓰면 TTL 삭제
            self.used_memory += new_size
            self.lru_list.move_to_front(old_entry.lru_node)  # 방금 씀 표시
        else:
            # 새 키: LRU 줄 맨 앞에 세우고 해시맵에 등록
            node = self.lru_list.insert_front(None)
            entry = Entry(key, value, node)
            node.data = entry                      # 노드에 엔트리 연결
            self.data_map.put(key, entry)
            self.used_memory += new_size

        self._evict_until_under_limit()            # 넘치면 오래된 것부터 정리
        return "OK"

    def get_key(self, key: str):
        """GET 명령. 값 또는 None(nil).

        주의: 만료로 삭제된 경우 LRU 갱신을 하지 않는다 (요구사항).
        """
        self.purge_if_expired(key)                 # 먼저 만료 검사!
        entry = self.data_map.get(key)
        if entry is None:
            return None
        self.lru_list.move_to_front(entry.lru_node)  # 읽었으니 최신 표시
        return entry.value

    def delete_key(self, key: str) -> bool:
        """DEL 명령. 지웠으면 True, 없었으면 False."""
        self.purge_if_expired(key)                 # 만료된 키는 '없는 키'
        entry = self.data_map.get(key)
        if entry is None:
            return False
        self._remove_entry(entry)
        return True

    def exists_key(self, key: str) -> bool:
        """EXISTS 명령. (만료 검사 먼저)"""
        self.purge_if_expired(key)
        return self.data_map.contains(key)

    def dbsize(self) -> int:
        """DBSIZE 명령. 현재 키 개수."""
        return self.data_map.size()

    def all_keys(self) -> list:
        """KEYS 명령. 전체 키 목록."""
        return self.data_map.keys()

    # ------------------------------------------------------------------
    # 메모리 관리
    # ------------------------------------------------------------------

    def config_set_maxmemory(self, max_bytes: int) -> str:
        """CONFIG SET maxmemory 명령. 0은 무제한."""
        self.maxmemory = max_bytes
        if max_bytes == 0:
            return "OK"
        self._evict_until_under_limit()            # 한계 낮추면 즉시 정리
        return "OK"

    def info_memory(self) -> list:
        """INFO memory 명령. 3개 항목을 리스트로 돌려준다."""
        return [
            f"used_memory:{self.used_memory}",
            f"maxmemory:{self.maxmemory}",
            f"evicted_keys:{self.evicted_keys}",
        ]

    # ------------------------------------------------------------------
    # TTL 명령어
    # ------------------------------------------------------------------

    def expire_key(self, key: str, seconds: int) -> int:
        """EXPIRE 명령. 설정 성공 1, 없는 키 0.

        seconds <= 0 이면 '즉시 만료'로 처리한다 (있으면 삭제 후 1).
        """
        self.purge_if_expired(key)
        entry = self.data_map.get(key)
        if entry is None:
            return 0                               # 없는 키
        if seconds <= 0:
            self._remove_entry(entry)              # 즉시 만료 = 바로 삭제
            return 1
        entry.expire_at = time.time() + seconds    # 만료 시각 기억
        self.ttl_heap.push((entry.expire_at, key)) # 만료 예약 더미에 추가
        return 1

    def ttl_of_key(self, key: str) -> int:
        """TTL 명령. 없음 -2 / 만료설정없음 -1 / 남은 초 N."""
        self.purge_if_expired(key)                 # 만료된 키는 -2가 된다
        entry = self.data_map.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        remaining = entry.expire_at - time.time()
        if remaining <= 0:
            return 0                               # 이 순간 만료 경계
        return int(math.ceil(remaining))           # 남은 초 (올림)

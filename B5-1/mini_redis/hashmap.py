# hashmap.py - 해시맵 (체이닝 방식, 직접 구현)
#
# [개념] 해시맵 = "이름표 계산으로 바로 찾아가는 창고".
#       키(문자열)를 해시 함수로 숫자로 바꾸고,
#       그 숫자를 방(버킷) 개수로 나눈 나머지가 곧 방 번호다.
#
# [충돌과 체이닝] 서로 다른 키가 같은 방 번호에 배정되는 일을 '충돌'이라 하고,
#       충돌한 항목들을 그 방 안에서 연결 리스트로 줄 세워두는 방식이 '체이닝'이다.
#       여기서는 doubly_linked_list.py의 이중 연결 리스트를 재사용했다. (요구사항 권장)
#
# [확장] 저장 개수 / 방 개수 (로드 팩터) 가 0.75를 넘으면 방을 2배로 늘리고
#        모든 항목을 다시 배치(rehash)한다.
#
# ※ 제약 준수: dict / set / collections 사용 금지.
#   버킷 보관함은 "고정 길이 배열 + 인덱스 접근" 수준으로만 list를 쓴다.

from .doubly_linked_list import DoublyLinkedList


class Pair:
    """해시맵 한 칸에 실제로 저장되는 (키, 값) 짝."""

    def __init__(self, key: str, value):
        self.key = key
        self.value = value


class ChainedHashMap:
    """체이닝 방식 해시맵.

    _buckets: 각 방(bucket)에 이중 연결 리스트 하나씩 들어있는 보관함.
              비어 있는 방은 None으로 둔다 (미리 만들지 않음).
    """

    def __init__(self, initial_buckets: int = 8):
        self._bucket_count = initial_buckets
        self._buckets = [None] * initial_buckets  # 고정 길이 배열 (인덱스 접근만 사용)
        self._count = 0                           # 지금 저장된 항목 수

    def __len__(self) -> int:
        return self._count

    # ---------------- 해시 함수 (직접 설계) ----------------

    def _hash(self, key: str) -> int:
        """문자열 키 -> 방 번호.

        원리: 글자 코드값에 31(소수)을 곱해가며 누적한다.
        소수를 곱하면 비슷한 키들이 방 전체에 고루 퍼진다(충돌 감소).
        마지막에 방 개수로 나눈 나머지 = 방 번호 (항상 범위 안).
        """
        h = 0
        for ch in key:
            code = ord(ch)                      # 글자 -> 숫자 코드
            h = (h * 31 + code) % self._bucket_count
        return h

    # ---------------- 기본 메서드들 ----------------

    def put(self, key: str, value):
        """키-값을 저장한다. 이미 있던 키면 값을 덮어쓴다.

        돌려주는 값: 이전에 있던 값(덮어썼으면), 없었으면 None.
        """
        index = self._hash(key)
        chain = self._buckets[index]
        if chain is not None:
            for pair in chain.iter_from_front():     # 이 방 안에서 키 찾기
                if pair.key == key:
                    old_value = pair.value
                    pair.value = value               # 덮어쓰기
                    return old_value
        # 새 키다: 방이 비어있으면 줄을 새로 만들고 맨 앞에 넣는다
        if chain is None:
            chain = DoublyLinkedList()
            self._buckets[index] = chain
        chain.insert_front(Pair(key, value))
        self._count += 1
        self._maybe_rehash()                          # 너무 붐비면 방 확장
        return None

    def get(self, key: str):
        """키로 값을 찾는다. 없으면 None."""
        chain = self._buckets[self._hash(key)]
        if chain is None:
            return None
        for pair in chain.iter_from_front():
            if pair.key == key:
                return pair.value
        return None

    def contains(self, key: str) -> bool:
        """키가 저장되어 있는지만 확인."""
        return self.get(key) is not None

    def remove(self, key: str):
        """키를 삭제하고 그 값을 돌려준다. 없으면 None."""
        chain = self._buckets[self._hash(key)]
        if chain is None:
            return None
        cur = chain.head
        while cur is not None:               # 이 방의 줄을 따라가며
            if cur.data.key == key:
                removed = chain.remove_node(cur)  # 노드 위치를 알므로 즉시 제거
                self._count -= 1
                return removed.value
            cur = cur.next
        return None

    def keys(self) -> list:
        """저장된 모든 키 목록을 리스트로 돌려준다 (순서는 중요하지 않음)."""
        result = []
        for i in range(self._bucket_count):   # 모든 방을 확인
            chain = self._buckets[i]
            if chain is None:
                continue
            for pair in chain.iter_from_front():
                result.append(pair.key)
        return result

    def size(self) -> int:
        """저장된 항목 수."""
        return self._count

    # ---------------- 확장(rehash) ----------------

    def _maybe_rehash(self) -> None:
        """로드 팩터(개수/방개수)가 0.75를 넘으면 방을 2배로 늘린다.

        방이 좁으면 한 방에 항목이 몰려서 느려진다.
        방을 늘린 뒤 모든 항목을 새 방 번호에 다시 배치해야 한다.
        """
        if self._count <= self._bucket_count * 0.75:
            return                            # 아직 여유 있음
        old_chains = self._buckets            # 기존 내용 잠깐 보관
        self._bucket_count *= 2               # 방 개수 2배
        self._buckets = [None] * self._bucket_count
        self._count = 0                       # put()에서 다시 세도록 초기화
        for chain in old_chains:
            if chain is None:
                continue
            for pair in chain.iter_from_front():
                self.put(pair.key, pair.value)  # 새 방 번호로 재배치

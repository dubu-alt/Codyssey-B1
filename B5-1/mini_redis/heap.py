# heap.py - 최소 힙 (Min Heap, 직접 구현)
#
# [개념] 힙 = "부모가 항상 자식보다 작다"는 규칙을 지키는 나무 구조.
#       그래서 맨 위(루트)에는 항상 '가장 작은 값'이 있다.
#       배열로 표현한다: i번째의 자식은 2i+1번째와 2i+2번째.
#
# [왜 쓰나] TTL 만료 관리에서 "가장 먼저 만료될 (시각, 키)"를
#           계속 물어봐야 한다. 만료 시각이 가장 작은 것 = 루트에 있으므로
#           peek() 한 번으로 즉답이 가능하다. 전체 정렬이 필요 없다!
#
# ※ 제약 준수: 내부 저장소는 list를 "배열"로만 사용. dict/set/collections 금지.


class MinHeap:
    """최소 힙. 요소끼리 서로 비교 가능해야 한다.

    여기서는 (expire_at, key) 형태의 튜플을 넣는다.
    튜플 비교 규칙상 첫 값(expire_at)이 같으면 두 번째 값(key)으로 비교된다.
    """

    def __init__(self):
        self._items = []  # 힙 본체 (배열)

    def __len__(self) -> int:
        return len(self._items)

    def size(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    # ---------------- 공개 메서드 ----------------

    def push(self, item) -> None:
        """요소를 추가한다. O(log n).

        일단 배열 맨 끝에 넣고(_append), 부모와 비교하며 위로 올린다.
        """
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)  # 새 원소 위치에서 시작

    def pop(self):
        """'가장 작은' 요소를 꺼내서 돌려준다. O(log n).

        루트(0번)를 빼고, 대신 마지막 원소를 루트로 올린 다음
        자식들과 비교하며 알맞은 자리까지 내린다.
        """
        if not self._items:
            return None
        smallest = self._items[0]               # 답은 항상 0번(루트)
        last = self._items.pop()                # 마지막 원소를 떼어내서
        if self._items:
            self._items[0] = last               # 루트 자리에 놓고
            self._heapify_down(0)               # 아래로 내려 보낸다
        return smallest

    def peek(self):
        """가장 작은 요소를 꺼내지 않고 보기만 한다. O(1)."""
        if not self._items:
            return None
        return self._items[0]

    # ---------------- 내부 정리 함수들 ----------------

    def _heapify_up(self, index: int) -> None:
        """index 위치의 원소를 부모와 비교하며 필요하면 위로 올린다.

        "나"가 부모보다 작으면 자리를 바꾼다. 더 큰 부모를 만나면 멈춘다.
        """
        while index > 0:
            parent = (index - 1) // 2           # 부모 인덱스 계산법
            if self._items[index] < self._items[parent]:
                self._swap(index, parent)       # 자식이 더 작으면 교환
                index = parent                  # 이제 내 위치는 부모 자리
            else:
                break                           # 규칙을 만족하면 끝

    def _heapify_down(self, index: int) -> None:
        """index 위치의 원소를 자식과 비교하며 필요하면 아래로 내린다.

        두 자식 중 '더 작은 쪽'과 비교해서 내가 더 크면 교환한다.
        """
        size = len(self._items)
        while True:
            left = index * 2 + 1                # 왼쪽 자식 인덱스
            right = index * 2 + 2               # 오른쪽 자식 인덱스
            smallest = index
            if left < size and self._items[left] < self._items[smallest]:
                smallest = left                 # 왼쪽 자식이 나보다 작으면 후보 변경
            if right < size and self._items[right] < self._items[smallest]:
                smallest = right                # 오른쪽도 확인
            if smallest == index:
                break                           # 나가 제일 작으면 규칙 만족, 끝
            self._swap(index, smallest)
            index = smallest                    # 내려간 자리에서 반복

    def _swap(self, a: int, b: int) -> None:
        """배열 안의 두 원소 자리를 바꾼다."""
        self._items[a], self._items[b] = self._items[b], self._items[a]

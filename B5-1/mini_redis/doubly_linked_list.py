# doubly_linked_list.py - 이중 연결 리스트 (직접 구현)
#
# [개념] 노드 = 데이터 + 화살표 2개(앞 사람, 뒷 사람).
#       노드들이 앞뒤로 손을 잡은 줄이라고 상상하면 된다.
#
# [왜 쓰나] 줄의 "맨 앞에 끼워 넣기", "아는 위치에서 빼기"가
#           다른 자료를 건드리지 않고 즉시(O(1)) 가능하기 때문.
#           LRU(가장 오래 안 쓴 키 추적)에 딱 맞는 구조다.
#
# ※ 제약 준수: dict / set / collections 사용 없이 만들었다.


class Node:
    """연결 리스트의 칸 하나. 앞(prev)과 뒤(next) 손잡이를 가진다."""

    def __init__(self, data):
        self.prev = None  # 바로 앞 노드를 가리키는 화살표
        self.next = None  # 바로 뒤 노드를 가리키는 화살표
        self.data = data  # 이 칸에 실제로 담긴 값


class DoublyLinkedList:
    """앞뒤로 연결된 줄. head(첫 칸)와 tail(마지막 칸)만 기억한다."""

    def __init__(self):
        self.head = None  # 줄의 맨 앞 노드 (비어있으면 None)
        self.tail = None  # 줄의 맨 뒤 노드
        self._size = 0    # 줄에 몇 개가 들어있는지

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def insert_front(self, data) -> Node:
        """맨 앞에 새 칸을 끼워 넣는다. O(1).

        새 노드의 next를 기존 head로 연결하고,
        기존 head의 prev를 새 노드로 연결하면 끝.
        """
        node = Node(data)
        if self.head is None:          # 빈 줄이면
            self.head = node           # 이 노드가 첫 번째이자
            self.tail = node           # 마지막 노드가 된다
        else:
            node.next = self.head      # 새노드 -> 기존첫칸
            self.head.prev = node      # 기존첫칸 -> 새노드
            self.head = node           # head 표시를 새 노드로 옮김
        self._size += 1
        return node                    # 나중에 remove_node()에 쓰라고 노드를 돌려줌

    def insert_back(self, data) -> Node:
        """맨 뒤에 새 칸을 붙인다. O(1). (insert_front의 거울상)"""
        node = Node(data)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self._size += 1
        return node

    def remove_front(self):
        """맨 앞 칸을 빼서 그 데이터를 돌려준다. O(1)."""
        if self.head is None:
            return None                # 빈 줄이면 뺄 게 없음
        node = self.head
        return self.remove_node(node)

    def remove_back(self):
        """맨 뒤 칸을 빼서 그 데이터를 돌려준다. O(1)."""
        if self.tail is None:
            return None
        node = self.tail
        return self.remove_node(node)

    def remove_node(self, node: Node):
        """'아는' 노드를 줄에서 제거한다. O(1).

        포인트: 처음부터 찾아가지 않는다! 이미 노드를 갖고 있으면
        앞뒤 노드의 손잡이만 서로 이어주면 되기 때문이다.
        """
        if node.prev is not None:
            node.prev.next = node.next  # 앞사람의 뒷손을 뒷사람에게
        else:
            self.head = node.next       # 제거된 게 첫 칸이면 head 갱신
        if node.next is not None:
            node.next.prev = node.prev  # 뒷사람의 앞손을 앞사람에게
        else:
            self.tail = node.prev       # 제거된 게 마지막 칸이면 tail 갱신
        self._size -= 1
        return node.data

    def move_to_front(self, node: Node) -> None:
        """아는 노드를 맨 앞으로 옮긴다. O(1). (= 빼고 + 맨 앞에 넣고)"""
        if self.head is node:
            return                      # 이미 맨 앞이면 할 일 없음
        self.remove_node(node)
        self.insert_front_data(node)

    def insert_front_data(self, node: Node) -> None:
        """'새 노드 객체'를 그대로 맨 앞에 연결한다. (move_to_front 내부용)

        insert_front()는 새 Node를 만들지만, 여기선 기존 노드를 재활용한다.
        """
        if self.head is None:
            self.head = node
            self.tail = node
            node.prev = node.next = None
        else:
            node.prev = None
            node.next = self.head
            self.head.prev = node
            self.head = node
        self._size += 1

    def iter_from_front(self):
        """맨 앞부터 차례대로 데이터를 넘겨주는 제너레이터."""
        cur = self.head
        while cur is not None:
            yield cur.data
            cur = cur.next

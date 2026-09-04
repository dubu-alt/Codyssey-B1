# algorithms.py - 탐색/정렬 알고리즘 모음 (전부 직접 구현)
#
# ※ 제약: sorted(), list.sort() 등 정렬 표준 API 사용 금지!
#   그래서 병합 정렬(merge sort)을 직접 만들었다.
#
# 이 파일에 들어 있는 것들:
#   merge_sort        : 정렬 (직접 구현)
#   topo_order        : 부모가 자식보다 먼저 나오는 순서 (위상 정렬 성격)
#   bfs_shortest_path : 두 커밋 사이 최단 경로 (BFS + 사전순 동률 처리)
#   find_ancestors    : 어떤 커밋의 모든 조상 찾기
#
# dict / set 사용은 허용된다. 방문 기록(visited)으로 무한 루프를 막는 게 핵심.


def merge_sort(items: list, compare) -> list:
    """병합 정렬. 평균/최악 모두 O(n log n), '안정 정렬'이다.

    [원리] 절반씩 쪼개서 각각 정렬한 뒤, 두 덩어리를 순서대로 섞는다.
    [compare] "앞의 것이 뒤의 것보다 앞이면 0 이하"를 돌려주는 기준 함수.
              기준을 바꾸고 싶으면 compare만 바꾸면 된다 (date/author).
    """
    if len(items) <= 1:
        return list(items)                    # 원소 1개 이하면 이미 정렬 완료

    mid = len(items) // 2
    left = merge_sort(items[:mid], compare)   # 왼쪽 절반을 재귀로 정렬
    right = merge_sort(items[mid:], compare)  # 오른쪽 절반도 재귀로 정렬

    merged = []                               # 두 줄을 섞은 결과
    i = 0                                     # 왼쪽 줄에서 볼 위치
    j = 0                                     # 오른쪽 줄에서 볼 위치
    while i < len(left) and j < len(right):
        # 같은 값일 때 왼쪽을 먼저 넣으므로 원래 순서가 유지된다(안정성).
        if compare(left[i], right[j]) <= 0:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    # 한쪽 줄이 남으면 통째로 붙인다 (이미 정렬된 상태라 그대로 이어붙임)
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def topo_order(commits: list) -> list:
    """'부모가 항상 자식보다 먼저' 나오도록 커밋들을 배열한다.

    [방법] DFS 후위 순회:
      1) 아직 기록 안 된 커밋 하나를 고른다
      2) 그 부모들을 '먼저' 재귀적으로 기록하고
      3) 마지막에 자기 자신을 기록한다
    이렇게 하면 모든 커밋에서 조상들이 항상 앞쪽에 오게 된다.

    visited 집합으로 같은 커밋을 두 번 처리하는 것을 막는다.
    (사이클이 없는 DAG가 보장되므로 재귀가 끝없이 도는 일은 없다)
    """
    visited = set()
    ordered = []

    def visit(commit):
        if commit.hash in visited:
            return                     # 이미 처리했으면 건너뛴다
        visited.add(commit.hash)
        for parent in commit.parents:  # (1) 부모 먼저
            visit(parent)
        ordered.append(commit)         # (2) 그다음 자신

    for commit in commits:             # 입력 순서대로 시작점을 시도
        visit(commit)
    return ordered


def find_ancestors(start) -> list:
    """start 커밋에서 부모 줄기를 따라 도달 가능한 '모든 조상'을 찾는다.

    DFS(깊이 우선) + visited 로 중복 방문을 막는다.
    브랜치가 합쳐진 그래프에서는 같은 조상에 여러 길로 도달하므로
    visited 가 있어야 빠짐없이, 그러나 딱 한 번씩만 방문한다.
    """
    ancestors = []
    visited = set()
    stack = list(start.parents)        # 스택: 다음에 볼 커밋 목록
    while stack:
        current = stack.pop()          # 하나 꺼내서
        if current.hash in visited:
            continue                   # 이미 본 커밋이면 건너뛴다
        visited.add(current.hash)
        ancestors.append(current)
        stack.extend(current.parents)  # 그 커밋의 부모들도 나중에 보기
    return ancestors


def bfs_shortest_path(start, target, neighbors_of) -> list:
    """두 커밋 사이 최단 경로를 찾는다. (무방향 BFS)

    [요구사항 규칙]
      - 커밋-부모 연결을 '무방향 간선'(양쪽으로 다닐 수 있는 길)으로 본다
      - 간선 수가 가장 적은 경로 = 최단 경로
      - 최단 경로가 여러 개면 hash1->hash2->... 문자열이 사전순으로
        가장 작은 것을 선택한다

    [방법]
      1) target 에서 BFS로 'target까지의 거리'를 전부 계산
      2) start에서 출발해 매 단계마다
         "거리가 1 줄어드는 이웃 중 hash가 가장 작은 것"을 고른다
      해시 길이가 모두 같아서, 이렇게 고르면 문자열 사전순 최소 경로가 된다.
      경로가 없으면 None을 돌려준다.
    """
    if start.hash == target.hash:
        return [start]

    # --- 1단계: target에서부터 각 커밋까지의 거리 계산 (BFS) ---
    from collections import deque          # 큐 전용 도구 (그래프 라이브러리 아님)
    distance = {target.hash: 0}            # {hash: target까지의 거리}
    queue = deque([target])
    while queue:
        current = queue.popleft()
        for neighbor in neighbors_of(current):
            if neighbor.hash not in distance:
                distance[neighbor.hash] = distance[current.hash] + 1
                queue.append(neighbor)

    if start.hash not in distance:
        return None                        # start가 target에 닿을 길이 없다

    # --- 2단계: greedy로 사전순 최소 경로 만들기 ---
    path = [start]
    current = start
    remaining = distance[start.hash]       # 아직 남은 걸음 수
    while remaining > 0:
        candidates = []
        for neighbor in neighbors_of(current):
            if distance.get(neighbor.hash) == remaining - 1:
                candidates.append(neighbor)
        # hash가 가장 작은 이웃을 선택 (같은 길이 문자열이라 비교 가능)
        best = merge_sort(candidates, lambda a, b: (a.hash > b.hash) - (a.hash < b.hash))[0]
        path.append(best)
        current = best
        remaining -= 1
    return path

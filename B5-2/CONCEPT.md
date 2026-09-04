# B5-2. 미리 알아야 할 개념 정리 (비전공자용)

> 이 문서는 B5-2 미션(Mini Git)에 필요한 개념들을
> 비전공자도 이해할 수 있게 풀어쓴 설명서입니다.

---

## 목차
1. [Git과 커밋이란?](#1-git과-커밋이란)
2. [그래프와 DAG - 왜 순환이 없어야 하나?](#2-그래프와-dag---왜-순환이-없어야-하나)
3. [브랜치와 HEAD - "지금 어디 작업 중?" 표시판](#3-브랜치와-head---지금-어디-작업-중-표시판)
4. [위상 정렬 - 부모가 먼저 나오는 로그](#4-위상-정렬---부모가-먼저-나오는-로그)
5. [BFS(너비 우선 탐색) - 최단 경로 찾기](#5-bfs너비-우선-탐색---최단-경로-찾기)
6. [DFS/집합 추적 - 조상 찾기](#6-dfs집합-추적---조상-찾기)
7. [역색인(Inverted Index) - 책 뒤의 색인 페이지](#7-역색인inverted-index---책-뒤의-색인-페이지)
8. [정렬 알고리즘 직접 구현하기 (merge sort)](#8-정렬-알고리즘-직접-구현하기-merge-sort)
9. [REPL과 명령 파싱](#9-repl과-명령-파싱)

---

## 1. Git과 커밋이란?

**Git** = 파일들의 변경 이력을 기록하는 도구.
**커밋(commit)** = "이 시점의 스냅샷 저장" 한 건. 누가(author), 언제(timestamp), 무슨 이유(message)로 저장했는지 메타데이터를 가집니다.

커밋은 **부모 커밋**을 가리킵니다: "이 변경은 저 변경 다음이다".
이 부모 가리키기가 쌓이면 **그래프**가 됩니다.

```
[초기커밋] ← [로그인추가] ← [결제추가]   (화살표는 자식→부모)
```

이 미션에서는 파일 내용 자체는 안 따지고, **이 메타데이터 그래프**만 만듭니다.

---

## 2. 그래프와 DAG - 왜 순환이 없어야 하나?

**그래프** = 점(노드)과 선(간선)으로 이루어진 구조.
**DAG (Directed Acyclic Graph)** = 방향이 있고(Directed), **루프(사이클)가 없는**(Acyclic) 그래프.

왜 커밋 구조에 사이클이 있으면 안 되나?
- A의 부모가 B, B의 부모가 A라면 → "누가 먼저냐"를 알 수 없음
- 로그 출력이 무한 반복되거나, 조상 계산이 끝나지 않음

그래서 커밋 생성 규칙("부모는 항상 이미 존재하는 과거 커밋")이 자연스럽게 사이클을 막아줍니다.

---

## 3. 브랜치와 HEAD - "지금 어디 작업 중?" 표시판

- **브랜치(branch)** = 어떤 커밋 하나를 가리키는 이름표. 병렬 작업용.
- **HEAD** = "내가 지금 서 있는 위치". 현재 체크아웃된 브랜치(또는 커밋)를 가리킴.

```
main      ──→ [c3 결제추가]
feature   ──→ [c2 로그인추가]
HEAD ──→ main
```

동작:
- `BRANCH feature`: 지금 HEAD가 보는 커밋을 feature도 함께 가리키게 함 (복사 X, 같은 커밋 공유)
- `SWITCH feature`: HEAD만 feature로 옮김
- `COMMIT`: 새 커밋을 만들고, 그 부모를 현재 HEAD 커밋으로 설정 + 현재 브랜치가 새 커밋을 가리키게 갱신

> 구현 팁: 커밋 조회가 빨라야 하니 "hash → 커밋 객체" 조회는 dict 사용 가능합니다.

---

## 4. 위상 정렬 - 부모가 먼저 나오는 로그

요구사항: LOG는 "최신순 나열"이 아니라 **부모 커밋이 항상 자식보다 먼저 출력**되어야 합니다.
이런 정렬을 **위상 정렬(topological sort)**이라고 합니다.

간단한 방법 (DFS 후위 순회):
1. 아직 출력 안 된 커밋을 하나 고른다
2. 그 커밋의 **부모들을 먼저 재귀적으로 출력**하고
3. 마지막에 자기 자신을 출력한다

```python
def topo_visit(commit, visited, out):
    """부모를 먼저 방문한 뒤 자신을 기록하는 함수"""
    if commit.hash in visited:
        return                    # 이미 처리한 커밋이면 건너뜀
    visited.add(commit.hash)
    for parent in commit.parents: # 1) 부모 먼저
        topo_visit(parent, visited, out)
    out.append(commit)            # 2) 그다음 자신
```

이렇게 하면 모든 커밋에서 "조상들이 항상 앞에" 오는 순서가 보장됩니다.

---

## 5. BFS(너비 우선 탐색) - 최단 경로 찾기

`PATH <c1> <c2>`: 두 커밋 사이의 **가장 짧은 연결**(간선 수 최소)을 찾습니다.
단, 커밋-부모 연결을 **무방향**(양방향으로 오갈 수 있는) 간선으로 봅니다.

**BFS** = 시작점에서 출발해서 **가까운 이웃부터 차례차례** 넓혀가며 탐색.
성질: BFS는 **처음 도달했을 때가 곧 최단 거리**입니다.

필요한 도구:
- **큐(queue)**: 다음에 방문할 곳 목록. 먼저 넣은 것부터 꺼냄 (`collections` 금지지만 list의 `append`/`pop(0)` 또는 인덱스 포인터로 구현 가능)
- **visited 집합**: 이미 방문한 커밋 재방문 방지 (사이클 대비)

경로 복원: 큐에 넣을 때 "어디서 왔는지(came_from)"를 기록해두면, 도착점에서 시작점까지 거꾸로 따라가며 경로를 만들 수 있습니다.

동률 처리(요구사항): 최단 경로가 여러 개면 `hash1->hash2->...` 문자열 기준 **사전순 최소** 선택.
구현 팁: 이웃을 방문 예약할 때 해시 문자열 순으로 정렬하거나, 같은 거리의 후보들 중 사전순으로 앞선 것을 우선 선택하도록 처리.

---

## 6. DFS/집합 추적 - 조상 찾기

`ANCESTORS <hash>`: 특정 커밋에서 **도달 가능한 모든 부모 쪽 커밋**을 전부 출력.

방법: hash에서 출발해 parents를 따라 쭉쭉 방문하면서, 방문한 적 없는 커밋마다 결과에 추가.

```python
def find_ancestors(start):
    """시작 커밋의 모든 조상을 모으는 함수 (BFS/DFS 아무거나)"""
    result = []
    visited = set()
    stack = [start]               # DFS는 줄 대신 스택(또는 재귀)
    while stack:
        cur = stack.pop()
        for p in cur.parents:
            if p.hash not in visited:
                visited.add(p.hash)
                result.append(p)
                stack.append(p)   # 부모의 부모도 계속 탐색
    return result
```

핵심은 **visited로 중복 방문 막기**. 브랜치가 합쳐진 그래프에서는 같은 조상에 여러 경로로 도달하기 때문입니다.

---

## 7. 역색인(Inverted Index) - 책 뒤의 색인 페이지

**문제**: "login이 들어간 커밋 찾아줘" 할 때마다 커밋 10만 개를 하나씩 읽으면 느림 (O(n)).

**해결**: 커밋을 만들 때 **미리 단어별 목록**을 만들어두기.

```
keyword_index:
  "login"   → [d4e5f6, ...]
  "payment" → [g7h8i9, ...]
author_index:
  "Alice"   → [a1b2c3, d4e5f6, g7h8i9]
```

검색할 땐 딱 그 단어의 목록만 꺼내면 됨 → 사실상 O(1) 조회 + 결과 개수만큼만 출력.

- 키워드 정규화 규칙: 메시지를 공백 split → 전부 소문자(lower)
- `COMMIT`할 때마다 두 인덱스를 **갱신**해주는 게 포인트

---

## 8. 정렬 알고리즘 직접 구현하기 (merge sort)

`sorted()`, `list.sort()` 금지! 직접 만듭니다. 추천은 **병합 정렬(merge sort)**:

원리: "절반씩 쪼개서 각각 정렬한 뒤, 두 덩어리를 순서대로 섞기"

```
[38, 27, 43, 10]
   ├→ [38, 27] → [27, 38]
   └→ [43, 10] → [10, 43]
   섞기 → [10, 27, 38, 43]
```

```python
def merge_sort(items, compare):
    """compare 함수 기준으로 items를 정렬하는 병합 정렬"""
    if len(items) <= 1:
        return items                       # 원소 1개면 이미 정렬됨
    mid = len(items) // 2
    left = merge_sort(items[:mid], compare)   # 왼쪽 절반 정렬
    right = merge_sort(items[mid:], compare)  # 오른쪽 절반 정렬
    merged = []                            # 두 덩어리를 섞는 중
    i = j = 0
    while i < len(left) and j < len(right):
        if compare(left[i], right[j]) <= 0:  # 왼쪽이 작거나 같으면
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    return merged + left[i:] + right[j:]     # 남은 것들 붙이기
```

설명용 지식 (과제 목표):
| 알고리즘 | 평균 | 최악 | 안정 정렬? |
|----------|------|------|-----------|
| merge sort | O(n log n) | O(n log n) | O (안정) |
| quick sort | O(n log n) | O(n²) | X |
| bubble sort | O(n²) | O(n²) | O |

**안정 정렬** = 값이 같은 원소끼리는 원래 순서가 유지되는 정렬.
비교 기준 교체: `compare = lambda a, b: a.timestamp - b.timestamp` 처럼 기준 함수만 바꿔서 같은 merge_sort 재사용.

---

## 9. REPL과 명령 파싱

```python
while True:
    line = input("mini-git> ")
    if line.strip().lower() in ("exit", "quit"):
        break
    tokens = smart_split(line)   # 따옴표 안 공백은 하나의 인자로
    run(tokens)
```

파싱 주의점:
- `COMMIT "Add login feature"` → `"Add login feature"`는 **따옴표째 하나의 인자**. 단순 `.split()`으로는 안 되고, 따옴표를 인식하는 분리 함수 필요
- 명령어 비교 전 `.upper()`로 통일 (대소문자 무시 요구사항)
- `--author=Alice`, `--sort-by=date` 같은 옵션은 `=` 기준으로 key/value 분리

---

## 한 줄 요약

| 개념 | 비전공자 버전 요약 |
|------|-------------------|
| 커밋/DAG | "누가 언제 뭘 했다" 기록 + 루프 없는 부모 가리키기 |
| 브랜치/HEAD | 커밋을 가리키는 이름표 / 내 현재 위치 |
| 위상 정렬 | 부모를 항상 자식보다 먼저 보여주는 출력 순서 |
| BFS | 가까운 곳부터 넓혀가며 찾는 최단 경로 탐색 |
| 조상 탐색 | 부모 줄기를 끝까지 따라가 전부 모으기 |
| 역색인 | 미리 단어별 목록장을 만들어 검색을 즉답으로 |
| merge sort | 절반씩 쪼개 정렬 후 섞기. 빠르고 안정적 |
| REPL | 입력→실행→출력 무한 반복 대화창 |

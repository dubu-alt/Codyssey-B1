# B5-2. 파일이 언제 어떻게 바뀌었는지 기록하는 작은 프로그램 만들기 (Mini Git)

> **분야**: AI/SW 기초 | **구분**: 자료구조와 알고리즘 | **학습시간**: 80시간
> **난이도**: ★★★☆☆ (3단계)

---

## 1. 이 미션이 뭔가요?

개발자들이 쓰는 버전 관리 시스템 **Git**의 핵심 구조를 직접 구현해서,
CLI 기반 **Mini Git** 프로그램을 완성하는 미션입니다.

Git의 커밋 하나에는 **그래프 자료구조와 해시**가 담겨 있습니다.
이걸 직접 만들어보면 실제 Git의 rebase, merge, cherry-pick이 다르게 보이고, 알고리즘 공부와도 연결됩니다.

만들 것:
- 커밋(변경 기록 한 건)을 노드로 하는 **그래프(DAG)** 구조
- 브랜치 생성/전환
- 커밋 로그 출력 (**위상 정렬** 성격: 부모가 항상 자식보다 먼저)
- 두 커밋 사이의 **최단 경로 찾기** (BFS)
- 특정 커밋의 모든 **조상 탐색**
- 빠른 검색을 위한 **역색인(Inverted Index)**
- 정렬 알고리즘 **직접 구현** (`sorted()`, `list.sort()` 사용 금지!)

---

## 2. 최종 결과물

CLI 기반 Mini Git 프로그램 1개. 아래 명령어들이 정상 동작해야 합니다.

### 저장소 및 브랜치 관리
| 명령어 | 하는 일 |
|--------|---------|
| `INIT [사용자명]` | 저장소 초기화 + main 브랜치 생성/HEAD 설정 + 현재 사용자 설정 |
| `BRANCH <브랜치명>` | 현재 커밋(HEAD)을 가리키는 새 브랜치 생성 |
| `SWITCH <브랜치명>` | HEAD를 지정한 브랜치로 이동 |
| `COMMIT <메시지>` | 현재 HEAD를 부모로 하는 새 커밋 생성 (커밋 hash 포함 결과 출력) |

### 커밋 로그 및 탐색
| 명령어 | 하는 일 |
|--------|---------|
| `LOG` | 부모가 항상 자식보다 먼저 출력되는 로그 (위상 정렬 성격) |
| `PATH <commit1> <commit2>` | 두 커밋 간 최단 경로 출력 (없으면 `No path`) |
| `ANCESTORS <commit_hash>` | 해당 커밋의 도달 가능한 모든 조상 출력 |

### 검색 및 정렬
| 명령어 | 하는 일 |
|--------|---------|
| `SEARCH <키워드>` | 역색인으로 키워드가 포함된 커밋 검색 |
| `SEARCH --author=<이름>` | 특정 작성자의 커밋 검색 (역색인 기반) |
| `LOG --sort-by=date\|author` | 직접 구현한 정렬로 날짜/작성자 기준 정렬 출력 |

### CLI 인터페이스 (REPL)
- `mini-git>` 프롬프트에서 명령 반복 입력 → 파싱 → 실행 → 출력
- `exit` / `quit`로 종료

### 필수 제출물 / 실행
- 엔트리 포인트(예: `main.py`) 1개 + README.md 1개
- 실행 예: `python main.py`

---

## 3. 과제 목표 (이걸 설명할 수 있게 되어야 해요)

1. 커밋 그래프를 구현하고, Git의 커밋 구조가 왜 DAG인지 말로 설명할 수 있다.
2. "부모가 먼저 출력되는 로그"를 만들기 위해 어떤 접근(위상 정렬 성격의 출력)이 필요한지 설명할 수 있다.
3. 두 커밋 사이의 최단 경로를 찾는 방법과 특정 커밋의 모든 조상을 탐색하는 방법을 설명할 수 있다.
4. 정렬 알고리즘을 직접 구현하고, 평균/최악 시간복잡도 및 안정 정렬 여부를 설명할 수 있다.
5. 역색인의 동작 원리와, 순회 검색보다 빠른 이유를 시간복잡도 관점에서 설명할 수 있다.

---

## 4. 기능 요구 사항 (상세)

### 4-1. CLI 공통 규칙
- 명령어는 **대소문자 구분 없음** (INIT = init)
- 문자열 인자(사용자명/커밋 메시지/키워드)는 공백 포함 가능 → 따옴표로 감싸기 (예: `COMMIT "Add login feature"`)
- 옵션 표기 통일:
  - `SEARCH --author=<name>`
  - `LOG --sort-by=date|author`
- 에러 메시지 표준화: `Invalid args`, `Unknown branch: <name>`, `Unknown commit: <hash>` 등

### 4-2. 커밋 그래프 (핵심 자료구조)
- 커밋 노드 필드: `hash`, `message`, `author`, `timestamp`, `parents`
- 커밋은 **0개 이상의 부모**를 가질 수 있다
- 그래프는 **DAG**(방향성 비순환 그래프)여야 한다
- 커밋 저장소는 hash로 **빠르게 조회** 가능 (해시맵 기반; dict 사용 가능)
- hash는 세션 내 유일해야 함 (증가 카운터 기반, 난수 기반 등 방식 자유, 중복 보장 안 됨 안 됨)

### 4-3. 역색인 (Inverted Index)
- 검색 시 전체 순회 없이 후보를 바로 가져와야 함
- 키워드 추출 최소 기준: 커밋 메시지를 공백 split + 소문자 lower 정규화
- 최소 2종 인덱스 지원:
  - `keyword -> commit_hash 목록`
  - `author -> commit_hash 목록`

### 4-4. 정렬 알고리즘 직접 구현
- **`sorted()`, `list.sort()` 사용 금지**
- 비교 기준 교체 가능 (date / author)
- 평균/최악 시간복잡도와 안정 정렬 여부를 설명할 수 있어야 함 (예: merge sort = O(n log n), 안정 정렬)

### 4-5. 명령어 세부 요구
- `INIT`: main 브랜치 생성 + HEAD 설정 + author 설정
- `BRANCH`: 현재 HEAD가 가리키는 커밋을 새 브랜치가 함께 가리킴
- `SWITCH`: HEAD 이동
- `COMMIT`: 현재 HEAD를 부모로 하는 새 커밋 생성 + 역색인(author/keyword) 갱신
- `LOG`: **부모 커밋이 항상 자식보다 먼저 출력** (최신순 나열 X). 출력에 hash / author / timestamp / message 식별 가능해야 함
- `LOG --sort-by=date|author`: 직접 구현한 정렬 사용
- `PATH <c1> <c2>`:
  - 커밋-부모 연결을 **무방향 간선**으로 간주한 최단 경로 (간선 수 최소)
  - 경로 없으면 `No path` 출력
  - 여러 개면 **hash1->hash2->... 문자열 사전순 최소** 경로 선택
- `ANCESTORS <hash>`: 도달 가능한 모든 조상 커밋 출력
- `SEARCH <keyword>`: 역색인 기반 메시지 검색
- `SEARCH --author=<name>`: 역색인 기반 작성자 검색

---

## 5. 개발 환경
- Python 3.10 이상

## 6. 제약 사항
- 실행: `python main.py`
- 그래프 전용 라이브러리 금지
- 정렬 표준 API 전부 금지 (`sorted()`, `list.sort()` 등)
- 기본 자료형(list, dict, set), 문자열/파일 입출력/시간 처리는 사용 가능
- 알고리즘 로직(탐색/정렬/인덱싱)은 독립된 함수 또는 클래스로 분리
- 주요 함수/클래스에 주석 또는 docstring 작성
- 파일 내용 추적 없음 (커밋 메타데이터 중심), 네트워크 없음, 영속성(파일 저장) 불필요 (메모리 동작)

---

## 7. 실행 결과 예시 (참고용, 문구/디자인은 달라도 됨)

```
mini-git> init "Alice"
Initialized repository.
Current branch: main
Current user: Alice

mini-git> commit "Initial commit"
[main a1b2c3] Initial commit

mini-git> branch feature
Created branch: feature

mini-git> switch feature
Switched to branch: feature

mini-git> commit "Add login feature"
[feature d4e5f6] Add login feature

mini-git> switch main
Switched to branch: main

mini-git> commit "Add payment feature"
[main g7h8i9] Add payment feature

mini-git> log
commit a1b2c3 (Alice, 2024-01-15 09:00:00) [main]
Initial commit
commit d4e5f6 (Alice, 2024-01-15 09:15:00) [feature]
Add login feature
commit g7h8i9 (Alice, 2024-01-15 09:30:00) [main]
Add payment feature

mini-git> path a1b2c3 g7h8i9
Path: a1b2c3 -> g7h8i9

mini-git> search "login"
Found 1 commit:

- d4e5f6: Add login feature

mini-git> log --sort-by=author
commit a1b2c3 (Alice, 2024-01-15 09:00:00)
Initial commit
...
```

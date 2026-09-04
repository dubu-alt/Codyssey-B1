# B5-2. 체크리스트

> 하나씩 확인하면서 `[ ]`를 `[x]`로 바꿔가세요.

---

## 0. 제약 조건 (위반하면 감점!)

- [ ] `python main.py`로 실행된다
- [ ] 그래프 전용 라이브러리 사용 안 함
- [ ] **`sorted()`, `list.sort()` 사용 금지** (정렬 직접 구현)
- [ ] 기본 자료형(list/dict/set), 문자열/파일/시간 처리만 사용
- [ ] 알고리즘 로직(탐색/정렬/인덱싱)이 독립된 함수 또는 클래스로 분리됨
- [ ] 주요 함수/클래스에 주석 또는 docstring 작성

## 1. CLI 공통 규칙

- [ ] 명령어 대소문자 구분 없음 (INIT = init)
- [ ] 공백 포함 인자는 따옴표로 감싸서 처리 (예: `COMMIT "Add login feature"`)
- [ ] 옵션 표기 통일: `SEARCH --author=<name>`, `LOG --sort-by=date|author`
- [ ] 표준 에러 메시지 구현 (`Invalid args`, `Unknown branch: <name>`, `Unknown commit: <hash>`)
- [ ] `mini-git>` 프롬프트 REPL 반복 + `exit`/`quit` 종료

## 2. 커밋 그래프

- [ ] 커밋 노드에 hash / message / author / timestamp / parents 필드 존재
- [ ] 커밋이 0개 이상의 부모를 가질 수 있음
- [ ] 그래프가 DAG(사이클 없음) 구조
- [ ] hash로 커밋을 빠르게 조회 가능 (dict 등 해시맵 기반)
- [ ] hash가 세션 내 유일함 (중복 방지 보장)

## 3. 역색인 (Inverted Index)

- [ ] 검색 시 전체 커밋 순회하지 않고 후보를 바로 가져옴
- [ ] 메시지 공백 split + 소문자 정규화로 키워드 추출
- [ ] keyword → commit_hash 목록 인덱스 구현
- [ ] author → commit_hash 목록 인덱스 구현
- [ ] COMMIT 시 두 인덱스가 갱신됨

## 4. 정렬 (직접 구현)

- [ ] 정렬 알고리즘을 직접 구현했다 (예: merge sort)
- [ ] 비교 기준 교체 가능 (date / author)
- [ ] 평균/최악 시간복잡도와 안정 정렬 여부를 설명할 수 있다

## 5. 명령어 동작

- [ ] `INIT <사용자명>`: 저장소 초기화 + main 브랜치 생성 + HEAD 설정 + author 설정
- [ ] `BRANCH <이름>`: 현재 HEAD 커밋을 가리키는 새 브랜치 생성
- [ ] `SWITCH <이름>`: HEAD를 해당 브랜치로 이동
- [ ] `COMMIT <메시지>`: 현재 HEAD를 부모로 하는 새 커밋 생성, hash 출력, 역색인 갱신
- [ ] `LOG`: 부모가 항상 자식보다 먼저 출력 (위상 정렬 성격), hash/author/timestamp/message 식별 가능
- [ ] `LOG --sort-by=date`: timestamp 기준 정렬 출력
- [ ] `LOG --sort-by=author`: 작성자 기준 정렬 출력
- [ ] `PATH <c1> <c2>`: 무방향 최단 경로 출력 (간선 수 최소)
- [ ] `PATH`: 경로 없으면 `No path` 출력
- [ ] `PATH`: 여러 경로 시 사전순 최소 문자열 경로 선택
- [ ] `ANCESTORS <hash>`: 도달 가능한 모든 조상 출력
- [ ] `SEARCH <키워드>`: 역색인 기반 메시지 검색
- [ ] `SEARCH --author=<이름>`: 역색인 기반 작성자 검색

## 6. 필수 제출물

- [ ] 엔트리 포인트(main.py) 1개
- [ ] README.md 1개

## 7. 코드 품질 (본인 규칙)

- [ ] 모든 코드에 주석이 달려있다 (비전공자도 읽을 수 있게)
- [ ] 코드가 심플하고 깔끔하다

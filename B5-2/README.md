# Mini Git

Git의 핵심 구조(커밋 그래프 DAG, 브랜치, 위상 정렬, BFS, 역색인, 직접 구현한 정렬)를
직접 구현한 CLI 프로그램입니다. (`sorted()`/`list.sort()` 미사용)

## 실행 방법 (필수 제출물: main.py + README.md)

이 폴더(`B5-2`)에서:

```bash
python -m mini_git.main
# 또는
python mini_git/main.py
```

`mini-git>` 프롬프트에 명령어를 입력합니다. 종료는 `exit` 또는 `quit`.

## 명령어 목록

| 명령어 | 예시 | 설명 |
|--------|------|------|
| INIT | `init "Alice"` | 저장소 초기화 + main 브랜치 생성 + 사용자 설정 |
| COMMIT | `commit "Initial commit"` | 새 커밋 생성 (역색인 갱신) |
| BRANCH | `branch feature` | 현재 HEAD 커밋을 가리키는 새 브랜치 생성 |
| SWITCH | `switch feature` | HEAD를 해당 브랜치로 이동 |
| LOG | `log` | **부모가 항상 자식보다 먼저** 출력되는 로그 |
| LOG 정렬 | `log --sort-by=date` / `--sort-by=author` | 직접 만든 병합 정렬로 정렬 출력 |
| PATH | `path <hash1> <hash2>` | 무방향 최단 경로. 없으면 `No path`. 동률이면 사전순 최소 |
| ANCESTORS | `ancestors <hash>` | 도달 가능한 모든 조상 출력 |
| SEARCH | `search login` / `search --author=Alice` | 역색인 기반 즉시 검색 |

- 명령어는 대소문자 구분 없음 (INIT = init)
- 공백 있는 문자열은 따옴표로 감싸기
- 데이터는 메모리에서만 동작 (종료하면 사라짐 - 요구사항)

## 동작 원리 요약

- **커밋 그래프**: 부모는 항상 과거 커밋 -> 사이클 없는 DAG
- **위상 정렬**: DFS 후위 순회로 "부모 먼저" 순서 보장
- **최단 경로**: target에서 BFS로 거리 계산 후, 거리가 1 줄어드는 이웃 중 hash가 가장 작은 것을 골라 사전순 최소 경로 보장
- **역색인**: 메시지 공백 split + 소문자화한 토큰별 목록장을 미리 만들어 검색을 즉답으로
- **정렬**: 병합 정렬 직접 구현 (평균/최악 O(n log n), 안정 정렬)

## 코드 구조

```
mini_git/
├── main.py        시작점. REPL + 명령 파싱
├── graph.py       커밋/브랜치/HEAD 관리 (DAG)
├── index.py       역색인 (키워드/작성자)
└── algorithms.py  병합 정렬 / 위상 정렬 / BFS 경로 / 조상 탐색
```

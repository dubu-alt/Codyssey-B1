# B5-1. 체크리스트

> 하나씩 확인하면서 `[ ]`를 `[x]`로 바꿔가세요.

---

## 0. 제약 조건 (위반하면 감점!)

- [ ] `dict`, `set`, `collections` **사용하지 않았다** (해시맵/캐시를 내장 컬렉션으로 대체 금지)
- [ ] 버킷 배열 수준의 "고정 길이 배열/인덱스 접근"으로만 list 사용
- [ ] 해시맵 / 이중 연결 리스트 / 힙이 각각 **독립된 모듈(파일)**로 분리되어 있다
- [ ] 핵심 클래스/함수에 주석 또는 docstring 작성
- [ ] 네트워크 통신 없음, 파일 저장 없음, List/Set/Sorted Set 자료형 없음

## 1. 이중 연결 리스트

- [ ] 노드가 `prev`, `next`, `data` 필드를 가진다
- [ ] `insert_front` 구현
- [ ] `insert_back` 구현
- [ ] `remove_front` 구현
- [ ] `remove_back` 구현
- [ ] `remove_node` 구현
- [ ] `move_to_front` 구현
- [ ] 모든 삽입/삭제/이동이 O(1)이다 (순회 없음)

## 2. 해시맵 (체이닝)

- [ ] 해시 함수를 직접 설계했다
- [ ] 충돌을 체이닝으로 해결했다 (권장: 이중 연결 리스트 재사용)
- [ ] `put` 구현
- [ ] `get` 구현
- [ ] `remove` 구현
- [ ] `contains` 구현
- [ ] `keys` 구현
- [ ] `size` 구현
- [ ] 로드 팩터 0.75 초과 시 버킷 2배 확장(rehash)

## 3. 최소 힙

- [ ] `push` 구현
- [ ] `pop` 구현
- [ ] `peek` 구현
- [ ] `size` 구현
- [ ] `_heapify_up` 직접 구현
- [ ] `_heapify_down` 직접 구현
- [ ] `(expire_at, key)` 형태 요소 처리 가능

## 4. String 명령어

- [ ] `SET key value` → `OK`, LRU 추적 갱신
- [ ] `SET`: 기존 키 덮어쓰면 TTL 초기화
- [ ] `GET key` → 값 또는 `(nil)`
- [ ] `GET`: 성공 반환 시에만 LRU 갱신 (만료 삭제 건은 미갱신)
- [ ] `DEL key` → `(integer) 1/0`
- [ ] `DEL`: 데이터 + LRU + TTL 구조에서 모두 함께 제거
- [ ] `EXISTS key` → `(integer) 1/0`
- [ ] `DBSIZE` → `(integer) N`
- [ ] `KEYS` → 전체 키 목록 출력 (없으면 빈 배열 표현)

## 5. 메모리 관리 + LRU

- [ ] `CONFIG SET maxmemory <bytes>` 동작 (0 = 무제한)
- [ ] `INFO memory`에 used_memory / maxmemory / evicted_keys 출력
- [ ] used_memory = Σ(len(utf8(key)) + len(utf8(value))) 공식 준수
- [ ] maxmemory 초과 시 이하가 될 때까지 LRU 순서대로 제거
- [ ] 제거된 키 evicted_keys 누적 카운트
- [ ] 단일 엔트리가 maxmemory 초과 시 OOM 에러 출력

## 6. TTL 관리

- [ ] `EXPIRE key seconds` → `(integer) 1`, 없는 키는 `(integer) 0`
- [ ] seconds ≤ 0이면 즉시 만료 처리
- [ ] `TTL key`: 없음 -2 / 만료설정없음 -1 / 남은 초 N
- [ ] 만료된 키 조회 시 먼저 삭제 후 "없는 키"처럼 처리
- [ ] 힙으로 가장 빠른 만료를 빠르게 찾는다

## 7. 에러 표준 + CLI

- [ ] `mini-redis>` 프롬프트 REPL 반복
- [ ] `exit` / `quit` 종료
- [ ] 잘못된 명령: `(error) ERR unknown command '<cmd>'`
- [ ] 인자 개수 오류: `(error) ERR wrong number of arguments for '<cmd>' command`
- [ ] 정수 파싱 실패: `(error) ERR value is not an integer or out of range`
- [ ] OOM: `(error) OOM command not allowed when used_memory > 'maxmemory'`
- [ ] 공백 없는 값 + 큰따옴표로 감싼 값 둘 다 지원

## 8. 엣지 케이스 최소 규칙

- [ ] 만료된 키 GET → 삭제 후 `(nil)`, LRU 갱신 안 함
- [ ] SET 덮어쓰기 → TTL 초기화
- [ ] EXPIRE on 없는 키 → `(integer) 0`
- [ ] DEL → 데이터/TTL/LRU 전부 제거

## 9. 코드 품질 (본인 규칙)

- [ ] 모든 코드에 주석이 달려있다 (비전공자도 읽을 수 있게)
- [ ] 코드가 심플하고 깔끔하다

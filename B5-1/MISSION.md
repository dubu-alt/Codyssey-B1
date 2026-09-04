# B5-1. 정보를 엄청 빠르게 찾아주는 작은 저장소 만들기 (Mini Redis)

> **분야**: AI/SW 기초 | **구분**: 자료구조와 알고리즘 | **학습시간**: 80시간
> **난이도**: ★★★☆☆ (3단계)

---

## 1. 이 미션이 뭔가요?

전 세계에서 가장 널리 쓰이는 메모리 기반 데이터 저장소인 **Redis**의 핵심을,
**자료구조를 밑바닥부터 직접 구현하면서** 따라 만들어보는 미션입니다.

- 터미널에 `SET user:1 "Alice"` 처럼 명령어를 입력하면 즉시 결과가 나오는 **CLI 프로그램**
- 평소엔 Python이 알아서 해주는 해시맵(dict) 같은 걸 **직접** 만들어봅니다:
  - **해시맵** (체이닝 방식) - 이름표를 붙여서 바로 찾는 저장 방식
  - **이중 연결 리스트** - 앞뒤로 연결된 줄 (LRU 추적용)
  - **최소 힙** - "가장 먼저 만료될 것"을 빠르게 찾는 구조
- 이걸 조합해서 실제 Redis의 핵심 기능 두 가지를 체득합니다:
  - **LRU**: 메모리가 부족하면 가장 오래 안 쓴 데이터부터 자동 삭제
  - **TTL**: 데이터에 유통기한(만료 시간)을 설정

> 목적: "Redis가 왜 빠른가"를 손으로 만들어보며 설명할 수 있게 되는 것.

---

## 2. 최종 결과물

CLI 기반 **Mini Redis** 프로그램 1개. 아래 명령어들이 정상 동작해야 합니다.

### String 타입 기본 명령어 (6개)
| 명령어 | 하는 일 | 성공 출력 |
|--------|---------|-----------|
| `SET key value` | 키에 값 저장 (+ LRU 추적 갱신) | `OK` |
| `GET key` | 키의 값 조회 (+ 성공 시 LRU 갱신) | `"value"` 또는 `(nil)` |
| `DEL key` | 키 삭제 | `(integer) 1` / 없으면 `(integer) 0` |
| `EXISTS key` | 존재 여부 확인 | `(integer) 1` / `(integer) 0` |
| `DBSIZE` | 전체 키 개수 반환 | `(integer) N` |
| `KEYS` | 전체 키 목록 출력 (패턴 매칭은 미구현) | `"key1"`, `"key2"...` |

### 메모리 관리 명령어 (2개)
| 명령어 | 하는 일 |
|--------|---------|
| `CONFIG SET maxmemory <bytes>` | 최대 메모리 제한 설정 (바이트 단위, 0 = 무제한) |
| `INFO memory` | used_memory / maxmemory / evicted_keys 출력 |

### TTL 관리 명령어 (2개)
| 명령어 | 하는 일 |
|--------|---------|
| `EXPIRE key seconds` | 키에 만료 시간 설정 (초 단위) |
| `TTL key` | 남은 만료 시간 조회 |

### CLI 인터페이스 (REPL)
- `mini-redis>` 프롬프트에서 명령 입력 → 파싱 → 실행 → 출력 반복
- `exit` 또는 `quit`으로 종료

---

## 3. 과제 목표 (이걸 설명할 수 있게 되어야 해요)

1. 해시맵의 해시 함수와 충돌 해결 방식(체이닝)을 구현 코드 기반으로 설명할 수 있다.
2. 이중 연결 리스트와 해시맵을 조합하여 O(1) LRU 추적이 가능한 이유를 설명할 수 있다.
3. 힙이 TTL 만료 시간 관리에 적합한 이유를 설명할 수 있다.
4. 메모리 제한 환경에서 LRU 정책으로 데이터를 제거하는 전체 흐름(used_memory 갱신 포함)을 설명할 수 있다.

---

## 4. 기능 요구 사항 (상세)

### 4-1. 기본 자료구조 직접 구현 (내장 dict/set/collections로 대체 금지!)

**(1) 이중 연결 리스트**
- 노드 구조: `prev`, `next`, `data` 필드
- 주요 메서드: `insert_front`, `insert_back`, `remove_front`, `remove_back`, `remove_node`, `move_to_front`
- 모든 삽입/삭제/이동 연산은 **O(1)**

**(2) 해시맵 (체이닝 방식)**
- 주요 메서드: `put`, `get`, `remove`, `contains`, `keys`, `size`
- 해시 함수 **직접 설계**
- 충돌 해결은 체이닝 방식 (권장: 이중 연결 리스트 재사용)
- 로드 팩터 0.75 초과 시 버킷 **2배 확장**

**(3) 힙 (최소 힙)**
- 주요 메서드: `push`, `pop`, `peek`, `size`
- `_heapify_up`, `_heapify_down` 직접 구현
- `(expire_at, key)` 형태 요소를 다룰 수 있어야 함 (TTL 관리용)

### 4-2. String 명령어 세부 규칙
- 공통: 키 기반 명령은 실행 전 **만료 여부 먼저 확인** (만료된 키는 삭제 후 "없는 키"처럼 처리)
- `SET`: 기존 키 덮어쓰면 기존 TTL은 **초기화(삭제)**
- `GET`: 없거나 만료되면 `(nil)`. **성공 반환 시에만** LRU 갱신 (만료 삭제 건은 갱신 안 함)
- `DEL`: 삭제 시 **데이터 + LRU + TTL 구조 모두에서 함께 제거**
- `KEYS`: 전체 키 배열 출력, 없으면 `(empty array)` 등으로 표현

### 4-3. 메모리 관리 + LRU 자동 제거
- `used_memory` 공식: **Σ( len(utf8(key)) + len(utf8(value)) )** (자료구조 오버헤드는 제외)
- `maxmemory > 0`이고 SET 후 초과하면 → 이하가 될 때까지 **가장 오래 안 쓴 키(LRU)부터 제거**
- 제거된 키는 `evicted_keys` 누적 카운트
- 단일 엔트리(키+값) 자체가 maxmemory 초과 → 저장하지 않고 OOM 에러

### 4-4. TTL 관리 (힙 기반)
- `EXPIRE key seconds`: 없는 키면 `(integer) 0`, seconds ≤ 0이면 즉시 만료 처리 가능(있으면 삭제 후 1), 정상 설정 `(integer) 1`
- `TTL key`:
  - 없는 키 → `(integer) -2`
  - 있지만 만료 설정 없음 → `(integer) -1`
  - 있고 만료 설정 있음 → 남은 초 `(integer) N`

### 4-5. TTL/LRU 엣지 케이스 최소 규칙
- 만료된 키 GET → 먼저 삭제 후 `(nil)`, LRU 갱신 안 함
- SET 덮어쓰기 → TTL 초기화
- EXPIRE on 없는 키 → `(integer) 0`
- DEL → 데이터/TTL/LRU 전부에서 제거
- 힙으로 "가장 빠른 만료"를 빠르게 찾을 수 있으면 됨 (lazy deletion 등 구현 선택 자유)

### 4-6. 에러 처리 표준 + CLI
- 에러 형식:
  ```
  (error) ERR unknown command '<cmd>'
  (error) ERR wrong number of arguments for '<cmd>' command
  (error) ERR value is not an integer or out of range
  (error) OOM command not allowed when used_memory > 'maxmemory'
  ```
- 값 파싱: 공백 없는 값 또는 큰따옴표로 감싼 값 지원 (예: `"Alice"`)

---

## 5. 개발 환경
- Python 3.8 이상

## 6. 제약 사항
- **dict, set, collections 사용 금지** (내장 컬렉션으로 해시맵/캐시 대체 금지; 고정 길이 배열/인덱스 접근 수준은 허용)
- 각 자료구조(해시맵/이중 연결 리스트/힙)는 **독립된 모듈/파일로 분리**
- 핵심 클래스/함수에 주석 또는 docstring 작성
- 네트워크 통신 없음 (오직 CLI), 파일 저장 없음 (메모리 동작), 복잡 자료형(List/Set/Sorted Set) 없음, 동시성 처리 불필요

---

## 7. 실행 결과 예시 (참고용)

```
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
# maxmemory(30) 초과로 LRU(user:1) 제거

mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
mini-redis> KEYS
1. "user:2"
2. "user:3"
mini-redis> EXPIRE user:2 3
(integer) 1
mini-redis> TTL user:2
(integer) 2
# (3초 경과 후)
mini-redis> GET user:2
(nil)
mini-redis> TTL user:2
(integer) -2
```

에러 예시:
```
mini-redis> CONFIG SET maxmemory abc
(error) ERR value is not an integer or out of range
mini-redis> GET
(error) ERR wrong number of arguments for 'GET' command
mini-redis> HELLO
(error) ERR unknown command 'HELLO'
```

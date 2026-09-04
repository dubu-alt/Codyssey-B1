# Mini Redis

Redis의 핵심을 자료구조를 밑바닥부터 직접 구현해서 따라 만든 CLI 프로그램입니다.
(해시맵 - 체이닝 / 이중 연결 리스트 / 최소 힙 모두 직접 구현, dict/set/collections 미사용)

## 실행 방법

이 폴더(`B5-1`)에서:

```bash
python -m mini_redis.main
```

`mini-redis>` 프롬프트에 명령어를 입력합니다. 종료는 `exit` 또는 `quit`.

## 명령어 목록

| 명령어 | 예시 | 설명 |
|--------|------|------|
| SET | `SET user:1 "Alice"` | 키에 값 저장 (LRU 추적 갱신) |
| GET | `GET user:1` | 값 조회. 없거나 만료되면 `(nil)` |
| DEL | `DEL user:1` | 키 삭제 |
| EXISTS | `EXISTS user:1` | 존재 여부 `(integer) 1/0` |
| DBSIZE | `DBSIZE` | 전체 키 개수 |
| KEYS | `KEYS` | 전체 키 목록 |
| CONFIG SET maxmemory | `CONFIG SET maxmemory 30` | 메모리 한도 설정 (바이트, 0=무제한) |
| INFO memory | `INFO memory` | used_memory / maxmemory / evicted_keys 출력 |
| EXPIRE | `EXPIRE user:2 3` | 3초 후 만료 설정 |
| TTL | `TTL user:2` | 남은 초 (-2 없음 / -1 만료설정없음 / N 남은초) |

값은 공백 없이(`Alice`) 또는 큰따옴표로 감싸서(`"hello world"`) 입력할 수 있습니다.

## 동작 원리 요약

- **LRU**: 메모리가 `maxmemory`를 넘으면 가장 오래 안 쓴 키부터 자동 삭제 (`evicted_keys` 누적)
- **used_memory** = Σ(len(utf8키) + len(utf8값))
- **TTL**: 만료 예약은 최소 힙으로 관리. 만료된 키 조회 시 먼저 삭제 후 "없는 키" 처리
- 단일 엔트리가 한계보다 크면 저장하지 않고 OOM 에러

## 코드 구조

```
mini_redis/
├── main.py                시작점. REPL + 명령어 파싱
├── store.py               데이터/LRU/TTL 관리 두뇌
├── hashmap.py             해시맵 (체이닝, 로드팩터 0.75 초과 시 2배 확장)
├── doubly_linked_list.py  이중 연결 리스트 (LRU 순서 추적)
└── heap.py                최소 힙 (만료 예약 관리)
```

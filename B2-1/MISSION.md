# B2-1. 나만의 용돈 기입장 프로그램 만들기

> **분야**: AI/SW 기초 | **구분**: Python과 Git 심화 | **학습시간**: 60시간
> **난이도**: ★★☆☆☆ (2단계)

---

## 1. 이 미션이 뭔가요?

터미널(검은 창)에서 명령어를 입력해서 사용하는 **콘솔용 가계부 프로그램**을 Python으로 만드는 미션입니다.

- 돈을 쓰거나 벌면 **내역을 추가**하고 (`add`)
- 지금까지의 내역을 **목록으로 보고** (`list`)
- 원하는 조건으로 **검색**하며 (`search`)
- 한 달에 얼마를 벌고 얼마를 썼는지 **요약**하고 (`summary`)
- 이번 달 **예산을 정해두면** 초과했을 때 경고해주고 (`budget`)
- 카테고리(식비, 교통비 등)를 **관리**하는 (`category`)
- 잘못 저장한 내역을 **수정/삭제**하고 (`update` / `delete`)
- CSV 파일로 **내보내기/가져오기**까지 (`export` / `import`)

핵심 포인트: 단순히 기능만 만드는 게 아니라,
1. 프로그램을 껐다 켜도 데이터가 남아있게 **파일에 저장**하고
2. 코드를 기능별로 **여러 파일로 나눠서**(모듈화) 관리하기 쉽게 만드는 것입니다.

> '작은 서비스'란 기능이 많은 게 아니라, **예외 상황에서도 데이터가 안전한 것**을 말합니다.

---

## 2. 최종 결과물 (10가지 기능이 동작하는 앱 1개)

| # | 명령어 | 하는 일 | 입력 | 출력 |
|---|--------|---------|------|------|
| 1 | `add` | 거래 추가 | 대화형으로 날짜/타입/카테고리/금액/메모/태그 순서대입력 | 저장 성공 메시지 + 생성된 거래 id |
| 2 | `list` | 목록 조회 | `--limit N` 옵션 | 최신순 거래 리스트 (스트리밍 처리) |
| 3 | `search` | 거래 검색 | `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` | 조건에 맞는 거래 리스트 (최신순) |
| 4 | `summary` | 월별 요약 | `--month YYYY-MM`, `--top N` | 총수입/총지출/잔액 + 카테고리별 지출 TOP N |
| 5 | `budget` | 예산 설정/조회 | `budget set --month YYYY-MM --amount 금액` | 저장 성공 메시지 + summary에서 예산 사용률/초과 경고 |
| 6 | `category` | 카테고리 관리 | `category add/list/remove` | 카테고리 목록/추가/삭제 결과 |
| 7 | `update` | 거래 수정 | `-id` 기반 (옵션 방식 또는 대화형 중 **1개로 고정**, 문서에 명시) | 수정 성공/실패 메시지 |
| 8 | `delete` | 거래 삭제 | `delete --id <id>` | 삭제 성공/실패 메시지 |
| 9 | `import` / `export` | 가져오기/내보내기 | `import --from <csv>`, `export --out <csv>` + 조건 | 처리 건수 출력 + CSV 파일 생성 확인 |

### 필수 구성 (추가 조건)
- 데이터는 **3개 이상 파일로 영구 저장** (예: `transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`)
- README.md에 **실행 방법 / 저장 파일 위치·형식 / 주요 명령 예시 / import·export CSV 스키마** 포함

---

## 3. 과제 목표 (이걸 설명할 수 있게 되어야 해요)

1. 파일 기반 저장(JSONL/CSV)으로 데이터를 영구 저장하고, CRUD/검색/요약/입출력을 구현할 수 있다.
2. 콘솔 프로그램을 클래스/모듈로 구조화하고, 각 계층(모델/저장소/서비스/CLI)의 책임을 설명할 수 있다.
3. `yield` 기반 제너레이터로 대용량 파일도 스트리밍 처리하는 이유와 동작 방식을 설명할 수 있다.
4. 데코레이터로 공통 관심사(로그/예외/시간 측정)를 분리한 구조와 이유를 설명할 수 있다.
5. 타입 힌트를 통해 입출력 계약을 명확히 했을 때 얻는 이점을 실제 코드 예로 설명할 수 있다.

---

## 4. 기능 요구 사항 (상세)

### 4-1. 실행 및 입력 방식
- 실행 형태: `python -m budget_app <command> [options]`
- 모든 명령은 `--help` 옵션으로 사용법 출력 가능해야 함
- 기본 입력은 **대화형**(`input()`으로 하나씩 질문)
- 단, `search / list / summary / export / import / delete`는 옵션 인자 방식 허용(권장)
- 옵션 표기는 리눅스 표준인 `--`로 통일 (예: `--help`, `--limit`, `--from`, `--to`, `--month`)

### 4-2. 데이터 모델
- 거래(Transaction) 필드:
  - `id`(유일), `type`(income/expense), `date`(YYYY-MM-DD), `amount`(양수), `category`, `memo`(선택), `tags`(선택)
- 데이터 모델은 **dataclass** 또는 그에 준하는 구조로 정의
- **최소 2개 이상의 클래스** 사용
  - 예: `Transaction`, `TransactionRepository`, `BudgetStore`, `CategoryStore`, `BudgetService`

### 4-3. 입력 검증
- 날짜 형식 오류, 음수/0 금액, 허용되지 않는 type, 없는 category → 재입력 요구 또는 오류 메시지 출력

### 4-4. 저장 정책
- 저장 포맷: **JSONL 또는 CSV 중 1개 선택**
- 저장 파일 **3개 이상 분리**: `transactions.<fmt>`, `categories.<fmt>`, `budgets.<fmt>`
- 기본 저장 폴더: `./data` 권장, 옵션으로 변경 가능 (예: `--data-dir`)
- 초기 실행(파일이 없을 때): 자동 생성하거나 초기화 안내 메시지 출력
- 카테고리 파일이 비어있으면 아래 중 하나 선택:
  - **(안 A)** 기본 카테고리 자동 생성 (예: food, transport, rent, etc)
  - **(안 B)** category add 먼저 하도록 안내하고 add 막음

### 4-5. 각 명령 세부 요구사항
- **add**: 대화형 입력, 등록된 카테고리만 허용(없으면 안내 후 재입력/등록 유도), 저장 시 생성된 id 출력
- **list**: 최신순 출력, `--limit N` 지원(기본값 제공), **제너레이터 스트리밍 처리**(파일 전체를 한 번에 로드하지 않음)
- **update/delete**: `delete --id <id>` 지원, 없는 id는 "없는 데이터" 메시지 처리.
  update는 아래 중 하나로 문서에 고정:
  - (안 A) 옵션 기반: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`
  - (안 B) 대화형: 수정할 필드만 선택/재입력
  - update/delete 시 "전체 재작성 / 임시 파일 / 원자적 교체(권장)" 등 안정성 고려
- **search**: 조건 = 기간(`--from`,`--to`) / 카테고리(`--category`) / 타입(`--type`) / 메모 키워드(`--q`) / 태그(`--tag`). 결과 최신순 + 제너레이터 스트리밍 유지
- **summary**: `--month YYYY-MM` 필수. 출력 = 총수입/총지출/잔액 + 카테고리별 지출 TOP N(`--top`). 데이터 없는 달은 "데이터 없음" 출력
- **budget**: `budget set --month YYYY-MM --amount <금액>`으로 저장. summary에서 예산 사용률(%), 초과 시 경고 문구. 예산도 영구 저장
- **category**: `add/list/remove` 제공. 삭제 시 그 카테고리를 사용 중인 내역이 있으면 **삭제를 막거나 대체 카테고리 요구**
- **import/export**:
  - `import --from <csv>`: 거래 일괄 등록
  - `export --out <csv>`: 조건에 맞는 거래를 CSV로 저장 (단, `--month YYYY-MM` 또는 `--from/--to` 중 **하나 이상 조건 필수**)

### 4-6. import/export CSV 최소 스키마 (고정)

| column | required | 설명 |
|--------|----------|------|
| date   | Y | YYYY-MM-DD |
| type   | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo   | N | 문자열 |
| tags   | N | 쉼표(,) 구분 문자열 |

공통: UTF-8, 헤더 포함

### 4-7. 데코레이터 / 예외 처리 / 모듈화
- **데코레이터**: 공통 관심사(예외 처리/로그/시간 측정) 데코레이터 1개 이상 구현 + 실제 적용
- **예외 처리 및 종료 코드**: 오류는 스택트레이스 대신 "원인 + 해결 힌트" 출력. 정상 종료 exit code 0, 오류 종료 0이 아닌 값
- **모듈화**: 최소 3개 이상 모듈로 분리. (권장) CLI / 서비스 / 저장소(파일 I/O) / 모델(데이터 구조)로 책임 분리

---

## 5. 개발 환경
- Python 3.10 이상

## 6. 제약 사항
- **표준 라이브러리만 사용** (pip install 필요한 외부 라이브러리 금지)
- JSONL 또는 CSV 중 1개 포맷 사용, 저장 파일 3개 이상 분리
- CLI 옵션 표기는 `--` 통일
- 스택트레이스 출력 금지 (원인 + 해결 힌트 출력)
- 오류 종료 시 exit code는 0이 아니어야 함

---

## 7. 실행 결과 예시 (참고용, 문구/디자인은 달라도 됨)

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

```
$ python -m budget_app list --limit 3
TX-000012 | 2024-01-15 | expense | food | 15000 | 점심
TX-000011 | 2024-01-14 | income  | salary | 3000000 |
TX-000010 | 2024-01-12 | expense | transport | 20000 |
```

```
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500000원

$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

```
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```

오류 출력 예시:
```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
```

# 나만의 용돈 기입장 프로그램 (budget_app)

터미널에서 명령어로 사용하는 콘솔 가계부입니다. Python 표준 라이브러리만 사용합니다.

## 실행 방법

이 폴더(`B2-1`)에서 아래처럼 실행합니다.

```bash
python -m budget_app <명령어> [옵션]
```

| 명령어 | 하는 일 | 주요 옵션 |
|--------|---------|-----------|
| `add` | 거래 추가 | 없음 - 날짜/타입/카테고리/금액/메모/태그를 순서대로 대화형 입력 |
| `list` | 최신순 목록 조회 | `--limit N` (기본값 10) |
| `search` | 조건 검색 | `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` |
| `summary` | 월별 요약 | `--month YYYY-MM` (필수), `--top N` |
| `budget set` | 월 예산 설정 | `--month YYYY-MM --amount 금액` |
| `category add/list/remove` | 카테고리 관리 | `add/remove --name 이름` (없으면 대화형) |
| `update` | 거래 수정 | **옵션 방식 고정**: `--id` 필수 + 바꿀 항목만 `--date/--type/--category/--amount/--memo/--tags` |
| `delete` | 거래 삭제 | `delete --id TX-000001` |
| `export` | CSV 내보내기 | `--out 파일.csv` + `--month` 또는 `--from/--to` 중 하나 이상 필수 |
| `import` | CSV 가져오기 | `import --from 파일.csv` |

모든 명령은 `--help`로 사용법을 볼 수 있습니다. (`python -m budget_app add --help`)
데이터 저장 폴더를 바꾸려면 전역 옵션 `--data-dir 경로`를 사용하세요.

### 실행 예시

```bash
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리(food, transport, rent, etc): food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000001

$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 35000원
잔액: 2965000원
예산: 100000원 (사용률 35.0%)

지출 TOP 2
1) transport 20000원
2) food 15000원
```

## 저장 파일 위치와 형식

기본 저장 폴더는 `./data`이며, **JSONL** 형식(한 줄에 데이터 한 건)으로 저장됩니다.

| 파일 | 내용 |
|------|------|
| `data/transactions.jsonl` | 거래 내역: id / type / date / amount / category / memo / tags |
| `data/categories.jsonl`   | 카테고리 목록 (첫 실행 시 food, transport, rent, etc 자동 생성) |
| `data/budgets.jsonl`      | 월 예산: month / amount |

프로그램을 껐다 켜도 데이터는 유지됩니다.

## import/export CSV 스키마 (고정)

UTF-8 인코딩, 첫 줄에 헤더 포함:

| column | required | 설명 |
|--------|----------|------|
| date     | Y | YYYY-MM-DD |
| type     | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount   | Y | 양수 정수 |
| memo     | N | 문자열 |
| tags     | N | 쉼표(,) 구분 문자열 |

```bash
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```

## 오류 처리 규칙

- 오류는 `[오류] 원인` + `[힌트] 해결 방법` 형태로 출력됩니다 (스택트레이스 없음)
- 잘못된 입력(날짜 형식, 음수 금액 등)은 대화형 모드에서 재입력을 요구합니다
- 정상 종료 exit code = 0, 오류 종료 exit code = 1

## 코드 구조

```
budget_app/
├── __main__.py    시작점. 명령어 해석(argparse)
├── cli.py         대화형 입력 도우미
├── services.py    실제 로직 (검증/저장/요약 등)
├── storage.py     파일 읽고/쓰기 (JSONL, 원자적 교체)
├── models.py      Transaction 데이터 상자 (dataclass)
└── decorators.py  공통 기능 포장지 (실행시간 측정, 오류 처리)
```

# B2-1. 체크리스트

> 하나씩 확인하면서 `[ ]`를 `[x]`로 바꿔가세요.
> 모든 항목이 체크되면 평가 요청을 할 수 있습니다.

---

## 0. 개발 환경 / 제약 조건

- [ ] Python 3.10 이상으로 동작한다
- [ ] 외부 라이브러리 없이 **표준 라이브러리만** 사용했다 (pip install 불필요)
- [ ] 저장 포맷은 JSONL 또는 CSV 중 1개로 통일했다
- [ ] CLI 옵션 표기를 `--`(리눅스 표준)로 통일했다

## 1. 프로젝트 구조

- [ ] `python -m budget_app <command> [options]` 형태로 실행된다
- [ ] 모듈을 **3개 이상**으로 분리했다 (권장: cli / services / storage / models)
- [ ] 클래스를 **2개 이상** 사용했다 (예: Transaction, TransactionRepository, BudgetStore...)
- [ ] 거래 데이터 모델을 dataclass(또는 준하는 구조)로 정의했다
- [ ] 공통 기능 데코레이터를 **1개 이상** 구현하고 실제 적용했다

## 2. 데이터 저장

- [ ] 데이터가 **3개 이상 파일**로 영구 저장된다 (transactions / categories / budgets)
- [ ] 기본 저장 폴더는 `./data`이고, 옵션(예: `--data-dir`)으로 변경 가능하다
- [ ] 처음 실행 시(파일이 없을 때) 자동 생성 또는 초기화 안내 메시지가 나온다
- [ ] 카테고리 파일이 비어있을 때의 동작을 정하고 구현했다
  - [ ] (안 A) 기본 카테고리 자동 생성, 또는
  - [ ] (안 B) category add 먼저 안내 + add 차단
- [ ] update/delete 시 원자적 교체 등 파일 안정성을 고려했다

## 3. 명령어 10종 동작

- [ ] `add`: 대화형 입력으로 날짜/타입/카테고리/금액/메모/태그를 받아 저장, 생성된 id 출력
- [ ] `add`: 등록되지 않은 카테고리는 안내 후 재입력/등록 유도
- [ ] `list`: 최신순 출력 + `--limit N` 지원(기본값 있음)
- [ ] `list`: 제너레이터 스트리밍 처리 (파일 전체를 한 번에 로드하지 않음)
- [ ] `search`: `--from`, `--to`, `--category`, `--type`, `--q`, `--tag` 조건 검색, 최신순 출력
- [ ] `search`: 제너레이터 스트리밍 유지
- [ ] `summary --month YYYY-MM`: 총수입/총지출/잔액 + 카테고리별 지출 TOP N(`--top`)
- [ ] `summary`: 데이터 없는 달은 "데이터 없음" 출력
- [ ] `budget set --month YYYY-MM --amount 금액`: 예산 영구 저장
- [ ] `summary`에서 예산 사용률(%) 표시 + 초과 시 경고 문구
- [ ] `category add/list/remove` 동작
- [ ] `category remove`: 사용 중인 카테고리는 삭제 막거나 대체 카테고리 요구
- [ ] `update`: 옵션 방식 또는 대화형 중 **1개로 고정**, README에 방식 명시, 성공/실패 메시지
- [ ] `delete --id <id>`: 삭제 성공/실패 메시지
- [ ] 없는 id에 대한 update/delete: "없는 데이터"로 처리
- [ ] `import --from <csv>`: CSV 일괄 등록, 처리 건수 출력
- [ ] `export --out <csv>`: `--month` 또는 `--from/--to` 조건 필수, 처리 건수 + 파일 생성 확인

## 4. import/export CSV 스키마 (고정)

- [ ] 컬럼 순서: `date, type, category, amount, memo, tags`
- [ ] date = YYYY-MM-DD, type = income/expense, amount = 양수 정수
- [ ] tags = 쉼표(,) 구분
- [ ] UTF-8 인코딩 + 헤더 포함

## 5. 검증과 오류 처리

- [ ] 날짜 형식 오류 → 재입력 요구 또는 오류 메시지 (+힌트)
- [ ] 음수/0 금액 → 재입력 요구 또는 오류 메시지
- [ ] 허용되지 않는 type(income/expense 외) → 처리됨
- [ ] 존재하지 않는 category → 처리됨
- [ ] 오류 발생 시 스택트레이스 대신 **원인 + 해결 힌트** 출력
- [ ] 정상 종료 exit code = 0, 오류 종료 exit code ≠ 0

## 6. README.md

- [ ] 실행 방법이 있다
- [ ] 저장 파일 위치와 형식 설명이 있다
- [ ] 주요 명령 예시가 있다
- [ ] import/export CSV 스키마가 있다
- [ ] update 방식(옵션형/대화형 중 무엇인지)이 명시되어 있다

## 7. 코드 품질 (본인 규칙)

- [ ] 모든 코드에 주석이 달려있다 (비전공자도 읽을 수 있게)
- [ ] 코드가 심플하고 깔끔하다 (불필요한 복잡함 없음)

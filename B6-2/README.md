# ai-gitgen — AI 기반 Git 커밋/PR 자동 생성기

`git status`, `git diff` 결과를 AI API(기본: **Google AI Studio Gemini**, OpenAI 호환 Chat Completions)에 전달해
**커밋 메시지**와 **PR 제목/본문 초안**을 자동 생성하는 Python CLI 도구입니다.

## 프로젝트 구조

```
ai-gitgen/
├── main.py           # CLI 진입점 (commit / pr 명령)
├── git_collector.py  # git status / git diff 수집
├── ai_client.py      # AI API REST 호출 클라이언트
├── prompts.py        # 커밋/PR 프롬프트 템플릿
├── validators.py     # 출력 형식 검증 및 후처리
├── safe_mode.py      # 민감정보 마스킹 + diff 전송량 제한
└── README.md
```

## 요구 사항

- Python 3.10 이상
- 외부 라이브러리 없음 (표준 라이브러리만 사용)
- Git이 설치되어 있고, 실행 위치가 Git 리포지토리 내부여야 함

## 설치 및 실행 방법

```bash
# 1. 프로젝트 디렉토리로 이동 (또는 원하는 Git 리포지토리 루트에서 실행)
cd ~/Downloads/ai-gitgen

# 2. API Key 설정 (Google AI Studio에서 발급)
export GOOGLE_API_KEY="AIza..."

# 3. 커밋 메시지 생성
python main.py commit

# 4. PR 초안 생성
python main.py pr
```

## 환경변수(API Key) 설정 방법

API Key는 **환경변수로만** 관리하며 코드에 하드코딩하지 않습니다.

[Google AI Studio](https://aistudio.google.com/)에서 API Key를 발급한 뒤 아래처럼 설정하세요.

```bash
# 방법 1 (권장): 공통 환경변수 사용
export AI_API_KEY="AIza..."

# 방법 2: Google 전용 환경변수 이름 사용 (자동 인식)
export GOOGLE_API_KEY="AIza..."
# 또는
export GEMINI_API_KEY="AIza..."

# 선택: 다른 OpenAI 호환 엔드포인트 사용 시 (기본값은 Google AI Studio)
export AI_API_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"
```

우선순위는 `AI_API_KEY` > `GOOGLE_API_KEY` > `GEMINI_API_KEY` 순입니다.

### `.env` 파일로 관리하기 (매번 export 안 해도 됨)

매번 `export`로 셸에 직접 입력하기 번거로우면, 프로젝트 루트에 `.env` 파일을 만들어두면 `python main.py` 실행 시 자동으로 읽어들입니다 (외부 라이브러리인 `python-dotenv` 없이 프로젝트 자체 코드로 구현됨).

```bash
# .env (프로젝트 루트에 생성, .gitignore에 이미 등록되어 있어 커밋되지 않음)
AI_API_KEY=AIza...
AI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

```bash
# source 없이 바로 실행해도 .env 값이 자동 적용된다
python main.py commit
```

- 이미 셸에서 `export`로 설정해둔 환경변수가 있으면 그 값이 항상 우선되고, `.env` 값은 비어있는 경우에만 채워집니다.
- `.env` 파일은 절대 커밋하지 마세요 (`.gitignore`에 이미 등록됨).

API Key가 없으면 아래처럼 안내 후 종료합니다.

```
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
  예) export AI_API_KEY="YOUR_KEY"
  (Google AI Studio 키: export GOOGLE_API_KEY="YOUR_KEY")
```

### (대안) Codyssey Public API Console 키 사용하기

Google/OpenAI/Anthropic에서 직접 키를 발급받는 대신, **Codyssey 자체 Public API Console**(`usr.codyssey.kr/public-api-console`)에서 발급한 키로도 그대로 사용할 수 있습니다. 이 콘솔은 OpenAI 호환 Chat Completions 엔드포인트를 제공하므로 `ai-gitgen` 코드 수정 없이 환경변수만 바꾸면 됩니다.

1. Codyssey에 로그인한 뒤 `public-api-console` 페이지 → **API 키** 탭 → **키 발급** 클릭
2. **API 호환 방식**에서 **OpenAI**를 선택하고 발급 (발급된 키 값은 한 번만 표시되므로 즉시 복사해 안전한 곳에 보관)
3. 아래처럼 환경변수를 설정

```bash
export AI_API_KEY="sk-cody-live-..."                       # 발급받은 키
export AI_API_BASE_URL="https://copa.codyssey.kr/v1"       # Codyssey Public API Base URL

# 사용 가능한 모델 예: gemini-3-flash, gemini-3.1-pro, claude-haiku-4, claude-sonnet-4, gpt-5-mini 등
python main.py commit --model gemini-3-flash
python main.py pr --model gemini-3-flash --safe-mode
```

- 콘솔 상단의 "잔여 토큰"으로 남은 무료 할당량을 확인할 수 있고, 모델별로 토큰 차감 배수가 다르므로(예: `gemini-3-flash` 0.5배, `claude-sonnet-4` 1배) 비용을 아끼려면 저가중치 모델을 우선 사용하세요.
- 실제 사용 확인: `gpt-5-mini`는 테스트 시점에 프로바이더 오류(HTTP 502)가 발생했고 `gemini-3-flash`는 정상 동작했습니다. 특정 모델에서 502/503 오류가 나면 다른 모델로 재시도하세요.
- 이 키도 일반 API Key와 동일하게 **환경변수로만** 관리하고 코드/`.env.example`에 절대 하드코딩하지 마세요.

## CLI 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--model` | `gemini-3-flash` | 사용할 AI 모델명 |
| `--temperature` | `0.3` | 생성 다양성(0.0~2.0). 낮을수록 일관된 결과 |
| `--max-tokens` | `800` | 최대 생성 토큰 수 |
| `--safe-mode` | off | 민감정보 마스킹 + diff 전송량 제한 활성화 |
| `--max-files` | `10` | safe-mode에서 전송할 최대 파일 수 |
| `--max-lines` | `200` | safe-mode에서 전송할 최대 diff 줄 수 |

### 사용 가능한 모델 목록 확인하기 (`models` 명령)

`--model`에 무엇을 넣을 수 있는지 매번 문서를 뒤지기 귀찮으면, 현재 API Key가 지원하는 모델 목록을 바로 조회할 수 있습니다. Git 리포지토리 밖에서도 실행 가능하며, 하드코딩된 목록이 아니라 API 서버(`GET /models`)에 실시간으로 물어본 결과라 항상 최신 상태를 보여줍니다.

```bash
python main.py models
```

```
--- 사용 가능한 모델 (--model 옵션에 그대로 사용) ---
  gemini-3-flash           (google)
  gemini-3.1-flash-lite    (google)
  gemini-3.1-pro           (google)
  claude-haiku-4           (anthropic)
  claude-sonnet-4          (anthropic)
  gpt-5-mini               (openai)
  claude-opus-4-7          (anthropic)
  claude-opus-4-8          (anthropic)
  gpt-5.5                  (openai)
  gpt-5.4                  (openai)
  gpt-5.4-mini             (openai)
----------------------------------------
```

> Codyssey Public API Console처럼 게이트웨이형 엔드포인트를 쓸 때 특히 유용합니다. 콘솔 문서 페이지를 매번 확인하지 않아도 되고, 목록에 없는 모델명을 넣어서 `404 Model not found` 오류를 만나는 것도 미리 방지할 수 있습니다.

### 파라미터가 결과 품질에 미치는 영향

- **temperature**: 낮으면(0.x) 형식을 잘 지키는 일관된 문구, 높으면 창의적이지만 형식이 흐트러질 수 있음. 커밋/PR 생성에는 낮은 값 권장.
- **max_tokens**: 너무 작으면 본문이 중간에 잘림. PR 본문은 커밋 메시지보다 길어지므로 500~1000 권장.
- **model**: 성능이 좋은 모델일수록 맥락 파악과 형식 준수가 우수하지만 비용 증가.

## 사용 예시

### 커밋 메시지 생성

```bash
python main.py commit --temperature 0.2
```

출력 예시:

```
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 128줄
[INFO] 현재 브랜치: feature/commit-pr-generator
[INFO] AI API 요청 중...
[DONE] 커밋 메시지 생성 완료

--- Commit Message ---
feat: Git 변경 사항 기반 커밋 메시지 자동 생성 기능 추가

- git_collector.py: git diff 결과를 수집해 AI 입력 컨텍스트로 전달하도록 구현
- prompts.py: 커밋 메시지 템플릿(feat/fix 등) 생성 규칙 적용
- main.py: API Key 미설정 시 안내 메시지 및 에러 처리 개선
----------------------

[INFO] AI API 호출 횟수: 1회
[INFO] 생성 결과는 초안입니다. 검토 후 적용하세요.
```

### PR 초안 생성

```bash
python main.py pr --safe-mode
```

출력 예시:

```
[DONE] PR 초안 생성 완료

--- PR Title ---
feat: 커밋/PR 자동 생성 기능 추가

--- PR Body ---
## Why
- 팀 협업 시 커밋 메시지와 PR 설명 작성에 시간이 소요되어 자동 생성 도구가 필요했습니다.
- Git 변경 사항을 기반으로 일관된 형식의 요약 텍스트를 생성해 리뷰 효율을 높이고자 했습니다.

## What
- git_collector.py: git status, git diff 결과를 수집해 AI 입력 컨텍스트로 전달하는 로직 추가
- main.py: 커밋 메시지 자동 생성(commit) 및 PR 초안 생성(pr) CLI 명령 구현
- safe_mode.py: 민감정보 마스킹 및 diff 전송량 제한 기능 추가

## How to Test
- 환경변수 설정: export AI_API_KEY="YOUR_KEY"
- 커밋 메시지 생성: python main.py commit
- PR 초안 생성: python main.py pr
- 출력된 PR 본문이 Why/What/How to Test 구조와 길이 규칙을 만족하는지 확인
-----------------
```

### 기타 상황별 출력

변경 사항이 없는 경우:

```
[INFO] 변경 사항이 없습니다. 생성하지 않고 종료합니다.
```

네트워크 오류:

```
[ERROR] AI API 호출 실패: 네트워크 오류: API 서버에 연결할 수 없습니다.
```

## 출력 형식 검증 규칙

생성 결과는 아래 규칙으로 검증하고, 위반 시 후처리(잘라내기/섹션 정규화)합니다.

- 커밋 제목: 50자 이내 권장(최대 72자, 초과 시 자름)
- PR 제목: 최대 80자(초과 시 자름)
- PR 본문: `## Why` / `## What` / `## How to Test` 섹션 헤더 필수 + 각 섹션 최소 1개 불릿
- 검증 경고는 `[INFO] 검증 경고: ...` 로 표시되므로 필요하면 옵션을 조정해 재실행하세요.

## 주의사항 (운영 관점)

### 민감정보 보호 (safe-mode)

`git diff`에는 실수로 넣은 API Key, 비밀번호, 개인정보(이메일 등)가 포함될 수 있습니다.
`--safe-mode` 옵션을 사용하면:

1. **마스킹**: API Key(`sk-...`, `ghp_...`, `AKIA...`, `xox...`, `AIza...`), JWT, Bearer 토큰, 이메일 주소, `.env` 스타일의 `KEY=VALUE` 비밀값을 정규표현식으로 찾아 `[MASKED:...]` 로 치환한 뒤 전송
2. **전송량 제한**: 최대 10개 파일 / 최대 200줄만 전송 (`--max-files`, `--max-lines` 으로 조정)

민감정보는 애초에 커밋 전에 제거하는 것이 원칙이며, safe-mode는 실수 방지용 안전장치입니다.

### 비용 / 요청 횟수 제한

- `commit` / `pr` 명령은 각각 **AI API 1회 호출**로 동작하며, 실행 마지막에 호출 횟수를 출력합니다.
- 불필요한 재실행을 줄이려면 `--max-lines` 로 전송량을 줄이고, 무료/저가 티어인 `gemini-3-flash` 같은 Flash 계열 모델을 사용하세요.

### 생성 결과 활용

- 생성된 커밋/PR 문구는 **초안**이며 최종 정답이 아닙니다. 반드시 사람이 검토 후 적용하세요.
- 원격 저장소 자동 반영(`git push`, GitHub PR API 생성)은 의도적으로 구현하지 않았습니다.

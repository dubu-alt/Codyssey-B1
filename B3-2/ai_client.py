"""AI API 클라이언트 모듈.

Google AI Studio(Gemini)의 OpenAI 호환 Chat Completions 엔드포인트를 기본으로 호출한다.
API Key는 환경변수(AI_API_KEY 또는 GOOGLE_API_KEY/GEMINI_API_KEY)로만 관리하며
코드에 하드코딩하지 않는다.
"""

from __future__ import annotations

# JSON 직렬화(요청 본문) 및 역직렬화(응답 파싱)에 사용
import json
# 환경변수에서 API Key를 읽기 위해 사용
import os
# HTTP 오류(HTTPError)와 네트워크 오류(URLError) 구분 처리에 사용
import urllib.error
# 표준 라이브러리만으로 REST API를 호출하기 위해 사용 (외부 의존성 없음)
import urllib.request

# --- 기본 설정 상수 ---

# API Key를 읽을 기본 환경변수 이름
API_KEY_ENV = "AI_API_KEY"
# 폴백 환경변수: Google AI Studio에서 발급한 키를 그대로 쓸 수 있도록 허용
# 조회 우선순위: AI_API_KEY > GOOGLE_API_KEY > GEMINI_API_KEY
API_KEY_ENV_FALLBACKS = ("GOOGLE_API_KEY", "GEMINI_API_KEY")
# Google AI Studio가 제공하는 OpenAI 호환(Chat Completions) 엔드포인트
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
# 기본 모델: 비용이 저렴하고 속도가 빠른 Gemini Flash 계열
DEFAULT_MODEL = "gemini-3-flash"


class AIAPIError(Exception):
    """AI API 호출 실패 시 발생하는 예외.

    네트워크 오류, 인증 실패(401), 요청 한도 초과(429),
    응답 형식 불일치 등 모든 API 관련 실패를 이 예외 하나로 통일해 전달하며,
    메시지에 오류 원인을 포함한다.
    """


def get_api_key() -> str:
    """환경변수에서 API Key를 읽는다. 없으면 AIAPIError 발생.

    우선순위: AI_API_KEY > GOOGLE_API_KEY > GEMINI_API_KEY
    """
    for env_name in (API_KEY_ENV, *API_KEY_ENV_FALLBACKS):
        key = os.environ.get(env_name, "").strip()
        if key:
            return key
    raise AIAPIError(
        f"{API_KEY_ENV} 환경변수가 설정되지 않았습니다.\n"
        f'  예) export {API_KEY_ENV}="YOUR_KEY"\n'
        f'  (Google AI Studio 키: export GOOGLE_API_KEY="YOUR_KEY")'
    )


class AIClient:
    """OpenAI 호환 Chat Completions API 클라이언트.

    Google AI Studio(Gemini)의 OpenAI 호환 엔드포인트를 기본으로 사용하며,
    base_url만 바꾸면 OpenAI 등 다른 호환 API에도 그대로 사용할 수 있다.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        max_tokens: int = 800,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        # 생성 시점에 API Key를 확인한다. 미설정이면 즉시 AIAPIError 발생.
        self.api_key = get_api_key()
        # 사용할 모델명 (CLI --model 옵션으로 변경 가능)
        self.model = model
        # 생성 다양성(0.0~2.0). 낮을수록 형식을 잘 지키는 일관된 결과가 나온다.
        self.temperature = temperature
        # 응답 최대 토큰 수. 너무 작으면 본문이 중간에 잘린다.
        self.max_tokens = max_tokens
        # API 베이스 URL: 인자 > 환경변수(AI_API_BASE_URL) > 기본값 순으로 결정
        self.base_url = (base_url or os.environ.get("AI_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        # 응답 대기 최대 시간(초)
        self.timeout = timeout
        # 실제 호출 횟수 누적 (비용 관리를 위해 실행 마지막에 로그로 출력)
        self.call_count = 0

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Chat Completions API를 호출하고 생성된 텍스트를 반환한다.

        요청 구성 → 전송 → 응답 파싱 → 예외 대응의 전체 흐름을 담당.
        """
        # --- 1. 요청 본문(payload) 구성 ---
        # system 프롬프트: 커밋/PR 양식 규칙 (역할 부여)
        # user 프롬프트: git status/diff로 수집한 변경 사항 컨텍스트
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        # --- 2. HTTP 요청 객체 생성 ---
        # JSON 본문 + Bearer 인증 헤더를 담아 POST 요청을 준비한다.
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        # 호출 횟수 기록 (미션 제약: 1회 실행당 1~2회 이내)
        self.call_count += 1

        # --- 3. 요청 전송 및 예외 대응 ---
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 서버가 4xx/5xx 상태 코드를 반환한 경우.
            # 응답 본문에 오류 상세가 담겨 있으므로 최대 500자까지 읽어 포함한다.
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                pass
            if exc.code == 401:
                # 인증 실패: 키가 잘못되었거나 만료됨
                raise AIAPIError(f"인증 실패(401): API Key가 유효하지 않습니다.\n{detail}") from exc
            if exc.code == 429:
                # 요청 한도 초과: 무료 티어 할당량 소진 등
                raise AIAPIError(f"요청 한도 초과(429): 잠시 후 다시 시도하세요.\n{detail}") from exc
            raise AIAPIError(f"API 요청 실패(HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            # DNS 실패, 연결 거부 등 네트워크 계층 오류
            raise AIAPIError(f"네트워크 오류: API 서버에 연결할 수 없습니다. ({exc.reason})") from exc
        except TimeoutError as exc:
            # 지정한 timeout 내에 응답이 오지 않은 경우
            raise AIAPIError("요청 시간이 초과되었습니다(timeout).") from exc

        # --- 4. 응답 파싱 ---
        # 정상 응답 형식: {"choices": [{"message": {"content": "..."}}]}
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            # 예상과 다른 구조가 오면 원본 일부를 보여주며 실패 원인을 알린다.
            raise AIAPIError(f"응답 형식이 예상과 다릅니다: {json.dumps(body)[:300]}") from exc

        if not content or not content.strip():
            raise AIAPIError("API가 빈 응답을 반환했습니다.")
        # 앞뒤 공백/개행을 제거한 생성 텍스트 반환
        return content.strip()

    def list_models(self) -> list[dict]:
        """OpenAI 호환 GET /models 엔드포인트를 호출해 사용 가능한 모델 목록을 가져온다.

        `--model`에 어떤 값을 넣을 수 있는지 매번 문서를 안 찾아봐도 되도록,
        게이트웨이가 실제로 응답하는 모델 목록을 그대로 조회한다(하드코딩 목록이 아님).

        Returns:
            [{"id": "gemini-3-flash", "owned_by": "google"}, ...] 형태의 리스트.
        """
        request = urllib.request.Request(
            f"{self.base_url}/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:  # noqa: BLE001
                pass
            if exc.code == 401:
                raise AIAPIError(f"인증 실패(401): API Key가 유효하지 않습니다.\n{detail}") from exc
            raise AIAPIError(f"모델 목록 조회 실패(HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise AIAPIError(f"네트워크 오류: API 서버에 연결할 수 없습니다. ({exc.reason})") from exc

        try:
            data = body["data"]
        except (KeyError, TypeError) as exc:
            raise AIAPIError(f"모델 목록 응답 형식이 예상과 다릅니다: {json.dumps(body)[:300]}") from exc

        return [
            {"id": item.get("id", "?"), "owned_by": item.get("owned_by", "-")}
            for item in data
        ]

"""안전 모드(safe-mode) 모듈.

git diff에 포함될 수 있는 민감정보(API Key, 개인정보 등)를
프롬프트에 포함하지 않도록 마스킹하고, 전송량을 제한한다.

[safe-mode 정책]
- (A) 정규표현식 기반 마스킹:
    - API Key 형태: sk-..., ghp_..., AKIA... 등
    - Bearer 토큰 / Authorization 헤더 값
    - AWS 자격 증명 키
    - 이메일 주소
    - .env 스타일의 KEY=VALUE 비밀값 줄 전체
- (B) diff 전송 제한: 최대 파일 수 / 최대 줄 수 제한 (기본: 10개 파일, 200줄)
"""

from __future__ import annotations

# 민감정보 패턴 매칭 및 diff 파일 단위 분리에 정규표현식 사용
import re

# --- 기본 전송 제한 기준 (미션 권장: 최대 10개 파일, 200줄) ---
DEFAULT_MAX_FILES = 10
DEFAULT_MAX_LINES = 200

# --- 민감정보 패턴 목록 (정규표현식 기반 마스킹 규칙) ---
# (마스킹 라벨, 패턴) 쌍. 라벨은 [MASKED:<라벨>] 형태로 텍스트에 남는다.
MASK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # OpenAI(sk-)/Anthropic(rk-) 계열 API Key
    ("OpenAI/Anthropic 계열 API Key", re.compile(r"\b(sk|rk)-[A-Za-z0-9_-]{8,}\b")),
    # GitHub 개인 액세스 토큰 (ghp_/gho_/ghu_/ghs_/ghr_ 접두사)
    ("GitHub 토큰", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b")),
    # AWS Access Key ID (AKIA로 시작하는 20자)
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{12,}\b")),
    # Slack 봇/사용자 토큰 (xoxb-, xoxa- 등)
    ("Slack 토큰", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    # Google API Key (AIza로 시작, Google AI Studio 키 포함)
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")),
    # Authorization 헤더 값 전체 (그룹 1 = "authorization: " prefix는 보존)
    (
        "Authorization/Bearer 헤더",
        re.compile(
            r"(?i)\b(authorization\s*[:=]\s*)(bearer\s+)?\S+",
        ),
    ),
    # JWT (header.payload.signature 3부분이 모두 base64url)
    ("JWT 토큰", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    # 이메일 주소 (개인정보)
    ("이메일 주소", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]

# .env 스타일 비밀값 라인.
# KEY=VALUE 에서 변수명에 KEY/SECRET/TOKEN/PASSWORD가 들어가면
# VALUE 부분(그룹 2)만 마스킹하고 "KEY=" 부분(그룹 1)은 보존한다.
ENV_SECRET_LINE = re.compile(
    r"(?i)^(\s*(?:export\s+)?[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD)[A-Z0-9_]*\s*=\s*)(.+)$"
)


def mask_sensitive_text(text: str) -> tuple[str, list[str]]:
    """텍스트에서 민감정보를 찾아 마스킹한다.

    MASK_PATTERNS의 각 패턴으로 매칭되는 부분을 [MASKED:<라벨>] 로 치환하고,
    .env 스타일 비밀값 줄도 함께 처리한다.

    Returns:
        (마스킹된 텍스트, 마스킹된 항목 설명 리스트)
        예: ["API Key 1건", "이메일 주소 2건"]
    """
    found: list[str] = []

    # --- 1. 패턴 기반 마스킹 ---
    for label, pattern in MASK_PATTERNS:
        matches = pattern.findall(text)
        if matches:

            def _sub(m: re.Match[str]) -> str:
                # Authorization 헤더는 prefix("authorization: ")를 보존해
                # 어떤 헤더였는지 맥락을 유지하고 값만 마스킹한다.
                prefix = m.group(1) if m.lastindex and m.lastindex >= 1 else ""
                return f"{prefix}[MASKED:{label}]"

            text = pattern.sub(_sub, text)
            found.append(f"{label} {len(matches)}건")

    # --- 2. .env 스타일 비밀값 라인 마스킹 ---
    def _mask_env_line(m: re.Match[str]) -> str:
        # 그룹 1("SECRET_KEY=")은 유지하고 값만 치환
        return f"{m.group(1)}[MASKED:비밀 설정값]"

    new_text, n = ENV_SECRET_LINE.subn(_mask_env_line, text)
    if n:
        text = new_text
        found.append(f".env 스타일 비밀 설정값 {n}건")

    return text, found


def limit_diff(diff: str, max_files: int = DEFAULT_MAX_FILES, max_lines: int = DEFAULT_MAX_LINES) -> tuple[str, str]:
    """diff를 파일 수/줄 수 기준으로 잘라낸다.

    미션 safe-mode 옵션 (B) 'diff 일부만 전송' 정책을 구현한다.
    파일 단위로 먼저 잘라내고, 그 다음 전체 줄 수를 제한한다.

    Args:
        diff: 원본 diff 텍스트
        max_files: 전송할 최대 파일 수
        max_lines: 전송할 최대 줄 수

    Returns:
        (제한된 diff, 제한 안내 메시지 — 적용 안 됐으면 빈 문자열)
    """
    notes: list[str] = []

    # --- 1. 파일 단위 분리 ---
    # 각 파일의 diff는 "diff --git " 으로 시작하므로,
    # lookahead(?=...) split으로 헤더를 보존하면서 청크로 나눈다.
    chunks = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    chunks = [c for c in chunks if c.strip()]

    # --- 2. 파일 수 제한 ---
    if len(chunks) > max_files:
        notes.append(f"파일 수 제한 적용: {len(chunks)}개 → {max_files}개")
        chunks = chunks[:max_files]
    limited = "".join(chunks)

    # --- 3. 줄 수 제한 ---
    lines = limited.splitlines()
    if len(lines) > max_lines:
        notes.append(f"줄 수 제한 적용: {len(lines)}줄 → {max_lines}줄")
        limited = "\n".join(lines[:max_lines]) + "\n... (이하 생략)"

    return limited, " / ".join(notes)


def apply_safe_mode(
    diff: str,
    max_files: int = DEFAULT_MAX_FILES,
    max_lines: int = DEFAULT_MAX_LINES,
) -> tuple[str, list[str]]:
    """safe-mode를 적용해 마스킹 + 전송 제한을 순서대로 수행한다.

    처리 순서가 중요하다: 반드시 '마스킹 먼저, 잘라내기 나중'이어야
    잘려나간 부분에 민감정보가 남아 있어도 외부로 전송되지 않는다.

    Returns:
        (처리된 diff, 사용자에게 표시할 적용 내역 메시지 리스트)
    """
    masked, found = mask_sensitive_text(diff)
    limited, note = limit_diff(masked, max_files, max_lines)
    messages = [f"마스킹: {f}" for f in found]
    if note:
        messages.append(note)
    return limited, messages

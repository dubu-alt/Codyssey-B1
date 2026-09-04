"""생성 결과 검증 및 후처리 모듈.

길이/형식 규칙을 검증하고, 위반 시 재생성 또는 후처리로 다듬는다.
"""

from __future__ import annotations

# 섹션 헤더 정규화 및 TITLE 라인 추출에 정규표현식 사용
import re
# 검증 결과를 담는 불변 데이터 클래스
from dataclasses import dataclass

# --- 형식 규칙 상수 (미션 요구사항의 길이/형식 규칙) ---

# 커밋 제목 권장 길이 (Git 커뮤니티 관례)
COMMIT_TITLE_RECOMMENDED = 50
# 커밋 제목 최대 허용 길이 (초과 시 후처리로 잘라냄)
COMMIT_TITLE_MAX = 72
# PR 제목 최대 허용 길이 (초과 시 후처리로 잘라냄)
PR_TITLE_MAX = 80
# PR 본문에 반드시 있어야 하는 섹션 헤더 (순서도 중요)
PR_SECTIONS = ("## Why", "## What", "## How to Test")


@dataclass
class ValidationResult:
    """검증 결과를 담는 데이터 클래스.

    Attributes:
        ok: 형식 규칙 통과 여부
        warnings: 위반/수정 내역 목록 (터미널에 [INFO] 검증 경고로 출력됨)
        fixed_text: 후처리(잘라내기/정규화)까지 마친 최종 텍스트
    """

    ok: bool
    warnings: list[str]
    fixed_text: str


def _strip_code_fence(text: str) -> str:
    """AI가 코드블록으로 감싸서 출력한 경우 제거한다."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # 첫 줄(```lang)과 마지막 줄(```) 제거
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def validate_commit(text: str) -> ValidationResult:
    """커밋 메시지 규칙 검증 및 후처리.

    검증 규칙:
    - 제목 1줄 필수, 72자 초과 시 잘라냄 (50자 초과는 권장 경고만)
    - 본문이 있는데 불릿이 없으면 경고
    """
    warnings: list[str] = []
    # AI가 ``` 코드블록으로 감싸서 출력하는 경우를 대비해 먼저 제거
    text = _strip_code_fence(text)
    lines = [ln.rstrip() for ln in text.splitlines()]
    # 첫 줄 = 커밋 제목
    title = lines[0].strip() if lines else ""

    if not title:
        # 제목조차 없으면 실패 처리
        return ValidationResult(False, ["빈 커밋 메시지"], text)

    # --- 제목 길이 규칙 적용 ---
    if len(title) > COMMIT_TITLE_MAX:
        # 최대치(72자) 초과: 강제로 잘라내고 경고 기록
        title = title[:COMMIT_TITLE_MAX].rstrip()
        warnings.append(f"커밋 제목이 {COMMIT_TITLE_MAX}자를 초과해 잘랐습니다.")
    elif len(title) > COMMIT_TITLE_RECOMMENDED:
        # 권장치(50자) 초과: 자르지는 않고 경고만 표시 (사용자가 판단)
        warnings.append(
            f"권장 길이({COMMIT_TITLE_RECOMMENDED}자)를 초과했습니다. (현재 {len(title)}자)"
        )

    # --- 본문 불릿 확인 ---
    body = [ln for ln in lines[1:] if ln.strip()]
    bullets = [ln for ln in body if ln.strip().startswith("-")]
    if body and not bullets:
        warnings.append("본문에 불릿이 없습니다.")

    # 제목(잘라낸 버전) + 원본 본문을 합쳐 최종 텍스트 생성
    fixed = "\n".join([title] + lines[1:]).strip()
    return ValidationResult(True, warnings, fixed)


def validate_pr(text: str) -> ValidationResult:
    """PR 초안 규칙 검증 및 후처리.

    검증/후처리 항목:
    - TITLE 라인에서 제목 추출 (없으면 첫 줄을 제목으로 대체)
    - 제목 80자 초과 시 잘라냄
    - "### Why" 같은 변형 헤더를 "## Why" 로 정규화
    - 필수 섹션(Why/What/How to Test) 누락 및 불릿 부재 경고
    """
    warnings: list[str] = []
    text = _strip_code_fence(text)

    # --- TITLE: 라인 분리 ---
    # "TITLE:", "**TITLE**:" 등 AI가 출력할 수 있는 변형까지 허용
    m = re.search(r"^\s*(?:\*\*)?TITLE(?:\*\*)?\s*[:：]\s*(.+)$", text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        body = text[m.end():].strip()
    else:
        # TITLE 라인이 없으면 첫 줄을 제목으로 간주 (관대한 fallback)
        lines = text.splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip()
        warnings.append("TITLE: 라인이 없어 첫 줄을 제목으로 사용했습니다.")

    if not title:
        return ValidationResult(False, ["PR 제목을 찾을 수 없습니다."], text)

    # --- 제목 길이 규칙 ---
    if len(title) > PR_TITLE_MAX:
        title = title[:PR_TITLE_MAX].rstrip()
        warnings.append(f"PR 제목이 {PR_TITLE_MAX}자를 초과해 잘랐습니다.")

    # --- 섹션 헤더 정규화 ---
    # "### Why", "#### How to Test", "## What:" 같은 변형을
    # 표준 형식("## Why" 등)으로 통일한다.
    for section in PR_SECTIONS:
        name = section[len("## "):]  # Why / What / How to Test
        pattern = re.compile(rf"^#+\s*{re.escape(name)}\s*:?\s*$", re.IGNORECASE | re.MULTILINE)
        body = pattern.sub(section, body)

    # --- 필수 섹션 존재 여부 확인 ---
    for section in PR_SECTIONS:
        if section not in body:
            warnings.append(f"필수 섹션 누락: {section}")

    # --- 각 섹션의 불릿 존재 여부 확인 ---
    # 본문을 "## " 헤더 기준으로 섹션 단위로 나눈 뒤,
    # 각 섹션 안에 "- " 불릿이 최소 1개 있는지 검사한다.
    sections_split = re.split(r"^(?=## )", body, flags=re.MULTILINE)
    for sec in sections_split:
        sec_stripped = sec.strip()
        if any(sec_stripped.startswith(h) for h in PR_SECTIONS):
            if "- " not in sec and "•" not in sec:
                warnings.append(f"'{sec_stripped.splitlines()[0]}' 섹션에 불릿이 없습니다.")

    # 제목 + 빈 줄 + 본문 형태로 재조립
    fixed = f"{title}\n\n{body}".strip()
    return ValidationResult(True, warnings, fixed)


def format_pr_output(title: str, body: str) -> str:
    """터미널 출력용 PR 텍스트를 구분선/헤더로 구획한다."""
    return (
        "--- PR Title ---\n"
        f"{title}\n"
        "\n"
        "--- PR Body ---\n"
        f"{body}\n"
        "-----------------"
    )

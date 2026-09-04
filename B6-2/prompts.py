"""프롬프트 구성 모듈.

Commit/PR 양식, 변경 이유, 요구사항을 컨텍스트에 포함해
AI가 요구사항에 맞는 요약을 생성하도록 프롬프트를 설계한다.
"""

from __future__ import annotations

# Git 컨텍스트 타입 힌트용 (변경 파일 목록, diff 등을 담는 객체)
from git_collector import GitContext

# --- 시스템 프롬프트: AI에게 "역할"과 "출력 규칙"을 부여하는 부분 ---

# 커밋 메시지 생성용 규칙.
# Conventional Commits 접두사, 제목 길이, 본문 불릿 요구사항을 명시해
# 미션의 '커밋 메시지 품질 최소 기준'을 만족하도록 유도한다.
COMMIT_SYSTEM_PROMPT = """\
당신은 Git 변경 사항을 분석해 커밋 메시지를 작성하는 전문가입니다.
아래 규칙을 반드시 지켜서 한국어 커밋 메시지를 생성하세요.

[커밋 메시지 규칙]
1. 첫 줄은 커밋 제목입니다. Conventional Commits 접두사(feat/fix/docs/refactor/chore/test 등)를 사용하세요.
2. 커밋 제목은 50자 이내(최대 72자)로 작성하고, 마침표로 끝내지 않습니다.
3. 제목 다음 빈 줄을 두고, 본문을 작성합니다.
4. 본문은 핵심 변경 사항 1~3개를 "- " 불릿으로 요약합니다.
5. 본문에는 변경된 파일 또는 모듈 중 중요한 것을 1~3개 언급합니다.
6. 출력은 커밋 메시지 텍스트만 포함해야 하며, 따옴표·코드블록·설명을 덧붙이지 않습니다.
"""

# PR 초안 생성용 규칙.
# Why/What/How to Test 섹션 헤더와 각 섹션 최소 1개 불릿을 강제해
# 미션에서 요구하는 PR 본문 템플릿 구조를 만족하도록 유도한다.
PR_SYSTEM_PROMPT = """\
당신은 Git 변경 사항을 분석해 Pull Request 초안을 작성하는 전문가입니다.
아래 규칙을 반드시 지켜서 한국어 PR 초안을 생성하세요.

[PR 형식 규칙]
1. 첫 줄에 "TITLE: " 로 시작하는 PR 제목 1줄을 작성합니다. (Conventional Commits 접두사 사용, 최대 80자)
2. 그 다음 빈 줄을 두고 PR 본문을 작성합니다.
3. PR 본문은 반드시 아래 3개 섹션 헤더를 정확히 이 순서로 포함합니다:
## Why
## What
## How to Test
4. 각 섹션에는 최소 1개 이상의 "- " 불릿을 작성합니다.
   - Why: 변경 배경/목적
   - What: 핵심 변경 사항 (파일/모듈 언급 포함)
   - How to Test: 실행 가능한 테스트 방법 (명령어 포함 권장)
5. 출력은 TITLE: 라인과 PR 본문만 포함하며, 코드블록이나 추가 설명을 덧붙이지 않습니다.
"""


def _truncate(text: str, max_chars: int) -> str:
    """텍스트가 너무 길면 앞부분만 잘라낸다.

    diff가 매우 큰 경우 API 요청 비용/토큰 한도 초과를 방지하기 위해
    앞부분(일반적으로 가장 중요한 변경)만 전송하고 생략 표시를 붙인다.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (이하 생략)"


def build_commit_user_prompt(ctx: GitContext, max_diff_lines: int = 200) -> str:
    """커밋 메시지 생성용 user 프롬프트를 구성한다.

    브랜치명 + 변경 파일 목록 + diff 본문을 하나의 컨텍스트로 묶어
    AI가 '무엇을 왜 바꿨는지' 파악할 수 있게 한다.

    Args:
        ctx: git 명령으로 수집한 변경 사항 컨텍스트
        max_diff_lines: 전송할 diff 최대 줄 수 (토큰/비용 제한용)
    """
    # 파일 목록이 너무 많으면 앞 20개만 사용 (프롬프트 길이 제한)
    files = "\n".join(f"- {f}" for f in ctx.changed_files[:20])
    return f"""\
아래 Git 변경 사항을 기반으로 커밋 메시지를 생성하세요.

[현재 브랜치]
{ctx.branch}

[변경된 파일 목록]
{files}

[git diff]
```diff
{_truncate(ctx.diff, max_diff_lines * 120)}
```
"""


def build_pr_user_prompt(ctx: GitContext, max_diff_lines: int = 200) -> str:
    """PR 초안 생성용 user 프롬프트를 구성한다.

    커밋용과 동일한 컨텍스트 구조를 사용하되,
    PR은 범위가 더 넓다는 점을 반영해 지시 문구만 다르게 한다.
    """
    files = "\n".join(f"- {f}" for f in ctx.changed_files[:20])
    return f"""\
아래 Git 변경 사항을 기반으로 Pull Request 제목과 본문 초안을 생성하세요.

[현재 브랜치]
{ctx.branch}

[변경된 파일 목록]
{files}

[git diff]
```diff
{_truncate(ctx.diff, max_diff_lines * 120)}
```
"""

"""AI 기반 Git 커밋/PR 자동 생성기 CLI.

전체 흐름: git status/diff 수집 → (safe-mode) → AI API 호출 → 검증/후처리 → 터미널 출력

사용 예:
    python main.py commit
    python main.py pr
    python main.py commit --model gemini-3-flash --temperature 0.2 --max-tokens 500
    python main.py pr --safe-mode --max-files 5 --max-lines 100
"""

from __future__ import annotations

# CLI 인자 파싱 (명령어/옵션 정의)
import argparse
# .env 파일 경로 확인용 (프로젝트 루트 기준)
import os
# untracked 파일 내용을 직접 읽기 위한 git 명령 실행용
import subprocess
# 종료 코드 반환 및 stderr 출력용
import sys

from ai_client import AIAPIError, AIClient, DEFAULT_MODEL
from git_collector import GitContext, GitError, collect_context, is_git_repository
from prompts import (
    COMMIT_SYSTEM_PROMPT,
    PR_SYSTEM_PROMPT,
    build_commit_user_prompt,
    build_pr_user_prompt,
)
from safe_mode import DEFAULT_MAX_FILES, DEFAULT_MAX_LINES, apply_safe_mode
from validators import format_pr_output, validate_commit, validate_pr


# --- 로그 출력 헬퍼 (미션 예시의 [INFO]/[DONE]/[ERROR] 형식) ---

def info(msg: str) -> None:
    """진행 상황 정보를 stdout에 출력한다."""
    print(f"[INFO] {msg}")


def done(msg: str) -> None:
    """작업 완료 메시지를 stdout에 출력한다."""
    print(f"[DONE] {msg}")


def error(msg: str) -> None:
    """오류 메시지를 stderr에 출력한다."""
    print(f"[ERROR] {msg}", file=sys.stderr)


def load_dotenv(path: str = ".env") -> None:
    """.env 파일을 찾아 환경변수로 미리 로드한다 (외부 의존성 없이 표준 라이브러리만 사용).

    매번 `source .env`로 직접 불러오는 불편을 없애기 위해,
    `python main.py commit` 실행 시 현재 디렉토리(프로젝트 루트)의 `.env` 파일을 자동으로 찾아 읽는다.

    규칙:
    - `KEY=VALUE` 형태의 줄만 처리하며, `#`으로 시작하는 주석/가장처리된 빈 줄은 무시한다.
    - 값을 둘러싼 따옴표(`".."`, `'..'`)는 제거한다.
    - 이미 셔림 환경변수로 설정된 값(`export AI_API_KEY=...`)이 있으면 `.env` 값으로 덮어쓰지 않는다
      (셔림 환경변수가 항상 우선순위가 높다).
    """
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # 이미 셔림에서 명시적으로 export된 값이 있으면 그것을 우선한다 (setdefault).
            os.environ.setdefault(key, value)


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서를 구성한다.

    commit / pr 두 개의 하위 명령을 제공하며,
    미션 요구사항대로 모델/temperature/max_tokens 등 API 호출 파라미터를
    옵션으로 변경할 수 있게 한다.
    """
    parser = argparse.ArgumentParser(
        prog="ai-gitgen",
        description="Git 변경 사항(git status/diff)을 AI API에 전달해 커밋 메시지/PR 초안을 생성하는 CLI 도구",
    )
    # 하위 명령(commit/pr)은 필수 — 없으면 사용법을 보여주고 종료
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_options(p: argparse.ArgumentParser) -> None:
        """commit/pr 양쪽 명령에 공통 옵션을 붙인다."""
        # AI 모델명 (기본값: ai_client.DEFAULT_MODEL = gemini-3-flash)
        p.add_argument("--model", default=DEFAULT_MODEL, help=f"AI 모델명 (기본값: {DEFAULT_MODEL})")
        p.add_argument(
            "--temperature",
            type=float,
            default=0.3,
            help="생성 다양성 조절 (0.0~2.0, 낮을수록 일관됨. 기본값: 0.3)",
        )
        p.add_argument("--max-tokens", type=int, default=800, help="최대 생성 토큰 수 (기본값: 2000)")
        # safe-mode: 민감정보 마스킹 + diff 전송량 제한을 함께 활성화
        p.add_argument(
            "--safe-mode",
            action="store_true",
            help="민감정보 마스킹 + diff 전송량 제한 활성화",
        )
        p.add_argument(
            "--max-files",
            type=int,
            default=DEFAULT_MAX_FILES,
            help=f"safe-mode에서 전송할 최대 파일 수 (기본값: {DEFAULT_MAX_FILES})",
        )
        p.add_argument(
            "--max-lines",
            type=int,
            default=DEFAULT_MAX_LINES,
            help=f"safe-mode에서 전송할 최대 diff 줄 수 (기본값: {DEFAULT_MAX_LINES})",
        )

    p_commit = sub.add_parser("commit", help="커밋 메시지 자동 생성")
    add_common_options(p_commit)

    p_pr = sub.add_parser("pr", help="PR 제목/본문 초안 자동 생성")
    add_common_options(p_pr)

    # models: --model 옵션에 무엇을 넣을 수 있는지 매번 문서를 찾지 않아도
    # 터미널에서 바로 확인할 수 있게 해주는 편의 명령어.
    sub.add_parser("models", help="--model 옵션에 쓸 수 있는 사용 가능한 모델 목록을 표시")

    return parser


def run_list_models() -> int:
    """`models` 명령: 현재 API Key로 쓸 수 있는 모델 목록을 조회해 출력한다.

    git 컴텍스트가 필요 없으므로 Git 리포지토리 밖에서도 실행할 수 있다.
    """
    try:
        # 모델 목록 조회만 할 거라 temperature/max_tokens는 의미 없음 (기본값 그대로 사용)
        client = AIClient()
    except AIAPIError as exc:
        error(str(exc))
        return 1

    try:
        models = client.list_models()
    except AIAPIError as exc:
        error(f"모델 목록 조회 실패: {exc}")
        return 1

    if not models:
        info("조회된 모델이 없습니다.")
        return 0

    print("\n--- 사용 가능한 모델 (--model 옵션에 그대로 사용) ---")
    for m in models:
        print(f"  {m['id']:<24} ({m['owned_by']})")
    print("----------------------------------------\n")
    return 0


def _include_untracked_diff(ctx: GitContext) -> None:
    """untracked 파일은 git diff에 나타나지 않으므로 내용을 diff에 보강한다.

    새로 만든 파일(아직 git add 하지 않음)도 AI가 분석할 수 있도록
    파일 내용을 읽어 '+ ' 접두사가 붙은 가짜 diff 형식으로 ctx.diff 뒤에 덧붙인다.
    프롬프트 길이 폭주를 막기 위해 최대 20개 파일, 파일당 4000자까지만 읽는다.
    """
    try:
        # --exclude-standard: .gitignore 에 등록된 파일은 제외
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        untracked = [ln for ln in result.stdout.splitlines() if ln.strip()]
    except FileNotFoundError:
        return

    extra_parts: list[str] = []
    for path in untracked[:20]:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read(4000)
        except OSError:
            # 읽을 수 없는 파일(바이너리, 권한 문제 등)은 건너뛴다.
            continue
        # 새 파일의 diff는 전부 추가(+) 라인이므로 그 형태로 재구성한다.
        header = f"diff --git a/{path} b/{path} (새 파일, untracked)\n--- /dev/null\n+++ b/{path}\n"
        body = "\n".join(f"+{ln}" for ln in content.splitlines())
        extra_parts.append(header + body + "\n")

    if extra_parts:
        ctx.diff = (ctx.diff + "\n" + "\n".join(extra_parts)).strip()
        ctx.diff_line_count = len(ctx.diff.splitlines())


def prepare_context(args: argparse.Namespace) -> GitContext | None:
    """Git 컨텍스트를 수집하고 safe-mode를 적용한다.

    Returns:
        변경 사항이 있으면 safe-mode가 적용된 GitContext,
        변경 사항이 없으면 None (호출부에서 안내 후 종료).

    Raises:
        GitError: Git 리포지토리 밖에서 실행한 경우.
    """
    # 미션 요구사항: CLI 실행은 Git이 초기화된 프로젝트 루트에서 수행되어야 함
    if not is_git_repository():
        raise GitError("현재 디렉토리는 Git 리포지토리가 아닙니다. 프로젝트 루트에서 실행하세요.")

    ctx = collect_context()
    if not ctx.changed_files:
        # 미션 요구사항: 변경 사항이 없으면 안내 메시지 출력 후 종료
        return None

    info(f"Git status 수집 완료: {len(ctx.changed_files)}개 파일 변경 감지")
    info(f"Git diff 수집 완료: {ctx.diff_line_count}줄")
    info(f"현재 브랜치: {ctx.branch}")

    # untracked(새) 파일 내용도 diff에 포함시켜 AI가 분석 가능하게 함
    _include_untracked_diff(ctx)

    # --- safe-mode 적용: 민감정보 마스킹 + 전송량 제한 ---
    if args.safe_mode:
        ctx.diff, notes = apply_safe_mode(ctx.diff, args.max_files, args.max_lines)
        for note in notes:
            info(f"safe-mode {note}")

    return ctx


def run_generate(args: argparse.Namespace, command: str) -> int:
    """공통 흐름 실행: 컨텍스트 수집 → AI 호출 → 검증/후처리 → 출력.

    Returns:
        프로세스 종료 코드 (0: 성공, 1: 오류)
    """
    # --- 1. Git 변경 사항 수집 (+ safe-mode) ---
    try:
        ctx = prepare_context(args)
    except GitError as exc:
        error(str(exc))
        return 1

    # 변경 사항이 없으면 생성하지 않고 정상 종료 (미션 요구사항)
    if ctx is None:
        info("변경 사항이 없습니다. 생성하지 않고 종료합니다.")
        return 0

    # --- 2. AI 클라이언트 준비 (이 시점에 API Key 환경변수 확인) ---
    try:
        client = AIClient(model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
    except AIAPIError as exc:
        # API Key 미설정 등 초기화 실패 시 트레이스백 대신 안내 메시지만 출력
        error(str(exc))
        return 1

    try:
        info("AI API 요청 중...")
        if command == "commit":
            # --- 3a. 커밋 메시지 생성 ---
            raw = client.chat(COMMIT_SYSTEM_PROMPT, build_commit_user_prompt(ctx))
            # 길이/형식 규칙 검증 및 후처리 (제목 잘라내기 등)
            result = validate_commit(raw)
            for w in result.warnings:
                info(f"검증 경고: {w}")
            done("커밋 메시지 생성 완료")
            # 구분선으로 구획을 나눠 사용자가 복사하기 쉽게 출력
            print("\n--- Commit Message ---")
            print(result.fixed_text)
            print("----------------------\n")
        else:
            # --- 3b. PR 초안 생성 ---
            raw = client.chat(PR_SYSTEM_PROMPT, build_pr_user_prompt(ctx))
            result = validate_pr(raw)
            for w in result.warnings:
                info(f"검증 경고: {w}")
            done("PR 초안 생성 완료")
            # fixed_text는 "제목\n\n본문" 형태이므로 제목/본문으로 분리해 출력
            title, _, body = result.fixed_text.partition("\n\n")
            print()
            print(format_pr_output(title, body))
            print()
    except AIAPIError as exc:
        # 네트워크 오류, 인증 실패 등 API 관련 모든 오류 처리
        error(f"AI API 호출 실패: {exc}")
        return 1

    # --- 4. 비용 관리 정보 및 주의 안내 ---
    info(f"AI API 호출 횟수: {client.call_count}회")
    info("생성 결과는 초안입니다. 검토 후 적용하세요.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점.

    Args:
        argv: 커맨드라인 인자 (None이면 sys.argv 사용, 테스트 시 직접 전달 가능)
    """
    # 인자 파싱보다 먼저 .env를 로드해 API Key 등을 미리 환경변수로 옥린다.
    # (이미 `export`로 설정된 값이 있으면 그대로 유지되고 .env 값으로 덮어쓰이지 않는다)
    load_dotenv()
    args = build_arg_parser().parse_args(argv)
    try:
        if args.command == "models":
            return run_list_models()
        return run_generate(args, args.command)
    except KeyboardInterrupt:
        # Ctrl+C 로 중단한 경우 (종료 코드 130 = SIGINT 관례)
        error("사용자에 의해 중단되었습니다.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

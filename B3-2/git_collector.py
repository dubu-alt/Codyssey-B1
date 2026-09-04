"""Git 명령 실행 결과를 수집하는 모듈.

`git status`, `git diff` 실행 결과를 프로그램 입력으로 변환한다.
"""

from __future__ import annotations

# Git 명령 실행을 위해 서브프로세스 모듈 사용 (외부 라이브러리 없이 표준 라이브러리만 사용)
import subprocess
from dataclasses import dataclass, field


class GitError(Exception):
    """Git 명령 실행 실패 시 발생하는 예외.

    - git이 설치되지 않은 경우
    - 현재 디렉토리가 Git 리포지토리가 아닌 경우
    - git 명령 자체가 실패한 경우(비정상 종료 코드)
    """


@dataclass
class GitContext:
    """AI 프롬프트에 전달할 Git 컨텍스트 데이터 묶음.

    git 명령 실행 결과를 하나의 객체로 모아서
    프롬프트 빌더(prompts.py)와 CLI(main.py)에서 사용한다.
    """

    # `git diff HEAD` 원본 출력 (스테이징 + 언스테이징 변경 모두 포함)
    diff: str = ""
    # 현재 체크아웃된 브랜치 이름 (예: main, feature/xxx)
    branch: str = ""
    # 변경된 파일 경로 목록 (status --porcelain 에서 추출)
    changed_files: list[str] = field(default_factory=list)
    # diff 텍스트의 총 줄 수 (로그 출력용)
    diff_line_count: int = 0


def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Git 명령을 실행하고 stdout을 반환한다.

    Args:
        args: git 뒤에 붙일 인자 목록 (예: ["status", "--porcelain"])
        cwd: 명령을 실행할 디렉토리 (None이면 현재 디렉토리)

    Returns:
        git 명령의 표준 출력(stdout) 문자열

    Raises:
        GitError: git 실행 파일이 없거나 명령이 비정상 종료된 경우
    """
    try:
        # capture_output=True: stdout/stderr를 파이프로 받아옴
        # text=True + encoding 지정: 바이트가 아닌 문자열로 디코딩
        # errors="replace": 깨진 바이트가 있어도 예외 대신 치환 문자로 처리
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        # 시스템에 git이 설치되어 있지 않은 경우
        raise GitError("git 명령을 찾을 수 없습니다. Git이 설치되어 있는지 확인하세요.") from exc

    if result.returncode != 0:
        # git이 0이 아닌 종료 코드를 반환한 경우 (예: 리포지토리 밖에서 실행)
        stderr = (result.stderr or "").strip()
        raise GitError(f"git {' '.join(args)} 실행 실패: {stderr}")
    return result.stdout


def is_git_repository(cwd: str | None = None) -> bool:
    """현재 디렉토리가 Git 리포지토리(작업 트리) 내부인지 확인.

    `git rev-parse --is-inside-work-tree` 가 성공하면 리포지토리 내부로 판단한다.
    """
    try:
        _run_git(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        return True
    except GitError:
        return False


def collect_context(cwd: str | None = None) -> GitContext:
    """git status / git diff / 현재 브랜치를 수집해 GitContext를 반환한다.

    미션 요구사항 중 'Git 변경 사항 수집'을 담당하는 핵심 함수로,
    Git 명령 실행 결과를 AI API 호출의 입력값으로 변환한다.
    """
    ctx = GitContext()

    # --- 1. 현재 브랜치 이름 수집 ---
    ctx.branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).strip()

    # --- 2. 변경 파일 목록 수집 ---
    # --porcelain: 기계가 파싱하기 좋은 짧은 형식("XY <path>")으로 출력
    status_output = _run_git(["status", "--porcelain"], cwd=cwd)
    for line in status_output.splitlines():
        if line.strip():
            # "XY <path>" 형식에서 앞의 상태 코드(XY)와 공백 1칸을 제거하고 경로만 추출
            path = line[3:].strip()
            if "->" in path:
                # rename(R) 상태인 경우 "old -> new" 형태이므로 새 경로만 사용
                path = path.split("->")[-1].strip()
            if path.startswith('"') and path.endswith('"'):
                # 특수문자가 포함된 경로는 git이 따옴표로 감싸므로 제거
                path = path[1:-1]
            ctx.changed_files.append(path)

    # --- 3. diff 내용 수집 ---
    # `diff HEAD`: 마지막 커밋 대비 스테이징된 변경 + 언스테이징 변경을 모두 포함
    ctx.diff = _run_git(["diff", "HEAD"], cwd=cwd)
    ctx.diff_line_count = len(ctx.diff.splitlines())

    return ctx


#!/usr/bin/env python3
"""safe-mode 실전 데모 스크립트.

R.md에 넣을 "가상 시나리오"를 실제 코드로 재현한다. AI API 호출을 제외한
모든 단계(git 수집, safe-mode 마스킹/제한, 출력 검증)를 B6-2 저장소의
실제 함수를 그대로 호출해서 보여준다.

흐름:
    1. B6-2 저장소(git_collector.py / safe_mode.py / validators.py)를
       클론(또는 --repo 로 지정한 로컬 경로 사용)
    2. 임시 git 저장소를 만들고, 민감정보가 섞인 변경 사항(12개 파일,
       API Key / AWS Key / Slack 토큰 / 이메일 등)을 실제 커밋 전 상태로 준비
    3. git_collector.collect_context() 를 실제로 호출해 git status/diff 수집
    4. safe_mode.apply_safe_mode() 를 실제로 적용해 마스킹 + 전송량 제한 확인
    5. validators.validate_commit() / validate_pr() 를 예시 텍스트에 적용해
       검증/후처리 결과 확인
       (5번만 실제 AI 응답 대신 예시 텍스트 사용 -- API Key 없이도
        전체 흐름을 확인하기 위함. 나머지는 전부 실제 실행 결과다.)

사용법:
    python demo_safe_mode.py                      # 저장소를 임시 디렉토리에 클론해서 실행
    python demo_safe_mode.py --repo /path/to/B6-2  # 이미 클론된 로컬 경로 사용
    python demo_safe_mode.py --keep                # 데모용 git 저장소를 지우지 않고 보존

의존성: 표준 라이브러리만 사용 (B6-2 자체가 외부 라이브러리 없이 동작하도록 만들어져 있음).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/dubu-alt/B6-2.git"


def run(cmd: list[str], cwd: Path | None = None) -> str:
    """명령을 실행하고 stdout을 반환한다. 실패하면 예외를 던진다."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


def prepare_repo(repo_path: str | None, tmp_root: Path) -> Path:
    """B6-2 소스를 준비한다. --repo 가 없으면 임시 디렉토리에 새로 클론한다."""
    if repo_path:
        return Path(repo_path).resolve()
    dest = tmp_root / "B6-2"
    print(f"[SETUP] {REPO_URL} 클론 중...")
    run(["git", "clone", "--depth", "1", REPO_URL, str(dest)])
    return dest


def build_demo_git_repo(demo_dir: Path) -> None:
    """민감정보가 섞인 변경 사항을 가진 데모 git 저장소를 실제로 만든다.

    1) 정상적인 초기 커밋을 하나 만들고
    2) 그 위에 실수로 비밀 값을 넣은 변경 사항(아직 커밋 안 함)을 더한다.
       -> git status/diff에 12개 파일 변경, 민감정보 포함 상태가 재현된다.
    """
    demo_dir.mkdir(parents=True, exist_ok=True)
    run(["git", "init", "-q"], cwd=demo_dir)
    run(["git", "config", "user.email", "demo@example.com"], cwd=demo_dir)
    run(["git", "config", "user.name", "Demo"], cwd=demo_dir)

    (demo_dir / "config").mkdir(exist_ok=True)
    (demo_dir / "notify.py").write_text(
        "import requests\n\n"
        'WEBHOOK_URL = "https://hooks.example.com/webhook"\n\n'
        "def send_alert(msg):\n"
        '    requests.post(WEBHOOK_URL, json={"text": msg})\n',
        encoding="utf-8",
    )
    (demo_dir / "config" / "settings.py").write_text(
        'DEBUG = False\nLOG_LEVEL = "INFO"\n', encoding="utf-8"
    )
    run(["git", "add", "-A"], cwd=demo_dir)
    run(["git", "commit", "-q", "-m", "chore: initial project skeleton"], cwd=demo_dir)

    # --- 여기서부터 '실수로 민감정보를 넣은' 변경 사항 (아직 커밋 전) ---
    (demo_dir / "notify.py").write_text(
        "import requests\n\n"
        'WEBHOOK_URL = "https://hooks.example.com/webhook"\n'
        'SLACK_BOT_TOKEN = "xoxb-1234567890-abcdefghijklmnop"\n\n'
        "def send_alert(msg):\n"
        '    headers = {"Authorization": "Bearer sk-ant-api03-abc123def456ghi789"}\n'
        "    requests.post(WEBHOOK_URL, headers=headers, json={\"text\": msg})\n",
        encoding="utf-8",
    )
    (demo_dir / "config" / "settings.py").write_text(
        "DEBUG = False\n"
        'LOG_LEVEL = "INFO"\n'
        'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"\n'
        'GOOGLE_API_KEY = "AIzaSyD1234567890abcdefghijklmnopqrstuv"\n'
        'ADMIN_EMAIL = "dev-team@example.com"\n',
        encoding="utf-8",
    )
    (demo_dir / ".env").write_text(
        "AI_API_KEY=sk-or-v1-abcdef1234567890\nDB_PASSWORD=hunter2super\n",
        encoding="utf-8",
    )
    # 파일 수 제한(기본 10개)과 줄 수 제한(기본 200줄)을 실제로 넘기기 위해
    # 자잘한 파일 9개를 추가로 만든다.
    for i in range(1, 10):
        lines = [f"# module_{i}.py"]
        for j in range(1, 21):
            lines.append(f"def func_{i}_{j}():")
            lines.append(f"    return {i} * {j}")
        (demo_dir / f"module_{i}.py").write_text("\n".join(lines) + "\n", encoding="utf-8")

    run(["git", "add", "-A"], cwd=demo_dir)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> int:
    parser = argparse.ArgumentParser(description="B6-2 safe-mode 실전 데모")
    parser.add_argument("--repo", default=None, help="이미 클론된 B6-2 로컬 경로 (없으면 새로 클론)")
    parser.add_argument("--keep", action="store_true", help="데모용 임시 git 저장소를 삭제하지 않고 남긴다")
    args = parser.parse_args()

    tmp_root = Path(tempfile.mkdtemp(prefix="aigitgen-demo-"))
    try:
        repo_dir = prepare_repo(args.repo, tmp_root)
        sys.path.insert(0, str(repo_dir))

        from git_collector import collect_context, is_git_repository  # type: ignore
        from safe_mode import apply_safe_mode  # type: ignore
        from validators import validate_commit, validate_pr  # type: ignore

        demo_dir = tmp_root / "demo"
        build_demo_git_repo(demo_dir)

        section("1. git_collector.collect_context() 실제 실행")
        print("is_git_repository:", is_git_repository(cwd=str(demo_dir)))
        ctx = collect_context(cwd=str(demo_dir))
        print("branch:", ctx.branch)
        print("changed_files:", len(ctx.changed_files), "개 -", ctx.changed_files)
        print("diff_line_count:", ctx.diff_line_count)

        print("\n[safe-mode 적용 전] diff에 그대로 들어있는 민감정보 예시")
        keywords = ("xoxb", "sk-ant", "sk-or", "AKIA", "AIzaSy", "ADMIN_EMAIL", "DB_PASSWORD")
        for line in ctx.diff.splitlines():
            if any(k in line for k in keywords):
                print(" ", line)

        section("2. safe_mode.apply_safe_mode() 실제 실행")
        limited_diff, messages = apply_safe_mode(ctx.diff, max_files=10, max_lines=200)
        for m in messages:
            print(f"[INFO] safe-mode {m}")

        print("\n[safe-mode 적용 후] 실제로 AI 프롬프트에 들어갈 내용 중 마스킹된 줄")
        for line in limited_diff.splitlines():
            if "MASKED" in line:
                print(" ", line)
        print(f"\n최종 전송 diff 줄 수: {len(limited_diff.splitlines())}줄")

        section("3. validators.py 실제 실행 (AI 응답은 예시 텍스트로 대체)")
        fake_commit = (
            "feat: Slack 알림 및 AWS/Google API 연동 설정 파일을 매우 길고 장황하게 "
            "한 줄로 추가하는 커밋 제목입니다 초과 테스트용\n"
            "- notify.py에 Slack 알림 전송 함수 추가\n"
            "- config/settings.py에 외부 서비스 키 설정 추가"
        )
        r1 = validate_commit(fake_commit)
        print("[validate_commit] warnings:", r1.warnings)
        print("[validate_commit] fixed_text 제목:", r1.fixed_text.splitlines()[0])

        fake_pr = (
            "TITLE: feat: Slack 알림 기능 추가\n\n"
            "## Why\n- 팀 채널에 배포 알림을 자동으로 보내기 위해 필요했습니다.\n\n"
            "## What\n- notify.py에 send_alert 함수 추가\n"
        )
        r2 = validate_pr(fake_pr)
        print("[validate_pr]     warnings:", r2.warnings)
        print("[validate_pr]     (How to Test 섹션이 자동으로 채워지지 않음을 확인)")

        return 0
    finally:
        if args.keep:
            print(f"\n데모 디렉토리를 남겨두었습니다: {tmp_root}")
        else:
            shutil.rmtree(tmp_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
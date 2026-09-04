# cli.py - 사용자와 대화하는 부분 (CLI 계층)
#
# input()으로 질문하고, 답을 검사해서 다시 물어보는
# "대화형 입력" 도우미 함수들이 모여 있다.

from datetime import datetime

from .models import Transaction


def ask(prompt: str) -> str:
    """질문을 보여주고 답을 입력받는 가장 기본 함수."""
    return input(prompt).strip()


def ask_date() -> str:
    """날짜를 입력받는다. 형식이 틀리면 다시 묻는다 (재입력 요구)."""
    while True:
        date = ask("날짜(YYYY-MM-DD): ")
        try:
            datetime.strptime(date, "%Y-%m-%d")  # 형식 검사
            return date
        except ValueError:
            print("[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
            print("[힌트] 예: 2024-01-15")          # 원인 + 해결 힌트


def ask_type() -> str:
    """타입(income/expense)을 입력받는다. 틀리면 다시 묻는다."""
    while True:
        tx_type = ask("타입(income/expense): ").lower()
        if tx_type in ("income", "expense"):
            return tx_type
        print("[오류] 타입은 income 또는 expense 여야 합니다.")
        print("[힌트] income=수입, expense=지출")


def ask_category(registered: list) -> str:
    """카테고리를 입력받는다. 등록되지 않은 이름이면 안내 후 다시 묻는다."""
    while True:
        category = ask(f"카테고리({', '.join(registered)}): ").strip().lower()
        if category in registered:
            return category
        print(f"[오류] 등록되지 않은 카테고리입니다: {category}")
        print("[힌트] 'category add' 명령으로 먼저 등록하거나, 목록에서 고르세요.")


def ask_amount() -> int:
    """금액을 입력받는다. 숫자가 아니거나 0 이하면 다시 묻는다."""
    while True:
        text = ask("금액(양수): ")
        try:
            amount = int(text)
        except ValueError:
            print("[오류] 금액은 숫자로 입력하세요.")
            print("[힌트] 예: 15000")
            continue
        if amount > 0:
            return amount
        print("[오류] 금액은 0보다 커야 합니다.")
        print("[힌트] 예: 15000")


def interactive_add(service) -> Transaction:
    """add 명령의 대화형 흐름 전체를 처리한다.

    날짜 -> 타입 -> 카테고리 -> 금액 -> 메모 -> 태그 순서로 하나씩 묻고,
    검사를 통과하면 거래 객체를 만들어 돌려준다.
    """
    date = ask_date()
    tx_type = ask_type()
    category = ask_category(service.get_categories())
    amount = ask_amount()
    memo = ask("메모(선택): ")                    # 선택 사항이라 검사 없음
    tags = ask("태그(쉼표로 구분, 없으면 엔터): ")

    # 서비스 쪽 검사 함수를 재활용해 최종 객체를 만든다
    return service.make_transaction(
        tx_type=tx_type, date=date, category=category,
        amount=amount, memo=memo, tags=tags,
    )

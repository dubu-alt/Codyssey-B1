# __main__.py - 프로그램의 출입문 (시작점)
#
# "python -m budget_app add" 처럼 실행하면 이 파일이 제일 먼저 실행된다.
# 명령어를 받아서 -> 서비스에 일을 시키고 -> 결과를 화면에 보여준다.

import argparse
import sys

from .cli import interactive_add
from .decorators import safe_command
from .services import BudgetService


def build_parser() -> argparse.ArgumentParser:
    """명령어 해석기(argparse)를 만들어 돌려준다.

    argparse의 장점:
      - --limit 같은 옵션을 알아서 쪼개준다
      - --help 옵션(사용법 출력)이 공짜로 생긴다
    """
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="나만의 용돈 기입장 - 콘솔 가계부 프로그램",
    )
    # 데이터가 저장될 폴더. 기본값은 ./data
    parser.add_argument("--data-dir", default="./data",
                        help="데이터 저장 폴더 (기본값: ./data)")

    # 하위 명령(add, list, ...)을 등록한다
    sub = parser.add_subparsers(dest="command", required=True)

    # --- add: 대화형으로 거래 추가 ---
    sub.add_parser("add", help="거래 추가 (대화형 입력)")

    # --- list: 목록 조회 ---
    p_list = sub.add_parser("list", help="최신순 거래 목록 조회")
    p_list.add_argument("--limit", type=int, default=10,
                        help="몇 건까지 보여줄지 (기본값: 10)")

    # --- search: 조건 검색 ---
    p_search = sub.add_parser("search", help="조건에 맞는 거래 검색")
    p_search.add_argument("--from", dest="date_from", default="", help="시작일 YYYY-MM-DD")
    p_search.add_argument("--to", dest="date_to", default="", help="종료일 YYYY-MM-DD")
    p_search.add_argument("--category", default="", help="카테고리")
    p_search.add_argument("--type", dest="tx_type", default="", help="income/expense")
    p_search.add_argument("--q", default="", help="메모 키워드")
    p_search.add_argument("--tag", default="", help="태그")

    # --- summary: 월별 요약 ---
    p_summary = sub.add_parser("summary", help="월별 요약 출력")
    p_summary.add_argument("--month", required=True, help="조회할 월 YYYY-MM")
    p_summary.add_argument("--top", type=int, default=3,
                           help="지출 TOP N 카테고리 개수 (기본값: 3)")

    # --- budget: 예산 설정 ---
    p_budget = sub.add_parser("budget", help="월 예산 설정/조회")
    budget_sub = p_budget.add_subparsers(dest="budget_action", required=True)
    p_bset = budget_sub.add_parser("set", help="예산 설정")
    p_bset.add_argument("--month", required=True, help="예산 월 YYYY-MM")
    p_bset.add_argument("--amount", type=int, required=True, help="예산 금액(양수)")

    # --- category: 카테고리 관리 ---
    p_cat = sub.add_parser("category", help="카테고리 관리")
    cat_sub = p_cat.add_subparsers(dest="cat_action", required=True)
    p_cadd = cat_sub.add_parser("add", help="카테고리 추가")
    p_cadd.add_argument("--name", help="추가할 카테고리 이름 (없으면 대화형)")
    cat_sub.add_parser("list", help="카테고리 목록")
    p_crm = cat_sub.add_parser("remove", help="카테고리 삭제")
    p_crm.add_argument("--name", help="삭제할 카테고리 이름 (없으면 대화형)")

    # --- update: 거래 수정 (옵션 기반으로 고정) ---
    p_update = sub.add_parser("update",
                              help="거래 수정 (옵션 방식 고정: 바꿀 항목만 옵션으로 지정)")
    p_update.add_argument("--id", required=True, help="수정할 거래 id")
    p_update.add_argument("--date", default="", help="새 날짜 YYYY-MM-DD")
    p_update.add_argument("--type", dest="new_type", default="", help="income/expense")
    p_update.add_argument("--category", default="", help="새 카테고리")
    p_update.add_argument("--amount", type=int, default=0, help="새 금액(양수)")
    p_update.add_argument("--memo", default=None, help="새 메모")
    p_update.add_argument("--tags", default=None, help="새 태그(쉼표 구분)")

    # --- delete: 거래 삭제 ---
    p_delete = sub.add_parser("delete", help="거래 삭제")
    p_delete.add_argument("--id", required=True, help="삭제할 거래 id")

    # --- export / import: CSV 내보내기/가져오기 ---
    p_export = sub.add_parser("export", help="CSV로 내보내기")
    p_export.add_argument("--out", required=True, help="저장할 CSV 파일 경로")
    p_export.add_argument("--month", default="", help="특정 월만 YYYY-MM")
    p_export.add_argument("--from", dest="date_from", default="", help="시작일 YYYY-MM-DD")
    p_export.add_argument("--to", dest="date_to", default="", help="종료일 YYYY-MM-DD")

    p_import = sub.add_parser("import", help="CSV에서 가져오기")
    p_import.add_argument("--from", dest="csv_path", required=True,
                          help="읽어올 CSV 파일 경로")

    return parser


@safe_command  # 오류가 나면 [오류]/[힌트]를 보여주고 종료 코드 1을 돌려주는 데코레이터
def run(args) -> int:
    """명령을 실제로 수행하는 함수. 결과 메시지를 출력하고 종료 코드를 돌려준다."""
    service = BudgetService(args.data_dir)  # 저장소 준비 (파일 자동 생성 포함)

    if args.command == "add":
        tx = interactive_add(service)       # 대화형으로 정보 입력받기
        print(service.add(tx))              # 저장 + 성공 메시지 출력

    elif args.command == "list":
        print(service.list_transactions(args.limit))

    elif args.command == "search":
        print(service.search(args.date_from, args.date_to, args.category,
                             args.tx_type, args.q, args.tag))

    elif args.command == "summary":
        print(service.summary(args.month, args.top))

    elif args.command == "budget":
        if args.budget_action == "set":
            print(service.set_budget(args.month, args.amount))

    elif args.command == "category":
        if args.cat_action == "add":
            name = args.name if args.name else input("카테고리명: ").strip()
            print(service.category_add(name))
        elif args.cat_action == "list":
            print(service.category_list())
        elif args.cat_action == "remove":
            name = args.name if args.name else input("삭제할 카테고리명: ").strip()
            print(service.category_remove(name))

    elif args.command == "update":
        print(service.update(args.id, new_date=args.date, new_type=args.new_type,
                             new_category=args.category, new_amount=args.amount,
                             new_memo=args.memo, new_tags=args.tags))

    elif args.command == "delete":
        print(service.delete(args.id))

    elif args.command == "export":
        # 요구사항: export는 --month 또는 --from/--to 중 최소 하나가 필요
        if not (args.month or args.date_from or args.date_to):
            raise ValueError(
                "export에는 조건이 필요합니다: --month 또는 --from/--to 중 하나 이상"
            )
        print(service.export_csv(args.out, args.month,
                                 args.date_from, args.date_to))

    elif args.command == "import":
        print(service.import_csv(args.csv_path))

    return 0  # 정상 종료 코드


def main() -> None:
    """프로그램 진입점. 명령을 파싱하고 실행하며, 종료 코드를 시스템에 넘긴다."""
    parser = build_parser()
    args = parser.parse_args()
    exit_code = run(args)
    sys.exit(exit_code)  # 0=성공, 그 외=오류


if __name__ == "__main__":
    main()

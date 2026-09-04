# services.py - 실제 일(비즈니스 로직)을 하는 파일 (서비스 계층)
#
# "거래 추가하면 뭘 검사하고 어떻게 저장하지?" 같은 판단을 여기서 한다.
# 화면 입출력(cli.py)과 파일 읽기/쓰기(storage.py) 사이에서
# 머리 역할을 맡는다.

import csv
import os
from datetime import datetime

from .decorators import measure_time
from .models import Transaction
from .storage import JsonlFileStore

# 허용되는 거래 타입 목록. 이외의 값은 오류 처리한다.
VALID_TYPES = ("income", "expense")
# 카테고리 파일이 비어있을 때 자동으로 만들어주는 기본 카테고리들 (안 A 방식)
DEFAULT_CATEGORIES = ["food", "transport", "rent", "etc"]


class BudgetService:
    """가계부의 모든 기능을 모아놓은 클래스.

    명령 하나가 메서드 하나와 대응된다.
      add / list / search / summary / budget / category / update / delete / import / export
    """

    def __init__(self, data_dir: str):
        # data_dir: 데이터 파일들을 보관할 폴더 (기본값 ./data)
        self.tx_store = JsonlFileStore(os.path.join(data_dir, "transactions.jsonl"))
        self.cat_store = JsonlFileStore(os.path.join(data_dir, "categories.jsonl"))
        self.budget_store = JsonlFileStore(os.path.join(data_dir, "budgets.jsonl"))

        # 요구사항: 파일이 없으면 초기화 안내 메시지를 출력한다.
        if not self.tx_store.exists():
            print("[초기화] data 폴더에 저장 파일이 없어 새로 만듭니다.")

        # 카테고리 파일이 비어있으면 기본 카테고리를 자동 생성 (안 A)
        if not any(True for _ in self.cat_store.read_all()):
            for name in DEFAULT_CATEGORIES:
                self.cat_store.append({"name": name})
            print(f"[초기화] 기본 카테고리를 만들었습니다: {', '.join(DEFAULT_CATEGORIES)}")

        # 예산 파일도 미리 만들어 둔다 (빈 파일)
        if not self.budget_store.exists():
            self.budget_store.rewrite([])

    # ------------------------------------------------------------------
    # 내부 도우미 함수들 (바깥에서 직접 부르지 않는 것들)
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        """새 거래에 붙일 고유 번호(id)를 만든다.

        기존 id 중 가장 큰 숫자를 찾아 1을 더한 값.
        예: TX-000007까지 있으면 -> TX-000008
        """
        max_num = 0
        for tx in self.tx_store.read_transactions():  # 스트리밍으로 훑으면서
            try:
                num = int(tx.id.split("-")[1])        # "TX-000012" -> 12
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue  # 이상한 형태의 id는 무시
        return f"TX-{max_num + 1:06d}"                # 6자리로 채움: TX-000013

    def get_categories(self) -> list[str]:
        """등록된 카테고리 이름 목록을 돌려준다."""
        names = []
        for record in self.cat_store.read_all():
            names.append(record.get("name", ""))
        return [n for n in names if n]  # 빈 이름은 제거

    def category_exists(self, name: str) -> bool:
        """카테고리가 등록되어 있는지 확인한다."""
        return name in self.get_categories()

    def validate_date(self, date: str) -> None:
        """날짜 형식이 YYYY-MM-DD가 맞는지 검사한다. 틀리면 오류 발생."""
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"날짜 형식이 올바르지 않습니다: '{date}' (YYYY-MM-DD). 예: 2024-01-15"
            )

    def validate_amount(self, amount: int) -> None:
        """금액이 양수인지 검사한다. 0 이하면 오류 발생."""
        if amount <= 0:
            raise ValueError(f"금액은 0보다 커야 합니다: {amount}")

    def validate_type(self, tx_type: str) -> None:
        """타입이 income 또는 expense인지 검사한다."""
        if tx_type not in VALID_TYPES:
            raise ValueError(
                f"타입은 income 또는 expense여야 합니다: '{tx_type}'"
            )

    def validate_category(self, category: str) -> None:
        """카테고리가 등록되어 있는지 검사한다."""
        if not self.category_exists(category):
            registered = ", ".join(self.get_categories())
            raise ValueError(
                f"등록되지 않은 카테고리입니다: '{category}'. "
                f"현재 등록됨: {registered} (category add 로 추가 가능)"
            )

    def make_transaction(self, tx_type, date, category, amount,
                         memo="", tags="") -> Transaction:
        """검사를 통과한 거래 객체를 만드는 공용 함수.

        add 명령과 import 명령이 함께 쓴다. (같은 검사를 두 번 쓰지 않기 위해)
        """
        self.validate_type(tx_type)
        self.validate_date(date)
        self.validate_amount(amount)
        self.validate_category(category)
        return Transaction(
            id=self._next_id(),
            type=tx_type,
            date=date,
            amount=int(amount),
            category=category,
            memo=memo,
            tags=tags,
        )

    # ------------------------------------------------------------------
    # 명령 구현부
    # ------------------------------------------------------------------

    def add(self, tx: Transaction) -> str:
        """거래를 파일에 저장하고 결과 메시지를 돌려준다."""
        self.tx_store.append(tx.to_dict())          # JSONL 파일 맨 뒤에 한 줄 추가
        return f"[저장 완료] id={tx.id}"

    @measure_time  # 데코레이터: 이 함수의 실행 시간을 자동으로 출력해준다
    def list_transactions(self, limit: int) -> str:
        """최신순으로 거래 목록을 돌려준다. (--limit N 개수 제한)

        스트리밍 처리: read_transactions() 제너레이터로 한 건씩 읽으며,
        최신 N건만 따로 보관한다. 파일 전체를 통째로 담아두지 않는다.
        """
        latest = []  # 최신 N개만 잠시 보관하는 자리
        for tx in self.tx_store.read_transactions():   # 한 건씩 흘러 들어온다
            latest.append(tx)
            latest.sort(key=lambda t: t.date + t.id, reverse=True)  # 날짜+id 최신순
            if len(latest) > limit:
                latest.pop()  # N개를 넘으면 가장 오래된 것 하나를 버린다
        if not latest:
            return "[안내] 저장된 거래가 없습니다."
        lines = []
        for tx in latest:
            # | 로 정보를 구분해서 보기 좋게 출력
            lines.append(f"{tx.id} | {tx.date} | {tx.type:<7} | "
                         f"{tx.category} | {tx.amount} | {tx.memo}")
        return "\n".join(lines)

    def search(self, date_from="", date_to="", category="",
               tx_type="", query="", tag="") -> str:
        """조건에 맞는 거래를 찾아 최신순으로 돌려준다.

        조건이 비어 있으면 그 조건은 무시한다(전부 해당).
        여기서도 제너레이터 스트리밍으로 파일을 읽는다.
        """
        results = []
        for tx in self.tx_store.read_transactions():
            # --- 조건 검사: 하나라도 안 맞으면 다음 거래로 넘어간다 ---
            if date_from and tx.date < date_from:
                continue                      # 시작일보다 이전이면 탈락
            if date_to and tx.date > date_to:
                continue                      # 종료일보다 이후면 탈락
            if category and tx.category != category:
                continue
            if tx_type and tx.type != tx_type:
                continue
            if query and query.lower() not in tx.memo.lower():
                continue                      # 메모에 키워드 없으면 탈락
            if tag and tag not in tx.tags.split(","):
                continue                      # 태그 목록에 없으면 탈락
            results.append(tx)

        if not results:
            return "[안내] 조건에 맞는 거래가 없습니다."
        results.sort(key=lambda t: t.date + t.id, reverse=True)  # 최신순 정렬
        lines = []
        for tx in results:
            lines.append(f"{tx.id} | {tx.date} | {tx.type:<7} | "
                         f"{tx.category} | {tx.amount} | {tx.memo}")
        return "\n".join(lines)

    def summary(self, month: str, top_n: int) -> str:
        """특정 월의 수입/지출 요약 + 카테고리별 지출 TOP N을 돌려준다."""
        total_income = 0   # 총 수입
        total_expense = 0  # 총 지출
        by_category = {}   # {카테고리: 지출 합계}

        for tx in self.tx_store.read_transactions():
            if not tx.date.startswith(month):
                continue  # 이 달의 거래가 아니면 건너뛴다
            if tx.type == "income":
                total_income += tx.amount
            else:
                total_expense += tx.amount
                by_category[tx.category] = by_category.get(tx.category, 0) + tx.amount

        lines = []
        if total_income == 0 and total_expense == 0:
            lines.append(f"[안내] {month} 에는 데이터가 없습니다.")
            return "\n".join(lines)

        balance = total_income - total_expense
        lines.append(f"총 수입: {total_income}원")
        lines.append(f"총 지출: {total_expense}원")
        lines.append(f"잔액: {balance}원")

        # 예산이 설정되어 있으면 사용률과 초과 경고를 함께 보여준다
        budget_amount = self._get_budget(month)
        if budget_amount is not None:
            usage = total_expense / budget_amount * 100  # 사용률(%)
            lines.append(f"예산: {budget_amount}원 (사용률 {usage:.1f}%)")
            if total_expense > budget_amount:
                lines.append("[경고] 예산을 초과했습니다! 지출을 줄이세요.")

        # 카테고리별 지출 TOP N (합계가 큰 순서대로 N개)
        top = sorted(by_category.items(), key=lambda x: x[1], reverse=True)[:top_n]
        if top:
            lines.append("")
            lines.append(f"지출 TOP {len(top)}")
            for rank, (cat_name, cat_sum) in enumerate(top, start=1):
                lines.append(f"{rank}) {cat_name} {cat_sum}원")

        return "\n".join(lines)

    def _get_budget(self, month: str):
        """저장된 월 예산을 찾는다. 없으면 None을 돌려준다."""
        for record in self.budget_store.read_all():
            if record.get("month") == month:
                return int(record.get("amount", 0))
        return None

    def set_budget(self, month: str, amount: int) -> str:
        """월 예산을 저장한다. 이미 있는 예산이면 새 값으로 덮어쓴다."""
        self.validate_amount(amount)
        records = [r for r in self.budget_store.read_all()
                   if r.get("month") != month]      # 기존 값은 빼고
        records.append({"month": month, "amount": amount})
        self.budget_store.rewrite(records)           # 안전하게 다시 쓰기
        return f"[저장 완료] {month} 예산 {amount}원"

    def category_add(self, name: str) -> str:
        """카테고리를 추가한다. 이미 있으면 알려준다."""
        name = name.strip().lower()  # 대소문자/공백 차이로 중복되지 않게 정리
        if not name:
            raise ValueError("카테고리 이름을 입력하세요.")
        if self.category_exists(name):
            return f"[안내] 이미 등록된 카테고리입니다: {name}"
        self.cat_store.append({"name": name})
        return f"[저장 완료] category={name}"

    def category_list(self) -> str:
        """카테고리 전체 목록을 돌려준다."""
        categories = self.get_categories()
        if not categories:
            return "[안내] 등록된 카테고리가 없습니다."
        return "\n".join(f"- {n}" for n in categories)

    def category_remove(self, name: str) -> str:
        """카테고리를 삭제한다. 단, 사용 중인 내역이 있으면 삭제를 막는다."""
        name = name.strip().lower()
        if not self.category_exists(name):
            raise ValueError(f"등록되지 않은 카테고리입니다: '{name}'")

        # 이 카테고리를 쓰는 거래가 하나라도 있는지 확인 (스트리밍 검사)
        for tx in self.tx_store.read_transactions():
            if tx.category == name:
                raise ValueError(
                    f"'{name}' 카테고리는 사용 중인 내역이 있어 삭제할 수 없습니다."
                )

        remaining = [{"name": n} for n in self.get_categories() if n != name]
        self.cat_store.rewrite(remaining)
        return f"[삭제 완료] category={name}"

    def find_by_id(self, target_id: str) -> Transaction:
        """id로 거래를 찾는다. 없으면 오류를 발생시킨다."""
        for tx in self.tx_store.read_transactions():
            if tx.id == target_id:
                return tx
        raise ValueError(f"존재하지 않는 id입니다: '{target_id}'")

    def delete(self, target_id: str) -> str:
        """거래 한 건을 삭제한다. (없는 id는 오류 처리)

        원자적 교체: storage.rewrite()가 임시 파일 + 교체 방식이라 안전하다.
        """
        self.find_by_id(target_id)  # 없으면 여기서 ValueError 발생
        remaining = [t.to_dict() for t in self.tx_store.read_transactions()
                     if t.id != target_id]
        self.tx_store.rewrite(remaining)
        return f"[삭제 완료] id={target_id}"

    def update(self, target_id: str, new_date="", new_type="",
               new_category="", new_amount=0, new_memo=None,
               new_tags=None) -> str:
        """거래를 수정한다 (옵션 기반 고정).

        옵션으로 넘어온 값만 새 값으로 바꾸고, 나머지는 원래 값을 유지한다.
        """
        old = self.find_by_id(target_id)  # 없으면 오류 발생

        # 새 값이 주어졌다면 각각 형식 검사를 한다.
        date = new_date or old.date
        if new_date:
            self.validate_date(new_date)
        tx_type = new_type or old.type
        if new_type:
            self.validate_type(new_type)
        category = new_category or old.category
        if new_category:
            self.validate_category(new_category)
        amount = new_amount if new_amount else old.amount
        if new_amount:
            self.validate_amount(new_amount)
        memo = new_memo if new_memo is not None else old.memo
        tags = new_tags if new_tags is not None else old.tags

        updated = Transaction(
            id=target_id, type=tx_type, date=date, amount=int(amount),
            category=category, memo=memo, tags=tags,
        )
        # 파일을 통째로 다시 쓰면서 해당 거래만 새 값으로 교체
        remaining = []
        for tx in self.tx_store.read_transactions():
            if tx.id == target_id:
                remaining.append(updated.to_dict())
            else:
                remaining.append(tx.to_dict())
        self.tx_store.rewrite(remaining)
        return f"[수정 완료] id={target_id}"

    def export_csv(self, out_path: str, month="",
                   date_from="", date_to="") -> str:
        """조건에 맞는 거래를 CSV 파일로 내보낸다.

        CSV 스키마(고정): date,type,category,amount,memo,tags (UTF-8, 헤더 포함)
        """
        count = 0
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
            for tx in self.tx_store.read_transactions():
                # 조건 검사: --month 또는 --from/--to 중 주어진 것만 적용
                if month and not tx.date.startswith(month):
                    continue
                if date_from and tx.date < date_from:
                    continue
                if date_to and tx.date > date_to:
                    continue
                writer.writerow([tx.date, tx.type, tx.category,
                                 tx.amount, tx.memo, tx.tags])
                count += 1
        return f"[완료] {out_path} ({count} records)"

    def import_csv(self, csv_path: str) -> str:
        """CSV 파일의 거래를 일괄 등록한다.

        잘못된 줄은 건너뛰고(skipped), 올바른 줄만 저장(imported)한다.
        """
        if not os.path.exists(csv_path):
            raise ValueError(f"파일을 찾을 수 없습니다: '{csv_path}'")

        imported = 0
        skipped = 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)  # 첫 줄(헤더)을 보고 칸 이름을 알아낸다
            for row in reader:
                try:
                    # tags는 "a,b" 문자열 그대로 저장 (단순함 유지)
                    tx = self.make_transaction(
                        tx_type=row["type"],
                        date=row["date"],
                        category=row["category"],
                        amount=int(row["amount"]),
                        memo=row.get("memo", ""),
                        tags=row.get("tags", ""),
                    )
                except (KeyError, ValueError, TypeError):
                    skipped += 1     # 형식이 틀린 줄은 세고 넘어간다
                    continue
                self.tx_store.append(tx.to_dict())
                imported += 1
        return f"[완료] imported={imported}, skipped={skipped}"

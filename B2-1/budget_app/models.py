# models.py - 데이터의 "모양"을 정하는 파일
# 거래 내역 한 건이 어떤 정보를 담는지 여기에 적어둔다.
# 다른 파일들(models 말고)은 이 모양을 그대로 사용하므로,
# 데이터 형태를 바꾸고 싶으면 이 파일만 고치면 된다.

from dataclasses import dataclass


@dataclass
class Transaction:
    """거래(수입/지출) 내역 한 건을 담는 상자.

    dataclass를 쓰면 __init__ 같은 기본 코드를 자동으로 만들어 준다.
    필드 설명:
      id       : 거래 고유 번호 (예: TX-000001) - 절대 겹치지 않는다
      type     : "income"(수입) 또는 "expense"(지출)
      date     : 날짜, 반드시 YYYY-MM-DD 형식
      amount   : 금액. 항상 양수 (수입/지출 구분은 type이 한다)
      category : 카테고리 이름 (예: food, transport)
      memo     : 메모. 선택 사항이라 비워도 된다
      tags     : 태그. 쉼표로 구분한 문자열 (예: "meal,lunch"). 선택 사항
    """
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: str = ""

    def to_dict(self):
        """거래 객체를 딕셔너리({키: 값})로 바꿔준다.

        왜 필요하나? -> JSONL 파일에는 딕셔너리 형태로 저장하는 게 편해서.
        """
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(record: dict):
        """딕셔너리를 다시 Transaction 객체로 바꿔준다.

        파일에서 읽어올 때 사용한다. 누락된 필드는 기본값으로 채운다.
        """
        return Transaction(
            id=record.get("id", ""),
            type=record.get("type", ""),
            date=record.get("date", ""),
            amount=int(record.get("amount", 0)),
            category=record.get("category", ""),
            memo=record.get("memo", ""),
            tags=record.get("tags", ""),
        )

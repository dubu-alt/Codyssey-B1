# storage.py - 파일에 읽고 쓰는 일만 전담하는 파일 (저장소 계층)
#
# "저장은 여기서만 한다"고 정해두면, 저장 방식을 바꾸고 싶을 때
# 이 파일 하나만 고치면 된다. 이런 역할 나누기가 '모듈화'다.

import json
import os
from typing import Iterator

from .models import Transaction


class JsonlFileStore:
    """JSONL 파일 한 개를 담당하는 저장소 클래스.

    JSONL = 한 줄에 데이터 한 건씩 저장하는 형식.
      예: {"id": "TX-000001", "amount": 15000}\n

    이 클래스가 하는 일은 딱 세 가지:
      1) read_all()   : 파일을 한 줄씩 흘려서 읽어주기 (제너레이터)
      2) append()     : 줄 한 건 덧붙여 쓰기
      3) rewrite()    : 파일 내용을 통째로 안전하게 다시 쓰기
    """

    def __init__(self, path: str):
        # path: 저장할 파일 위치 (예: data/transactions.jsonl)
        self.path = path
        folder = os.path.dirname(path)  # 파일이 들어갈 폴더 이름
        if folder:
            os.makedirs(folder, exist_ok=True)  # 폴더가 없으면 자동 생성

    def exists(self) -> bool:
        """파일이 이미 존재하는지 확인한다."""
        return os.path.exists(self.path)

    def read_all(self) -> Iterator[dict]:
        """파일의 모든 줄을 '한 줄씩' 넘겨주는 제너레이터.

        제너레이터(yield)를 쓰면 파일 전체를 메모리에 한 번에 올리지 않고,
        필요한 만큼 조금씩 읽을 수 있다. (스트리밍 처리)
        """
        if not self.exists():
            return  # 파일이 없으면 그냥 아무것도 안 넘겨줌(빈 상태로 끝)
        with open(self.path, encoding="utf-8") as f:
            for line in f:               # 파일에서 한 줄씩 꺼내서
                line = line.strip()
                if not line:             # 빈 줄은 건너뛴다
                    continue
                yield json.loads(line)   # 글자 -> 딕셔너리로 바꿔서 넘겨준다

    def read_transactions(self) -> Iterator[Transaction]:
        """read_all()과 같은데, 딕셔너리 대신 Transaction 객체로 넘겨준다."""
        for record in self.read_all():
            yield Transaction.from_dict(record)

    def append(self, record: dict) -> None:
        """새 거래 한 건을 파일 맨 뒤에 덧붙인다.

        "a" 모드(append)는 기존 내용을 지우지 않고 뒤에만 추가한다.
        ensure_ascii=False는 한글을 그대로 저장하기 위한 옵션이다.
        """
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def rewrite(self, records: list[dict]) -> None:
        """파일 내용을 통째로 다시 쓴다. (수정/삭제 때 사용)

        안전 장치(원자적 교체):
          1) 먼저 임시 파일(.tmp)에 완성본을 다 쓰고
          2) 성공하면 os.replace()로 원본과 단숨에 교체한다.
        중간에 프로그램이 죽어도 원본 파일이 망가지지 않는다.
        """
        tmp_path = self.path + ".tmp"  # 임시 파일 경로
        with open(tmp_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(tmp_path, self.path)  # 완성된 임시 파일을 원본으로 교체

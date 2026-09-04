# B2-1. 미리 알아야 할 개념 정리 (비전공자용)

> 이 문서는 B2-1 미션(용돈 기입장 프로그램)을 진행할 때 필요한 개념들을
> 비전공자도 이해할 수 있도록 쉽게 풀어쓴 설명서입니다.

---

## 목차
1. [콘솔 프로그램이란?](#1-콘솔-프로그램이란)
2. [CLI와 명령어 파싱 (argparse)](#2-cli와-명령어-파싱-argparse)
3. [dataclass - 데이터 담는 그릇](#3-dataclass---데이터-담는-그릇)
4. [클래스와 모듈화 - 코드를 나눠서 정리하기](#4-클래스와-모듈화---코드를-나눠서-정리하기)
5. [파일 입출력과 영구 저장](#5-파일-입출력과-영구-저장)
6. [JSONL과 CSV - 저장 파일 형식](#6-jsonl과-csv---저장-파일-형식)
7. [제너레이터(yield)와 스트리밍 처리](#7-제너레이터yield와-스트리밍-처리)
8. [데코레이터 - 공통 기능을 분리하는 포장지](#8-데코레이터---공통-기능을-분리하는-포장지)
9. [타입 힌트 - 함수의 설명서](#9-타입-힌트---함수의-설명서)
10. [예외 처리와 종료 코드](#10-예외-처리와-종료-코드)
11. [원자적 교체 - 안전하게 파일 고치기](#11-원자적-교체---안전하게-파일-고치기)

---

## 1. 콘솔 프로그램이란?

마우스로 클릭하는 프로그램(GUI)과 달리, **글자(명령어)를 입력해서** 사용하는 프로그램입니다.

- 윈도우: `명령 프롬프트` 또는 `PowerShell`
- 맥: `터미널(Terminal)`

우리가 만들 가계부는 이렇게 사용합니다:

```
python -m budget_app add      ← "add 명령 실행해줘" 라는 뜻
python -m budget_app list     ← "목록 보여줘"
```

---

## 2. CLI와 명령어 파싱 (argparse)

**파싱(parsing)** = 사용자가 입력한 글자를 의미별로 쪼개서 이해하는 것.

```
python -m budget_app list --limit 3 --data-dir ./mydata
       └─모듈 이름┘   └명령┘ └──옵션──┘ └────옵션────┘
```

Python에는 **`argparse`**(표준 라이브러리)라는 도구가 있어서 이 쪼개기 작업을 대신 해줍니다.

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("command")                      # add, list 같은 명령어
parser.add_argument("--limit", type=int, default=10) # --limit 옵션 (기본값 10)
args = parser.parse_args()
print(args.command, args.limit)
```

- `--help` 옵션은 argparse가 **알아서 만들어줍니다** (요구사항 충족!)
- 요구사항에서 옵션 표기를 `--`(두 개)로 통일하라고 한 이유: 리눅스 세계의 표준 규칙이라서

---

## 3. dataclass - 데이터 담는 그릇

거래 내역 하나에는 여러 정보가 들어갑니다: id, 날짜, 타입, 카테고리, 금액...

이걸 그냥 변수 여러 개로 관리하면 헷갈립니다. **dataclass**는 "이런 정보를 담는 상자"를 선언하는 방법입니다.

```python
from dataclasses import dataclass

@dataclass
class Transaction:
    """거래 내역 하나를 담는 상자"""
    id: str            # 거래 고유 번호
    type: str          # income(수입) 또는 expense(지출)
    date: str          # YYYY-MM-DD 형식
    amount: int        # 양수만 허용
    category: str      # food, transport 등
    memo: str = ""     # 선택 사항 (없으면 빈 문자열)
    tags: list = None  # 선택 사항
```

- `@dataclass`를 붙이면 `__init__`(상자 초기화 코드)을 자동으로 만들어줌
- 요구사항: 데이터 모델은 dataclass 또는 그에 준하는 구조로 정의

---

## 4. 클래스와 모듈화 - 코드를 나눠서 정리하기

### 클래스(class)
**역할별로 묶은 함수+데이터 묶음**입니다. 비유하면:
- `TransactionRepository` = 가계부 본체 (내역 추가/찾기/수정/삭제 담당)
- `CategoryStore` = 카테고리 관리 담당자
- `BudgetStore` = 예산 관리 담당자

각각 자기 일만 맡아서 처리하면 코드가 깔끔해집니다.

> 요구사항: 최소 2개 이상의 클래스 사용

### 모듈(module) 분리
모듈 = **코드 파일 하나**. 한 파일에 다 몰아넣지 말고 역할별로 나누라는 뜻입니다.

```
budget_app/
├── __init__.py      ← 이 폴더가 파이썬 패키지임을 표시
├── __main__.py      ← python -m budget_app 으로 실행될 때 시작점
├── cli.py           ← 화면과 대화하는 부분 (입력받고 출력)
├── models.py        ← Transaction 같은 데이터 상자 정의
├── storage.py       ← 파일 읽고 쓰는 부분 (저장소 계층)
└── services.py      ← 실제 로직 (검색, 요약, 예산 판정 등)
```

계층(layer) 개념: 사용자와 마주보는 곳(CLI) → 판단하는 곳(Service) → 저장하는 곳(Storage) → 데이터 모양(Model).
**위에서 아래로만 호출**하면 나중에 고치기 쉬워집니다.

> 요구사항: 최소 3개 이상 모듈로 분리

---

## 5. 파일 입출력과 영구 저장

프로그램 변수는 프로그램을 끄면 사라집니다. 그래서 **파일에 저장**해야 합니다.

```python
# 쓰기
with open("data/transactions.jsonl", "a", encoding="utf-8") as f:
    f.write('{"id": "TX-000001", "amount": 15000}\n')

# 읽기
with open("data/transactions.jsonl", encoding="utf-8") as f:
    for line in f:          # 한 줄씩 읽기
        print(line.strip())
```

포인트:
- `"a"` 모드 = 덧붙여 쓰기(기존 내용 유지), `"w"` 모드 = 통째로 새로 쓰기
- `encoding="utf-8"` 필수 (한국어 깨짐 방지)

---

## 6. JSONL과 CSV - 저장 파일 형식

### JSONL (JSON Lines)
한 줄에 데이터 하나(JSON 형태). Python의 딕셔너리와 거의 1:1로 변환되어 편합니다.

```
{"id": "TX-000001", "type": "expense", "date": "2024-01-15", "amount": 15000}
{"id": "TX-000002", "type": "income", "date": "2024-01-14", "amount": 3000000}
```

```python
import json
obj = json.loads(line)          # 글자 → 파이썬 딕셔너리
text = json.dumps(obj, ensure_ascii=False)  # 딕셔너리 → 글자
```

### CSV
엑셀처럼 쉼표로 칸을 나눈 형식. import/export 스키마는 CSV로 고정되어 있습니다.

```python
import csv
with open("export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "type", "category", "amount", "memo", "tags"])  # 헤더
    writer.writerow(["2024-01-15", "expense", "food", 15000, "점심", "meal"])
```

> 저장은 JSONL 또는 CSV 중 **1개** 선택하면 되지만, import/export는 **CSV 스키마로 고정**입니다.
> (팁: 둘 다 CSV로 하면 변환 없이 import/export를 재활용할 수 있습니다.)

---

## 7. 제너레이터(yield)와 스트리밍 처리

**문제**: 파일에 내역이 100만 줄이 있으면, 전부 메모리에 올리면 오래 걸리고 메모리도 많이 먹습니다.

**해결**: **한 줄씩 흘려보내기**. 물을통째로 붓지 않고 수도꼭지처럼 조금씩 틀어주는 방식.

```python
def read_lines(path):
    """파일을 한 줄씩 순서대로 넘겨주는 제너레이터"""
    with open(path, encoding="utf-8") as f:
        for line in f:              # 파일 전체를 메모리에 올리지 않고
            yield line              # 한 줄씩 '흘려보낸다'
```

- 일반 함수는 `return`으로 값을 한 번에 돌려주지만,
- **`yield`**를 쓰면 값을 하나 넘기고 잠깐 멈췄다가, 다음 요청 때 이어서 실행됩니다.

```python
for tx in read_lines("data/transactions.jsonl"):
    if 조건(tx):
        print(tx)   # 필요한 만큼만 읽으니 빠르고 가볍다
```

> 요구사항: `list`, `search`는 제너레이터 기반 스트리밍 처리로 구현

---

## 8. 데코레이터 - 공통 기능을 분리하는 포장지

모든 명령에 "오류가 나면 예쁘게 알려줘" / "얼마나 걸렸는지 재줘" 같은 공통 기능을 붙이고 싶다면?
매번 코드를 복붙하지 않고, **함수를 감싸는 포장지(래퍼)**를 만듭니다.

```python
import time
from functools import wraps

def log_time(func):
    """함수 실행 시간을 측정해서 출력해주는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()               # 시작 시간 기록
        result = func(*args, **kwargs)    # 원래 함수 실행
        end = time.time()
        print(f"[로그] {func.__name__} 실행 시간: {end - start:.3f}초")
        return result                     # 원래 함수의 결과는 그대로 돌려줌
    return wrapper

@log_time                 # ← 이 한 줄이면 run_summary에 시간 측정이 자동 적용됨
def run_summary():
    ...
```

- `@log_time` 한 줄만 붙이면 됩니다. 원래 함수 코드는 건드리지 않음
- 요구사항: 예외 처리/로그/시간 측정 데코레이터 **1개 이상 구현 + 실제 적용**

---

## 9. 타입 힌트 - 함수의 설명서

타입 힌트 = "이 함수는 이런 타입을 받아서 이런 타입을 돌려준다"고 표시하는 것.

```python
def get_month_summary(month: str) -> dict:
    ...

def add_transaction(amount: int, category: str) -> Transaction:
    ...
```

- `month: str` = month는 글자여야 함, `-> dict` = 결과는 딕셔너리
- 실행할 때 강제력은 약하지만, **잘못된 사용을 미리 잡아주고**(에디터 경고), **읽는 사람이 바로 이해**됩니다
- 이게 "입출력 계약"입니다: 함수끼리 주고받는 약속을 코드에 명시

---

## 10. 예외 처리와 종료 코드

### try / except
예상되는 오류는 프로그램이 튕기지 않게 잡아줍니다.

```python
try:
    amount = int(user_input)          # "abc"가 들어오면 ValueError 발생
except ValueError:
    print("[오류] 금액은 숫자로 입력하세요.")
    print("[힌트] 예: 15000")
```

- 요구사항: **스택트레이스(빨간 에러 지뢰) 출력 금지**, 반드시 "원인 + 해결 힌트" 출력

### 종료 코드(exit code)
프로그램이 끝날 때 운영체제에 남기는 성적표입니다.

```python
import sys
sys.exit(0)   # 0 = 정상 종료
sys.exit(1)   # 0이 아니면 = 오류로 인한 종료
```

- 요구사항: 정상 종료 0, 오류 종료는 0이 아닌 값

---

## 11. 원자적 교체 - 안전하게 파일 고치기

update/delete는 파일 내용 일부를 고치는 작업입니다. 그런데 **쓰던 중에 프로그램이 꺼지면 파일이 망가질 수 있습니다.**

안전한 방법 (**임시 파일 + 교체**):

```python
import os, tempfile

def rewrite_file(path: str, lines: list[str]) -> None:
    """파일을 안전하게 다시 쓰는 함수 (원자적 교체)"""
    tmp_path = path + ".tmp"          # 1. 임시 파일에 완성본부터 작성
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    os.replace(tmp_path, path)        # 2. 완성됐으면 원본과 '순식간에' 교체
```

`os.replace`는 파일 시스템 수준에서 한 번에 교체되므로, 중간에 꺼져도 원본은 안전합니다.
(요구사항: update/delete는 "전체 재작성/임시 파일/원자적 교체(권장)" 등 안정성 고려)

---

## 한 줄 요약

| 개념 | 비전공자 버전 요약 |
|------|-------------------|
| CLI/argparse | 글자 명령을 받아서 쪼개주는 접수원 |
| dataclass | 데이터를 담는 정형화된 상자 |
| 클래스/모듈 | 역할별 담당자 + 파일별 정리함 |
| 파일 입출력 | 프로그램이 꺼져도 살아있는 노트 |
| JSONL/CSV | 한 줄에 한 건씩 / 엑셀식 표 |
| 제너레이터 | 물을 통째로 붓지 않고 조금씩 틀어주는 수도꼭지 |
| 데코레이터 | 함수에 기능을 덧씌우는 포장지 |
| 타입 힌트 | 함수 입출력의 설명서/약속 |
| 예외 처리 | 튕기지 말고 원인+힌트를 알려주기 |
| 원자적 교체 | 초안 완성 후 한 번에 갈아끼우기 |

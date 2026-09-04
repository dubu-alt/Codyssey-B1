# decorators.py - 여러 명령이 공통으로 쓰는 "포장지" 모음
#
# 데코레이터 = 함수를 감싸서 공통 기능을 자동으로 붙여주는 문법.
# 예를 들어 @measure_time 한 줄만 붙이면 그 함수의 실행 시간이 자동 기록된다.
# 매번 같은 코드를 복붙하지 않아도 되는 게 장점이다.

import time
from functools import wraps


def measure_time(func):
    """함수 실행 시간을 재어서 [로그]로 출력해주는 데코레이터.

    원리:
      1) 함수가 시작되기 전에 시간을 기록하고
      2) 원래 함수를 실행한 뒤
      3) 끝난 시각과 비교해서 얼마나 걸렸는지 출력한다.
    """

    @wraps(func)  # 원래 함수의 이름 등 정보를 유지해주는 도우미
    def wrapper(*args, **kwargs):
        start = time.time()               # (1) 시작 시간
        result = func(*args, **kwargs)    # (2) 진짜 함수 실행
        elapsed = time.time() - start     # (3) 걸린 시간 계산
        print(f"[로그] '{func.__name__}' 실행 시간: {elapsed:.3f}초")
        return result                     # 결과는 원래대로 돌려준다

    return wrapper


def safe_command(func):
    """명령 실행 중 오류가 나면 프로그램이 튕기지 않게 잡아주는 데코레이터.

    요구사항: 오류 메시지는 [오류] 원인 + [힌트] 해결 방법 형태로,
    스택트레이스(빨간 에러 지뢰)를 그대로 보여주면 안 된다.
    오류가 났을 때는 종료 코드로 1(비정상)을 돌려준다.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 정상 완료. result가 None이 아니면 그것이 종료 코드가 된다.
            return result if result is not None else 0
        except Exception as error:  # 어떤 오류이든 여기서 잡는다
            # str(error): 오류의 한 줄 설명
            print(f"[오류] {str(error)}")
            print("[힌트] --help 옵션으로 사용법을 확인할 수 있습니다.")
            return 1  # 0이 아닌 값 = 오류로 인한 종료

    return wrapper

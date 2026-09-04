# main.py - Mini Redis 실행 시작점 (CLI / REPL)
#
# [REPL] Read(읽기) -> Eval(실행) -> Print(출력) -> Loop(반복)
#        mini-redis> 프롬프트에 명령을 입력하면 바로 결과를 보여준다.
#        exit 또는 quit 으로 종료한다.
#
# ※ 제약 준수: 명령 분기도 if/elif로 처리한다 (dict 사용 금지).

import sys

from .store import OOMError, RedisStore


def split_args(line: str) -> list:
    """입력 줄을 명령 인자들로 쪼갠다.

    규칙:
      - 공백으로 구분
      - 큰따옴표로 감싼 부분은 공백이 있어도 하나의 값으로 본다
        예: SET greeting "hello world" -> ["SET", "greeting", "hello world"]
    """
    tokens = []
    current = ""       # 지금 만들고 있는 조각
    in_quotes = False  # 따옴표 안인지 표시
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes   # 따옴표 열고/닫기 전환
        elif ch == " " and not in_quotes:
            if current:                 # 공백을 만나면 조각 완성
                tokens.append(current)
                current = ""
        else:
            current += ch               # 글자를 조각에 붙임
    if current:                         # 마지막 조각 처리
        tokens.append(current)
    return tokens


def format_output(result) -> str:
    """저장소의 반환값을 Redis 스타일 화면 출력으로 바꾼다.

      None     -> (nil)
      True     -> (integer) 1
      False    -> (integer) 0
      숫자     -> (integer) N
      리스트   -> 한 줄씩 번호 매겨 출력
      문자열   -> "문자열" 형태 그대로
    """
    if result is None:
        return "(nil)"
    if isinstance(result, bool):
        return f"(integer) {1 if result else 0}"
    if isinstance(result, int):
        return f"(integer) {result}"
    if isinstance(result, list):
        if not result:
            return "(empty array)"
        lines = []
        for i, item in enumerate(result, start=1):
            if isinstance(item, str) and not item.startswith(("used_memory", "maxmemory", "evicted_keys")):
                # KEYS 처럼 키 목록일 때는 번호 + 따옴표 형식
                lines.append(f'{i}. "{item}"')
            else:
                lines.append(str(item))
        return "\n".join(lines)
    return str(result)


def execute(store: RedisStore, line: str) -> str:
    """입력 한 줄을 해석해서 실행하고 출력 문자열을 돌려준다."""
    tokens = split_args(line)
    if not tokens:
        return ""                            # 빈 입력이면 아무것도 안 함

    cmd = tokens[0].upper()                  # 대소문자 구분 없음
    args = tokens[1:]

    # ---------- String 기본 명령어 ----------
    if cmd == "SET":
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'SET' command"
        return store.set_key(args[0], args[1])

    elif cmd == "GET":
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'GET' command"
        value = store.get_key(args[0])
        return "(nil)" if value is None else f'"{value}"'

    elif cmd == "DEL":
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'DEL' command"
        return format_output(store.delete_key(args[0]))

    elif cmd == "EXISTS":
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'EXISTS' command"
        return format_output(store.exists_key(args[0]))

    elif cmd == "DBSIZE":
        if args:
            return "(error) ERR wrong number of arguments for 'DBSIZE' command"
        return format_output(store.dbsize())

    elif cmd == "KEYS":
        if args:
            return "(error) ERR wrong number of arguments for 'KEYS' command"
        return format_output(store.all_keys())

    # ---------- 메모리 관리 명령어 ----------
    elif cmd == "CONFIG":
        # 형식: CONFIG SET maxmemory <bytes>
        if len(args) == 3 and args[0].upper() == "SET" and args[1].lower() == "maxmemory":
            try:
                max_bytes = int(args[2])          # 정수 파싱 시도
                if max_bytes < 0:
                    raise ValueError              # 음수는 안 됨
            except ValueError:
                return "(error) ERR value is not an integer or out of range"
            return store.config_set_maxmemory(max_bytes)
        return "(error) ERR unknown command 'CONFIG'" if not args \
            else "(error) ERR wrong number of arguments for 'CONFIG' command"

    elif cmd == "INFO":
        if len(args) != 1 or args[0].lower() != "memory":
            return "(error) ERR wrong number of arguments for 'INFO' command"
        return "\n".join(store.info_memory())

    # ---------- TTL 관리 명령어 ----------
    elif cmd == "EXPIRE":
        if len(args) != 2:
            return "(error) ERR wrong number of arguments for 'EXPIRE' command"
        try:
            seconds = int(args[1])
        except ValueError:
            return "(error) ERR value is not an integer or out of range"
        return format_output(store.expire_key(args[0], seconds))

    elif cmd == "TTL":
        if len(args) != 1:
            return "(error) ERR wrong number of arguments for 'TTL' command"
        return format_output(store.ttl_of_key(args[0]))

    # ---------- 알 수 없는 명령 ----------
    else:
        return f"(error) ERR unknown command '{tokens[0]}'"


def repl() -> None:
    """REPL 반복문. 프로그램의 심장부."""
    store = RedisStore()
    print("Mini Redis 시작! (종료: exit 또는 quit)")
    while True:
        try:
            line = input("mini-redis> ")      # Read: 한 줄 입력받기
        except EOFError:                      # Ctrl+D 로 끝낸 경우
            print()
            break
        stripped = line.strip()
        if stripped.lower() in ("exit", "quit"):
            break                             # 종료 명령
        if not stripped:
            continue                          # 빈 줄은 무시
        try:
            output = execute(store, stripped)  # Eval: 실행
        except OOMError as error:             # 메모리 초과는 특별 표시
            output = f"(error) {str(error)}"
        if output:
            print(output)                     # Print: 결과 출력
                                             # Loop: while 문이 반복


if __name__ == "__main__":
    try:
        repl()
    except KeyboardInterrupt:
        print()
        sys.exit(130)                         # Ctrl+C 종료 코드
    sys.exit(0)

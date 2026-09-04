# main.py - Mini Git 실행 시작점 (CLI / REPL)
#
# [REPL] mini-git> 프롬프트에서 명령을 반복 입력받는 대화 구조.
#        exit 또는 quit 으로 종료한다.
#
# 명령 처리 흐름: 입력 한 줄 -> 파싱(쪼개기) -> 실행 -> 출력

import sys

from .algorithms import bfs_shortest_path, find_ancestors, merge_sort, topo_order
from .graph import MiniGitRepository
from .index import InvertedIndex


def split_args(line: str) -> list:
    """입력 줄을 인자들로 쪼갠다.

    - 공백으로 구분한다
    - 큰따옴표로 감싼 부분은 공백이 있어도 하나의 인자다
      예: COMMIT "Add login feature" -> ["COMMIT", "Add login feature"]
    """
    tokens = []
    current = ""
    in_quotes = False
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes      # 따옴표 열고/닫기
        elif ch == " " and not in_quotes:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += ch
    if current:
        tokens.append(current)
    return tokens


class CommandRunner:
    """명령 해석 + 실행을 맡는 클래스. 저장소와 역색인을 함께 가진다."""

    def __init__(self):
        self.repo = MiniGitRepository()    # 커밋 그래프/브랜치 상태
        self.index = InvertedIndex()       # 빠른 검색용 색인

    # ---------------- 파싱 도우미 ----------------

    @staticmethod
    def _find_option(tokens: list, name: str):
        """--이름=값 형태의 옵션 값을 찾아 돌려준다. 없으면 None.

        예: ["LOG", "--sort-by=date"] 에서 name="sort-by" -> "date"
        """
        for token in tokens:
            if token.startswith(f"--{name}="):
                return token.split("=", 1)[1]
        return None

    def neighbors_of(self, commit):
        """무방향 이웃 = 부모들 + 자식들. (PATH 최단 경로에서 사용)"""
        result = list(commit.parents)
        result.extend(self._children.get(commit.hash, []))
        return result

    # ---------------- 명령 실행 ----------------

    def execute(self, line: str) -> str:
        """입력 한 줄을 실행하고 결과 문자열을 돌려준다."""
        tokens = split_args(line)
        if not tokens:
            return ""
        cmd = tokens[0].upper()            # 대소문자 구분 없음
        args = tokens[1:]

        if cmd == "INIT":
            author = args[0] if args else "unknown"
            return self.repo.init(author)

        elif cmd == "BRANCH":
            if len(args) != 1:
                raise ValueError("Invalid args: BRANCH <브랜치명>")
            return self.repo.branch(args[0])

        elif cmd == "SWITCH":
            if len(args) != 1:
                raise ValueError("Invalid args: SWITCH <브랜치명>")
            return self.repo.switch(args[0])

        elif cmd == "COMMIT":
            message = " ".join(args).strip()   # 따옴표 벗겨진 인자들을 합친다
            result = self.repo.commit(message)
            # 새 커밋을 역색인에도 등록한다 (요구사항)
            new_commit = self.repo.commits[self.repo.branches[self.repo.head]]
            self.index.add_commit(new_commit)
            return result

        elif cmd == "LOG":
            return self.cmd_log(args)

        elif cmd == "PATH":
            if len(args) != 2:
                raise ValueError("Invalid args: PATH <commit1> <commit2>")
            return self.cmd_path(args[0], args[1])

        elif cmd == "ANCESTORS":
            if len(args) != 1:
                raise ValueError("Invalid args: ANCESTORS <commit_hash>")
            return self.cmd_ancestors(args[0])

        elif cmd == "SEARCH":
            return self.cmd_search(args)

        elif cmd in ("EXIT", "QUIT"):
            return "__EXIT__"                  # REPL에 종료 신호 전달

        else:
            return f"(error) Unknown command: {cmd}"

    # ---------------- 각 명령의 실제 일 ----------------

    def cmd_log(self, args: list) -> str:
        """LOG / LOG --sort-by=date|author."""
        sort_by = self._find_option(args, "sort-by")
        commits = self.repo.all_commits()

        if sort_by is None:
            # 기본 LOG: 부모가 항상 자식보다 먼저 나오는 순서(위상 정렬 성격)
            ordered = topo_order(commits)
        elif sort_by in ("date", "author"):
            # 직접 만든 병합 정렬로 기준별 정렬
            if sort_by == "date":
                key_compare = lambda a, b: (a.timestamp > b.timestamp) - (a.timestamp < b.timestamp)
                ordered = merge_sort(commits, key_compare)
            else:
                key_compare = lambda a, b: (a.author > b.author) - (a.author < b.author)
                ordered = merge_sort(commits, key_compare)
        else:
            raise ValueError(f"Invalid args: unknown --sort-by '{sort_by}'")

        lines = []
        branch_tips = {}                       # {hash: [브랜치명...]} 미리 계산
        for commit in ordered:
            names = self.repo.branch_names_pointing_to(commit.hash)
            if names:
                branch_tips[commit.hash] = names
        for commit in ordered:
            tags = ""
            if commit.hash in branch_tips:
                tags = " [" + ", ".join(branch_tips[commit.hash]) + "]"
            lines.append(f"commit {commit.hash} "
                         f"({commit.author}, {commit.time_string()}){tags}")
            lines.append(commit.message)
            lines.append("")                   # 커밋 사이 빈 줄
        return "\n".join(lines).rstrip()

    def cmd_path(self, hash1: str, hash2: str) -> str:
        """PATH 명령. 두 커밋 사이 무방향 최단 경로."""
        start = self.repo.get_commit(hash1)    # 없는 hash면 오류 메시지
        target = self.repo.get_commit(hash2)
        self._children = self.repo.children_map()  # 자식 방향 지도 준비
        path = bfs_shortest_path(start, target, self.neighbors_of)
        if path is None:
            return "No path"
        hashes = [c.hash for c in path]        # hash1->hash2->... 문자열로 표현
        return "Path: " + " -> ".join(hashes)

    def cmd_ancestors(self, commit_hash: str) -> str:
        """ANCESTORS 명령. 도달 가능한 모든 조상 출력."""
        start = self.repo.get_commit(commit_hash)
        ancestors = find_ancestors(start)
        if not ancestors:
            return "(no ancestors)"
        lines = []
        for commit in ancestors:
            lines.append(f"- {commit.hash}: {commit.message} ({commit.time_string()})")
        return "\n".join(lines)

    def cmd_search(self, args: list) -> str:
        """SEARCH <키워드> 또는 SEARCH --author=<이름>. 둘 다 역색인 사용."""
        author = self._find_option(args, "author")
        if author is not None:
            hashes = self.index.search_author(author)
        else:
            if not args:
                raise ValueError('Invalid args: SEARCH <키워드> 또는 SEARCH --author=<이름>')
            keyword = args[0]
            hashes = self.index.search_keyword(keyword)

        if not hashes:
            return "(no results)"

        # hash 순서대로 보여주기 위해 직접 만든 정렬 사용
        commits = [self.repo.commits[h] for h in hashes]
        ordered = merge_sort(commits,
                             lambda a, b: (a.hash > b.hash) - (a.hash < b.hash))
        lines = [f"Found {len(ordered)} commit(s):", ""]
        for commit in ordered:
            lines.append(f"- {commit.hash}: {commit.message} ({commit.author})")
        return "\n".join(lines)


def repl() -> None:
    """REPL 반복문."""
    runner = CommandRunner()
    print("Mini Git 시작! (종료: exit 또는 quit)")
    while True:
        try:
            line = input("mini-git> ")
        except EOFError:
            print()
            break
        if not line.strip():
            continue
        try:
            output = runner.execute(line)
        except ValueError as error:            # 표준 오류 메시지 처리
            print(f"(error) {str(error)}")
            continue
        if output == "__EXIT__":
            break
        if output:
            print(output)


if __name__ == "__main__":
    try:
        repl()
    except KeyboardInterrupt:
        print()
        sys.exit(130)
    sys.exit(0)

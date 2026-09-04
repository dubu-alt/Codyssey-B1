# graph.py - 커밋 그래프 (Mini Git의 핵심 자료구조)
#
# [개념] 커밋 = "누가, 언제, 무슨 이유로" 저장했다는 기록 한 건.
#       각 커밋은 부모 커밋(과거)을 가리킨다. 이 화살표들이 모이면 그래프가 된다.
#       부모는 항상 이미 존재하는 과거 커밋뿐이라 루프(사이클)가 생길 수 없다.
#       이런 구조를 DAG(방향성 비순환 그래프)라고 부른다.
#
# [브랜치와 HEAD]
#   브랜치 = 어떤 커밋을 가리키는 이름표
#   HEAD   = "내가 지금 서 있는 브랜치" 표시
#
# dict 사용은 허용된다 (기본 자료형). 정렬 API만 금지!

import hashlib
import time


class Commit:
    """커밋 노드. 요구사항의 최소 필드를 모두 가진다."""

    def __init__(self, commit_hash: str, message: str,
                 author: str, timestamp: float, parents: list):
        self.hash = commit_hash          # 세션 내 유일한 식별자
        self.message = message           # 커밋 메시지
        self.author = author             # 작성자
        self.timestamp = timestamp       # 만든 시각(초 단위 숫자)
        self.parents = parents           # 부모 Commit 객체 목록 (0개 이상)

    def time_string(self) -> str:
        """timestamp 숫자를 사람이 읽는 날짜 글자로 바꿔준다."""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))


class MiniGitRepository:
    """저장소 전체 상태를 관리하는 클래스.

    commits  : {hash: Commit} - hash로 빠르게 찾기 위한 해시맵(dict)
    branches : {브랜치명: hash} - 각 브랜치가 가리키는 커밋
    head     : 현재 체크아웃된 브랜치 이름
    user     : 현재 사용자(author)
    """

    def __init__(self):
        self.commits = {}      # hash -> Commit
        self.branches = {}     # 브랜치명 -> hash (커밋이 없으면 None)
        self.head = None       # 현재 브랜치 이름
        self.user = ""         # 현재 author
        self.initialized = False
        self._counter = 0      # hash 만들 때 쓰는 증가 번호 (유일성 보장용)

    # ------------------------------------------------------------------
    # 명령어 구현
    # ------------------------------------------------------------------

    def init(self, author: str) -> str:
        """INIT 명령. 저장소를 새로 만들고 main 브랜치와 사용자를 설정한다."""
        if self.initialized:
            raise ValueError("Invalid args: repository is already initialized")
        self.commits = {}
        self.branches = {"main": None}   # 아직 커밋이 없으니 None을 가리킴
        self.head = "main"
        self.user = author
        self.initialized = True
        return ("Initialized repository.\n"
                f"Current branch: {self.head}\n"
                f"Current user: {self.user}")

    def _require_init(self) -> None:
        """초기화가 안 됐으면 공통 오류를 발생시킨다."""
        if not self.initialized:
            raise ValueError("Invalid args: run 'init' first")

    def current_head_commit(self):
        """HEAD 브랜치가 가리키는 커밋 객체. 아직 커밋이 없으면 None."""
        target_hash = self.branches[self.head]
        return self.commits.get(target_hash) if target_hash else None

    def new_hash(self) -> str:
        """세션 내에서 절대 겹치지 않는 짧은 해시를 만든다.

        방법: 매번 1씩 늘어나는 번호를 섞어서 SHA-1로 만든 뒤 앞 7글자만 사용.
        번호가 계속 달라지므로 입력이 절대 중복되지 않고 -> 해시도 안 겹친다.
        """
        while True:
            self._counter += 1
            raw = f"{self._counter}-{time.time()}"
            candidate = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:7]
            if candidate not in self.commits:   # 혹시 몰라 중복 검사까지
                return candidate

    def commit(self, message: str) -> str:
        """COMMIT 명령. 현재 HEAD를 부모로 하는 새 커밋을 만든다."""
        self._require_init()
        if not message:
            raise ValueError('Invalid args: COMMIT "메시지" 형식으로 입력하세요')
        parent = self.current_head_commit()
        parents = [parent] if parent else []    # 첫 커밋은 부모가 없다 (root)
        commit = Commit(self.new_hash(), message, self.user,
                        time.time(), parents)
        self.commits[commit.hash] = commit
        self.branches[self.head] = commit.hash  # 현재 브랜치가 새 커밋을 가리킴
        return f"[{self.head} {commit.hash}] {message}"

    def branch(self, name: str) -> str:
        """BRANCH 명령. 현재 HEAD 커밋을 함께 가리키는 새 이름표를 만든다."""
        self._require_init()
        if not name or " " in name:
            raise ValueError(f"Invalid args: bad branch name '{name}'")
        if name in self.branches:
            raise ValueError(f"Invalid args: branch already exists: {name}")
        # 복사가 아니라 같은 커밋을 함께 가리키는 것!
        self.branches[name] = self.branches[self.head]
        return f"Created branch: {name}"

    def switch(self, name: str) -> str:
        """SWITCH 명령. HEAD를 다른 브랜치로 옮긴다."""
        self._require_init()
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")
        self.head = name                        # 위치 표시판만 바꾸면 끝
        return f"Switched to branch: {name}"

    def get_commit(self, commit_hash: str) -> Commit:
        """hash로 커밋을 찾는다. 없으면 표준 오류 메시지로 예외 발생."""
        commit = self.commits.get(commit_hash)
        if commit is None:
            raise ValueError(f"Unknown commit: {commit_hash}")
        return commit

    def all_commits(self) -> list:
        """저장된 모든 커밋 목록."""
        return list(self.commits.values())

    def children_map(self) -> dict:
        """{커밋 hash: [자식 Commit 목록]} 지도를 만든다.

        PATH 명령에서 커밋-부모 연결을 '무방향'(양방향)으로 탐색하려면
        자식 방향 정보도 필요해서 미리 계산해 둔다.
        """
        children = {}
        for commit in self.commits.values():
            for parent in commit.parents:
                children.setdefault(parent.hash, []).append(commit)
        return children

    def branch_names_pointing_to(self, commit_hash: str) -> list:
        """이 커밋을 가리키는 브랜치 이름들. LOG에서 [main] 표시에 쓴다."""
        names = []
        for branch_name, target in self.branches.items():
            if target == commit_hash:
                names.append(branch_name)
        return names

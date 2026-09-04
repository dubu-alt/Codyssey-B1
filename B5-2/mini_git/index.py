# index.py - 역색인 (Inverted Index)
#
# [개념] 책 맨 뒤의 "색인 페이지"를 떠올려보자.
#   일반 검색: 커밋을 하나씩 다 읽으며 찾기 -> 데이터가 많으면 느림 O(n)
#   역색인:    미리 "단어 -> 그 단어가 나온 커밋 목록" 장부를 만들어두고
#              검색 때는 장부만 펼쳐보기 -> 즉답
#
# 두 가지 인덱스를 유지한다 (요구사항):
#   keyword_index : {키워드: [커밋 hash, ...]}
#   author_index  : {작성자: [커밋 hash, ...]}
#
# 키워드 규칙(요구사항): 메시지를 공백으로 자르고(split) 전부 소문자(lower)로.


class InvertedIndex:
    """커밋 검색을 빠르게 해주는 색인 장부."""

    def __init__(self):
        self.keyword_index = {}   # {키워드: [hash, ...]}
        self.author_index = {}    # {작성자명: [hash, ...]}

    def add_commit(self, commit) -> None:
        """새 커밋이 생길 때마다 인덱스를 갱신한다. (COMMIT 명령에서 호출)"""
        # --- 키워드 인덱스 갱신 ---
        tokens = commit.message.lower().split()   # 공백 분리 + 소문자화
        for token in tokens:
            bucket = self.keyword_index.setdefault(token, [])
            if commit.hash not in bucket:         # 같은 단어가 메시지에
                bucket.append(commit.hash)        # 두 번 나와도 한 번만 기록

        # --- 작성자 인덱스 갱신 ---
        author = commit.author.lower()
        bucket = self.author_index.setdefault(author, [])
        if commit.hash not in bucket:
            bucket.append(commit.hash)

    def search_keyword(self, keyword: str) -> list:
        """메시지에 해당 키워드(토큰)가 있는 커밋의 hash 목록."""
        return list(self.keyword_index.get(keyword.lower(), []))

    def search_author(self, author: str) -> list:
        """해당 작성자의 커밋 hash 목록."""
        return list(self.author_index.get(author.lower(), []))

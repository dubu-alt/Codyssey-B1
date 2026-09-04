-- ============================================================
-- 핵심 SQL 쿼리 모음
-- 실행 전 01_schema.sql, 02_sample_data.sql을 먼저 실행할 것
-- 각 쿼리 실행 후 결과를 스크린샷 또는 텍스트로 캡처하여
-- 별도 폴더(execution_results)에 저장할 것
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- [기본 조회] 5개 - WHERE, ORDER BY, LIMIT, LIKE 포함
-- ============================================================

-- Q1. 조회수 10만 이상인 릴스 조회
-- 확인 목적: 인기 릴스(조회수 기준)를 걸러낸다
SELECT reel_id, caption, view_count
FROM reels
WHERE view_count >= 100000;

-- Q2. 전체 릴스를 조회수 내림차순으로 정렬
-- 확인 목적: 조회수가 높은 순서로 릴스를 나열한다
SELECT reel_id, caption, view_count
FROM reels
ORDER BY view_count DESC;

-- Q3. 가장 최근에 업로드된 릴스 5개 조회
-- 확인 목적: 최신 업로드 릴스를 확인한다
SELECT reel_id, caption, upload_date
FROM reels
ORDER BY upload_date DESC
LIMIT 5;

-- Q4. 캡션에 'daily'가 포함된 릴스 검색
-- 확인 목적: 특정 키워드로 릴스를 검색한다
SELECT reel_id, caption
FROM reels
WHERE caption LIKE '%daily%';

-- Q5. 해시태그에 'daily' 태그가 포함된 릴스 검색
-- 확인 목적: hashtags 컬럼(쉼표로 구분된 텍스트)에서도 LIKE로 태그 검색이
--           가능함을 보여준다. 별도의 hashtags 테이블 없이도 태그 검색 자체는 된다.
SELECT reel_id, caption, hashtags
FROM reels
WHERE hashtags LIKE '%daily%';

-- ============================================================
-- [조인] 4개 - INNER JOIN 2개 이상, LEFT JOIN 1개 이상
-- ============================================================

-- Q6. 릴스와 업로더(사용자) 정보를 함께 조회 (INNER JOIN)
-- 확인 목적: 각 릴스를 누가 올렸는지 확인한다
SELECT r.reel_id, r.caption, u.username
FROM reels r
INNER JOIN users u ON r.user_id = u.user_id;

-- Q7. 댓글, 작성자, 대상 릴스를 함께 조회 (INNER JOIN 2회)
-- 확인 목적: 어떤 사용자가 어떤 릴스에 어떤 댓글을 달았는지 확인한다
SELECT c.comment_id, u.username AS commenter, r.caption, c.content
FROM comments c
INNER JOIN users u ON c.user_id = u.user_id
INNER JOIN reels r ON c.reel_id = r.reel_id;

-- Q8. 댓글이 하나도 없는 릴스 찾기 (LEFT JOIN)
-- 확인 목적: 댓글 반응이 없는 릴스를 파악한다
SELECT r.reel_id, r.caption
FROM reels r
LEFT JOIN comments c ON r.reel_id = c.reel_id
WHERE c.comment_id IS NULL;

-- Q9. 릴스에 좋아요를 누른 사용자 목록 조회 (INNER JOIN 2회)
-- 확인 목적: 어떤 사용자가 어떤 릴스에 좋아요를 눌렀는지 확인한다
SELECT r.reel_id, r.caption, u.username AS liked_by
FROM likes l
INNER JOIN users u ON l.user_id = u.user_id
INNER JOIN reels r ON l.reel_id = r.reel_id
ORDER BY r.reel_id;

-- ============================================================
-- [집계] 3개 - COUNT/SUM/AVG 중 2개 이상 + GROUP BY
-- ============================================================

-- Q10. 사용자별 업로드한 릴스 수와 총 조회수 (COUNT, SUM)
-- 확인 목적: 어떤 사용자가 릴스를 많이 올리고 조회수를 많이 받았는지 확인한다
SELECT u.username,
       COUNT(r.reel_id) AS reel_count,
       SUM(r.view_count) AS total_views
FROM users u
INNER JOIN reels r ON u.user_id = r.user_id
GROUP BY u.username
ORDER BY total_views DESC;

-- Q11. 릴스별 좋아요 개수 집계 (COUNT)
-- 확인 목적: 어떤 릴스가 좋아요를 가장 많이 받았는지 확인한다
SELECT r.reel_id, r.caption, COUNT(l.like_id) AS like_count
FROM reels r
LEFT JOIN likes l ON r.reel_id = l.reel_id
GROUP BY r.reel_id, r.caption
ORDER BY like_count DESC;

-- Q12. 사용자가 올린 릴스들의 평균 조회수 (AVG)
-- 확인 목적: 사용자별 평균 조회수 성과를 비교한다
SELECT u.username, AVG(r.view_count) AS avg_views
FROM users u
INNER JOIN reels r ON u.user_id = r.user_id
GROUP BY u.username
ORDER BY avg_views DESC;

-- ============================================================
-- [서브쿼리] 2개
-- ============================================================

-- Q13. 전체 릴스 평균 조회수보다 조회수가 높은 릴스 조회 (서브쿼리)
-- 확인 목적: 평균 이상의 성과를 낸 릴스를 걸러낸다
SELECT reel_id, caption, view_count
FROM reels
WHERE view_count > (SELECT AVG(view_count) FROM reels)
ORDER BY view_count DESC;

-- Q14. 댓글을 한 번도 작성하지 않은 사용자 조회 (서브쿼리)
-- 확인 목적: 댓글 활동이 없는 사용자를 파악한다
SELECT username
FROM users
WHERE user_id NOT IN (SELECT DISTINCT user_id FROM comments);

-- ============================================================
-- [데이터 수정 및 삭제] 2개
-- ============================================================

-- Q15. 특정 릴스(reel_id = 3)의 조회수를 5000 증가시키기 (UPDATE)
-- 확인 목적: 조회수 증가 처리가 정상 반영되는지 확인한다
UPDATE reels
SET view_count = view_count + 5000
WHERE reel_id = 3;

-- Q16. 특정 좋아요 취소 처리 (DELETE)
-- 확인 목적: 좋아요 취소 시 해당 레코드가 삭제되는지 확인한다
DELETE FROM likes
WHERE user_id = 9 AND reel_id = 2;

-- ============================================================
-- [인덱스] 1개
-- ============================================================

-- Q17. reels.user_id 컬럼에 인덱스 생성
-- 적용 이유: "사용자별 릴스 조회(WHERE user_id = ?)"와 users-reels JOIN 조건이
--           매우 빈번하게 사용되므로, 이 컬럼에 인덱스를 걸어 조회 속도를 높인다
CREATE INDEX idx_reels_user_id ON reels(user_id);

-- ============================================================
-- [무결성 검증] FK 제약조건이 없는 값 참조를 실제로 막는지 확인
-- ============================================================

-- 검증 1. 존재하지 않는 user_id(999)를 참조하는 릴스를 강제로 삽입 시도
-- 아래 INSERT는 의도적으로 실패해야 하는 검증용 쿼리이다.
-- users 테이블에 user_id = 999인 사용자가 없기 때문에
-- reels.user_id -> users.user_id FK 제약조건에 걸려 삽입이 거부된다.
INSERT INTO reels (reel_id, user_id, caption, video_url, duration_seconds, view_count, upload_date, hashtags)
VALUES (99, 999, '무결성 테스트용 릴스', 'https://reels.example.com/fake', 10, 0, '2026-07-14', 'test');

-- 실제 실행 결과 (SQLite):
--   sqlite3.IntegrityError: FOREIGN KEY constraint failed
--
-- 왜 막히는가:
--   PRAGMA foreign_keys = ON 상태에서, reels.user_id는 users.user_id를
--   참조하는 FK로 선언되어 있다. FK는 "자식 테이블의 값은 반드시
--   부모 테이블에 실제로 존재하는 값이어야 한다"는 규칙을 강제한다.
--   user_id = 999는 users 테이블에 존재하지 않으므로 참조 무결성이
--   깨지는 것을 DB 엔진이 자동으로 차단한다.

-- 검증 2. 존재하지 않는 reel_id(999)를 참조하는 댓글을 강제로 삽입 시도
-- likes/comments 두 테이블 모두 reels를 참조하는 FK가 걸려 있음을 함께 확인한다.
INSERT INTO comments (user_id, reel_id, content)
VALUES (1, 999, '무결성 테스트용 댓글');

-- 실제 실행 결과 (SQLite):
--   sqlite3.IntegrityError: FOREIGN KEY constraint failed
--   (comments.reel_id -> reels.reel_id FK가 존재하지 않는 reel_id=999 삽입을 차단)

-- 검증 3. 실제 존재하는 값으로 바꾸면 정상적으로 삽입되는 것도 함께 확인 (대조군)
INSERT INTO reels (reel_id, user_id, caption, video_url, duration_seconds, view_count, upload_date, hashtags)
VALUES (99, 4, '무결성 테스트용 릴스', 'https://reels.example.com/fake', 10, 0, '2026-07-14', 'test');
-- user_id = 4는 users 테이블에 실제로 존재하므로 정상 삽입된다.
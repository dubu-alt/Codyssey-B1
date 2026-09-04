/* ============================================================
- 실행 환경: SQLite
- 실행 순서: 01_schema.sql -> 02_sample_data.sql -> 03_queries.sql

- 테이블 4개로 단순화한 버전입니다.
  (원래는 hashtags, reel_hashtags를 별도 테이블로 뒀지만,
   여기서는 reels 테이블 안에 hashtags라는 TEXT 컬럼 하나를 추가해
   '#travel,#daily' 처럼 쉼표로 구분된 문자열로 저장합니다.

각 테이블 간 관계
users -> reels     (1:N)  사용자 1명이 릴스 여러 개 업로드
users -> likes     (1:N)  사용자 1명이 좋아요 여러 개
reels -> likes     (1:N)  릴스 1개에 좋아요 여러 개
users -> comments  (1:N)  사용자 1명이 댓글 여러 개
reels -> comments  (1:N)  릴스 1개에 댓글 여러 개
============================================================ */

-- SQLite 전용 문법: FK 무결성은 기본값이 OFF이므로 반드시 켜야 함
PRAGMA foreign_keys = ON;

-- 재실행 대비 기존 테이블 정리 (자식 테이블부터 삭제)
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS reels;
DROP TABLE IF EXISTS users;

-- ------------------------------------------------------------
-- 1. users : 사용자 정보
-- ------------------------------------------------------------
CREATE TABLE users (
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,           -- 중복 불가
    email       TEXT NOT NULL UNIQUE,           -- 중복 불가
    full_name   TEXT,
    created_at  DATE NOT NULL DEFAULT (date('now'))  -- SQLite 전용: date('now')
);

-- ------------------------------------------------------------
-- 2. reels : 릴스(영상) 정보
--    1:N 관계 -> reels.user_id -> users.user_id (사용자 1명이 여러 릴스 업로드)
--    hashtags : 원래 별도 테이블(hashtags, reel_hashtags)로 관리하던 태그를
--               쉼표로 구분된 텍스트 한 컬럼에 저장 (예: 'travel,daily')
-- ------------------------------------------------------------
CREATE TABLE reels (
    reel_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    caption           TEXT,
    video_url         TEXT NOT NULL,
    duration_seconds  INTEGER NOT NULL,
    view_count        INTEGER NOT NULL DEFAULT 0,
    upload_date       DATE NOT NULL,
    hashtags          TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ------------------------------------------------------------
-- 3. likes : 좋아요 기록
--    1:N 관계 -> likes.user_id -> users.user_id
--    1:N 관계 -> likes.reel_id -> reels.reel_id
--    동일 사용자가 동일 릴스에 중복 좋아요 방지 위해 UNIQUE 복합키 적용
-- ------------------------------------------------------------
CREATE TABLE likes (
    like_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    reel_id     INTEGER NOT NULL,
    liked_at    DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (reel_id) REFERENCES reels(reel_id),
    UNIQUE (user_id, reel_id)
);

-- ------------------------------------------------------------
-- 4. comments : 댓글
--    1:N 관계 -> comments.user_id -> users.user_id
--    1:N 관계 -> comments.reel_id -> reels.reel_id
-- ------------------------------------------------------------
CREATE TABLE comments (
    comment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    reel_id        INTEGER NOT NULL,
    content        TEXT NOT NULL,
    commented_at   DATETIME NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (reel_id) REFERENCES reels(reel_id)
);
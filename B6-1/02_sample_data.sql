-- ============================================================
-- 샘플 데이터 입력
-- 실행 전 반드시 01_schema.sql을 먼저 실행할 것
-- 입력 순서: users -> reels -> likes -> comments
--           (FK가 참조하는 부모 테이블이 먼저 채워져야 함)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- 1. users (12행)
-- ------------------------------------------------------------
INSERT INTO users (user_id, username, email, full_name, created_at) VALUES
(1,  'traveler_ji',    'traveler_ji@example.com',    '지수민', '2025-11-02'),
(2,  'foodie_hoon',    'foodie_hoon@example.com',    '박준훈', '2025-11-10'),
(3,  'dance_yuna',     'dance_yuna@example.com',     '김유나', '2025-12-01'),
(4,  'daily_minji',    'daily_minji@example.com',    '이민지', '2025-12-15'),
(5,  'gamer_seok',     'gamer_seok@example.com',     '최석진', '2026-01-05'),
(6,  'pet_lover_haru', 'pet_lover_haru@example.com', '정하루', '2026-01-20'),
(7,  'fitness_woo',    'fitness_woo@example.com',    '우진혁', '2026-02-03'),
(8,  'artsy_nari',     'artsy_nari@example.com',     '한나리', '2026-02-18'),
(9,  'music_taeho',    'music_taeho@example.com',    '강태호', '2026-03-01'),
(10, 'beauty_soyeon',  'beauty_soyeon@example.com',  '오소연', '2026-03-20'),
(11, 'book_junho',     'book_junho@example.com',     '배준호', '2026-04-10'),
(12, 'coding_areum',   'coding_areum@example.com',   '신아름', '2026-04-25');

-- ------------------------------------------------------------
-- 2. reels (15행)
--    hashtags 컬럼: 기존 reel_hashtags 연결 내역을 쉼표 구분 문자열로 변환
-- ------------------------------------------------------------
INSERT INTO reels (reel_id, user_id, caption, video_url, duration_seconds, view_count, upload_date, hashtags) VALUES
(1,  1, '제주도 노을 daily 브이로그',      'https://reels.example.com/v1',  25, 152000, '2026-06-20', 'travel,daily'),
(2,  1, '부산 여행 하이라이트',            'https://reels.example.com/v2',  30,  98000, '2026-07-01', 'travel'),
(3,  2, '매운 라면 챌린지',                'https://reels.example.com/v3',  20, 210000, '2026-06-15', 'food'),
(4,  2, '홈메이드 파스타 daily 레시피',    'https://reels.example.com/v4',  40,  45000, '2026-07-05', 'food,daily'),
(5,  3, '커버댄스 챌린지',                 'https://reels.example.com/v5',  15, 320000, '2026-06-25', 'dance'),
(6,  3, '연습실 daily 비하인드',           'https://reels.example.com/v6',  22,  87000, '2026-07-08', 'dance,daily'),
(7,  4, '아침 daily 루틴 브이로그',        'https://reels.example.com/v7',  35,  61000, '2026-06-30', 'daily'),
(8,  5, '신작 게임 첫 플레이',             'https://reels.example.com/v8',  45, 133000, '2026-07-02', 'game'),
(9,  5, '게임 speedrun 도전',              'https://reels.example.com/v9',  28,  76000, '2026-07-10', 'game'),
(10, 6, '강아지 목욕시키기',               'https://reels.example.com/v10', 18, 254000, '2026-06-18', 'pet,daily'),
(11, 6, '고양이 첫 산책',                  'https://reels.example.com/v11', 20, 190000, '2026-07-06', 'pet'),
(12, 7, '5분 홈트레이닝 daily',            'https://reels.example.com/v12', 12, 342000, '2026-06-22', 'fitness,daily'),
(13, 8, '수채화 그리기 타임랩스',          'https://reels.example.com/v13', 33,  58000, '2026-07-03', 'art'),
(14, 9, '기타 커버 연주',                  'https://reels.example.com/v14', 27, 121000, '2026-06-28', 'music'),
(15, 11,'책 추천 daily 브이로그',          'https://reels.example.com/v15', 24,  39000, '2026-07-09', 'book,daily');

-- ------------------------------------------------------------
-- 3. likes (25행)
-- ------------------------------------------------------------
INSERT INTO likes (user_id, reel_id) VALUES
(2, 1), (3, 1), (4, 1), (5, 1),
(1, 3), (4, 3), (6, 3), (7, 3), (8, 3),
(1, 5), (2, 5), (4, 5), (6, 5), (9, 5), (10, 5),
(3, 10), (5, 10), (7, 10), (12, 10),
(2, 12), (6, 12), (8, 12), (11, 12),
(1, 14),
(9, 2);

-- ------------------------------------------------------------
-- 4. comments (16행)
-- ------------------------------------------------------------
INSERT INTO comments (user_id, reel_id, content) VALUES
(2, 1,  '제주도 진짜 예쁘네요'),
(5, 1,  '저도 가보고 싶어요'),
(1, 3,  '저건 저는 절대 못 먹어요'),
(6, 3,  '맵기 실화인가요'),
(4, 5,  '춤 진짜 잘 추시네요'),
(9, 5,  '연습 얼마나 하신 거예요'),
(2, 10, '강아지 너무 귀여워요'),
(7, 10, '목욕 시간에 얌전하네요'),
(3, 12, '오늘부터 따라해볼게요'),
(8, 12, '5분만에 땀나네요'),
(10,14, '기타 소리 좋아요'),
(1, 14, '어떤 기타 쓰시나요'),
(12,15, '책 제목이 뭔가요'),
(11,7,  '루틴 참고할게요'),
(6, 8,  '신작 게임 재밌어 보여요'),
(2, 11, '고양이 산책 신기해요');
# 03_queries.sql 실행 결과

실행 환경: Python 3 sqlite3 모듈 (SQLite), PRAGMA foreign_keys = ON

### Q1. 조회수 10만 이상인 릴스 조회
```
reel_id | caption | view_count
------------------------------------------------------------
1 | 제주도 노을 daily 브이로그 | 152000
3 | 매운 라면 챌린지 | 210000
5 | 커버댄스 챌린지 | 320000
8 | 신작 게임 첫 플레이 | 133000
10 | 강아지 목욕시키기 | 254000
11 | 고양이 첫 산책 | 190000
12 | 5분 홈트레이닝 daily | 342000
14 | 기타 커버 연주 | 121000

(8행)
```

### Q2. 전체 릴스 조회수 내림차순 정렬
```
reel_id | caption | view_count
------------------------------------------------------------
12 | 5분 홈트레이닝 daily | 342000
5 | 커버댄스 챌린지 | 320000
10 | 강아지 목욕시키기 | 254000
3 | 매운 라면 챌린지 | 210000
11 | 고양이 첫 산책 | 190000
1 | 제주도 노을 daily 브이로그 | 152000
8 | 신작 게임 첫 플레이 | 133000
14 | 기타 커버 연주 | 121000
2 | 부산 여행 하이라이트 | 98000
6 | 연습실 daily 비하인드 | 87000
9 | 게임 speedrun 도전 | 76000
7 | 아침 daily 루틴 브이로그 | 61000
13 | 수채화 그리기 타임랩스 | 58000
4 | 홈메이드 파스타 daily 레시피 | 45000
15 | 책 추천 daily 브이로그 | 39000

(15행)
```

### Q3. 최신 업로드 릴스 5개
```
reel_id | caption | upload_date
------------------------------------------------------------
9 | 게임 speedrun 도전 | 2026-07-10
15 | 책 추천 daily 브이로그 | 2026-07-09
6 | 연습실 daily 비하인드 | 2026-07-08
11 | 고양이 첫 산책 | 2026-07-06
4 | 홈메이드 파스타 daily 레시피 | 2026-07-05

(5행)
```

### Q4. 캡션에 'daily' 포함된 릴스 검색
```
reel_id | caption
------------------------------------------------------------
1 | 제주도 노을 daily 브이로그
4 | 홈메이드 파스타 daily 레시피
6 | 연습실 daily 비하인드
7 | 아침 daily 루틴 브이로그
12 | 5분 홈트레이닝 daily
15 | 책 추천 daily 브이로그

(6행)
```

### Q5. 해시태그에 'daily' 포함된 릴스 검색
```
reel_id | caption | hashtags
------------------------------------------------------------
1 | 제주도 노을 daily 브이로그 | travel,daily
4 | 홈메이드 파스타 daily 레시피 | food,daily
6 | 연습실 daily 비하인드 | dance,daily
7 | 아침 daily 루틴 브이로그 | daily
10 | 강아지 목욕시키기 | pet,daily
12 | 5분 홈트레이닝 daily | fitness,daily
15 | 책 추천 daily 브이로그 | book,daily

(7행)
```

### Q6. 릴스 + 업로더 정보 (INNER JOIN)
```
reel_id | caption | username
------------------------------------------------------------
1 | 제주도 노을 daily 브이로그 | traveler_ji
2 | 부산 여행 하이라이트 | traveler_ji
3 | 매운 라면 챌린지 | foodie_hoon
4 | 홈메이드 파스타 daily 레시피 | foodie_hoon
5 | 커버댄스 챌린지 | dance_yuna
6 | 연습실 daily 비하인드 | dance_yuna
7 | 아침 daily 루틴 브이로그 | daily_minji
8 | 신작 게임 첫 플레이 | gamer_seok
9 | 게임 speedrun 도전 | gamer_seok
10 | 강아지 목욕시키기 | pet_lover_haru
11 | 고양이 첫 산책 | pet_lover_haru
12 | 5분 홈트레이닝 daily | fitness_woo
13 | 수채화 그리기 타임랩스 | artsy_nari
14 | 기타 커버 연주 | music_taeho
15 | 책 추천 daily 브이로그 | book_junho

(15행)
```

### Q7. 댓글 + 작성자 + 대상 릴스 (INNER JOIN 2회)
```
comment_id | commenter | caption | content
------------------------------------------------------------
1 | foodie_hoon | 제주도 노을 daily 브이로그 | 제주도 진짜 예쁘네요
2 | gamer_seok | 제주도 노을 daily 브이로그 | 저도 가보고 싶어요
3 | traveler_ji | 매운 라면 챌린지 | 저건 저는 절대 못 먹어요
4 | pet_lover_haru | 매운 라면 챌린지 | 맵기 실화인가요
5 | daily_minji | 커버댄스 챌린지 | 춤 진짜 잘 추시네요
6 | music_taeho | 커버댄스 챌린지 | 연습 얼마나 하신 거예요
7 | foodie_hoon | 강아지 목욕시키기 | 강아지 너무 귀여워요
8 | fitness_woo | 강아지 목욕시키기 | 목욕 시간에 얌전하네요
9 | dance_yuna | 5분 홈트레이닝 daily | 오늘부터 따라해볼게요
10 | artsy_nari | 5분 홈트레이닝 daily | 5분만에 땀나네요
11 | beauty_soyeon | 기타 커버 연주 | 기타 소리 좋아요
12 | traveler_ji | 기타 커버 연주 | 어떤 기타 쓰시나요
13 | coding_areum | 책 추천 daily 브이로그 | 책 제목이 뭔가요
14 | book_junho | 아침 daily 루틴 브이로그 | 루틴 참고할게요
15 | pet_lover_haru | 신작 게임 첫 플레이 | 신작 게임 재밌어 보여요
16 | foodie_hoon | 고양이 첫 산책 | 고양이 산책 신기해요

(16행)
```

### Q8. 댓글이 하나도 없는 릴스 (LEFT JOIN)
```
reel_id | caption
------------------------------------------------------------
2 | 부산 여행 하이라이트
4 | 홈메이드 파스타 daily 레시피
6 | 연습실 daily 비하인드
9 | 게임 speedrun 도전
13 | 수채화 그리기 타임랩스

(5행)
```

### Q9. 릴스에 좋아요 누른 사용자 목록 (INNER JOIN 2회)
```
reel_id | caption | liked_by
------------------------------------------------------------
1 | 제주도 노을 daily 브이로그 | foodie_hoon
1 | 제주도 노을 daily 브이로그 | dance_yuna
1 | 제주도 노을 daily 브이로그 | daily_minji
1 | 제주도 노을 daily 브이로그 | gamer_seok
2 | 부산 여행 하이라이트 | music_taeho
3 | 매운 라면 챌린지 | traveler_ji
3 | 매운 라면 챌린지 | daily_minji
3 | 매운 라면 챌린지 | pet_lover_haru
3 | 매운 라면 챌린지 | fitness_woo
3 | 매운 라면 챌린지 | artsy_nari
5 | 커버댄스 챌린지 | traveler_ji
5 | 커버댄스 챌린지 | foodie_hoon
5 | 커버댄스 챌린지 | daily_minji
5 | 커버댄스 챌린지 | pet_lover_haru
5 | 커버댄스 챌린지 | music_taeho
5 | 커버댄스 챌린지 | beauty_soyeon
10 | 강아지 목욕시키기 | dance_yuna
10 | 강아지 목욕시키기 | gamer_seok
10 | 강아지 목욕시키기 | fitness_woo
10 | 강아지 목욕시키기 | coding_areum
12 | 5분 홈트레이닝 daily | foodie_hoon
12 | 5분 홈트레이닝 daily | pet_lover_haru
12 | 5분 홈트레이닝 daily | artsy_nari
12 | 5분 홈트레이닝 daily | book_junho
14 | 기타 커버 연주 | traveler_ji

(25행)
```

### Q10. 사용자별 릴스 수 / 총 조회수 (COUNT, SUM)
```
username | reel_count | total_views
------------------------------------------------------------
pet_lover_haru | 2 | 444000
dance_yuna | 2 | 407000
fitness_woo | 1 | 342000
foodie_hoon | 2 | 255000
traveler_ji | 2 | 250000
gamer_seok | 2 | 209000
music_taeho | 1 | 121000
daily_minji | 1 | 61000
artsy_nari | 1 | 58000
book_junho | 1 | 39000

(10행)
```

### Q11. 릴스별 좋아요 개수 (COUNT)
```
reel_id | caption | like_count
------------------------------------------------------------
5 | 커버댄스 챌린지 | 6
3 | 매운 라면 챌린지 | 5
1 | 제주도 노을 daily 브이로그 | 4
10 | 강아지 목욕시키기 | 4
12 | 5분 홈트레이닝 daily | 4
2 | 부산 여행 하이라이트 | 1
14 | 기타 커버 연주 | 1
4 | 홈메이드 파스타 daily 레시피 | 0
6 | 연습실 daily 비하인드 | 0
7 | 아침 daily 루틴 브이로그 | 0
8 | 신작 게임 첫 플레이 | 0
9 | 게임 speedrun 도전 | 0
11 | 고양이 첫 산책 | 0
13 | 수채화 그리기 타임랩스 | 0
15 | 책 추천 daily 브이로그 | 0

(15행)
```

### Q12. 사용자별 평균 조회수 (AVG)
```
username | avg_views
------------------------------------------------------------
fitness_woo | 342000.0
pet_lover_haru | 222000.0
dance_yuna | 203500.0
foodie_hoon | 127500.0
traveler_ji | 125000.0
music_taeho | 121000.0
gamer_seok | 104500.0
daily_minji | 61000.0
artsy_nari | 58000.0
book_junho | 39000.0

(10행)
```

### Q13. 평균 조회수보다 높은 릴스 (서브쿼리)
```
reel_id | caption | view_count
------------------------------------------------------------
12 | 5분 홈트레이닝 daily | 342000
5 | 커버댄스 챌린지 | 320000
10 | 강아지 목욕시키기 | 254000
3 | 매운 라면 챌린지 | 210000
11 | 고양이 첫 산책 | 190000
1 | 제주도 노을 daily 브이로그 | 152000

(6행)
```

### Q14. 댓글을 한 번도 작성하지 않은 사용자 (서브쿼리)
```
username
------------------------------------------------------------

(0행)
```

### Q15. 특정 릴스(reel_id=3) 조회수 +5000 (UPDATE)
```
OK - 영향받은 행 수: 1
```

### Q15 확인. UPDATE 반영 결과
```
reel_id | caption | view_count
------------------------------------------------------------
3 | 매운 라면 챌린지 | 215000

(1행)
```

### Q16. 특정 좋아요 취소 (DELETE)
```
OK - 영향받은 행 수: 1
```

### Q16 확인. DELETE 반영 결과 (0행이면 정상 삭제)
```
like_id | user_id | reel_id | liked_at
------------------------------------------------------------

(0행)
```

### Q17. reels.user_id 인덱스 생성
```
OK - 영향받은 행 수: -1
```

### Q17 확인. 인덱스 생성 확인
```
name | tbl_name
------------------------------------------------------------
idx_reels_user_id | reels

(1행)
```

### 무결성 검증 1. 존재하지 않는 user_id(999)를 참조하는 릴스 삽입 시도
FK 제약(reels.user_id -> users.user_id)이 없는 값 참조를 막는지 확인
```
[의도된 실패] IntegrityError: FOREIGN KEY constraint failed
```

### 무결성 검증 2. 존재하지 않는 reel_id(999)를 참조하는 댓글 삽입 시도
FK 제약(comments.reel_id -> reels.reel_id)이 없는 값 참조를 막는지 확인
```
[의도된 실패] IntegrityError: FOREIGN KEY constraint failed
```

### 무결성 검증 3. 실제 존재하는 user_id(4)로 바꿔서 정상 삽입되는지 확인 (대조군)
```
OK - 영향받은 행 수: 1
```
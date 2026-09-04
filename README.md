# Codyssey-B1

본 과정은 AI/SW 기초 단계로 운영체제, 자료구조, 웹, DB, 클라우드까지 소프트웨어의 핵심 기술을 구현하며 차근차근 익히는 단계입니다.\
아래 링크로 원하는 파일에 빠르게 이동할 수 있습니다.

- [B1-1 파일 가기](./B1-1/)  — 웹 기초 완성, 나만의 포트폴리오 구축
- [B2-1 파일 가기](./B2-1/)  — 파일 기반 가계부 콘솔 프로그램 생성
- [B2-2 파일 가기](./B2-2/)  — 실전 Git 협업 워크 플로우
- [B3-1 파일 가기](./B3-1/)  — AWS 클라우드 인프라 구축
- [B3-2 파일 가기](./B3-2/)  — 내가 고친 코드 설명을 AI가 대신 써주는 커밋 메시지 도우미 (ai-gitgen)
- [B4-1 파일 가기](./B4-1/)  — 시스템 관제 자동화 스크립트 개발
- [B4-2 파일 가기](./B4-2/)  — 리눅스 프로세스 및 시스템 리소스 트러블 슈팅
- [B5-1 파일 가기](./B5-1/)  — 정보를 엄청 빠르게 찾아주는 작은 저장소 만들기 (Mini Redis)
- [B5-2 파일 가기](./B5-2/)  — 파일이 언제 어떻게 바뀌었는지 기록하는 작은 프로그램 만들기 (Mini Git)
- [B6-1 파일 가기](./B6-1/)  — SNS 데이터베이스 스키마 설계 및 SQL 실습

> ⓘ 2026-09-04 기준 코디세이 학습로드맵의 미션 번호 체계가 다시 개편되어, 위 목록은 새 번호에 맞춰 재정렬한 것입니다 (내용은 그대로, 폴더명/번호만 변경).

```
전체적인 디렉토리 구조:

B1-1 (웹 기초 완성, 나만의 포트폴리오 구축)
├── README.md              # 프로젝트 설명 문서
├── index.html             # 포트폴리오 메인 페이지
├── css/                   # 스타일시트 (base, layout, components, responsive 등)
├── js/                    # 스크립트 (main, error, empty, rate-limit 등)
└── images/                # 이미지 리소스

B2-1 (파일 기반 가계부 콘솔 프로그램 생성)
├── README.md              # 실행 방법 문서
├── MISSION.md             # 미션 요구사항 원문 정리
├── CONCEPT.md             # 알아야 되는 개념들 문서 정리 (비전공자용)
├── CHECKLIST.md           # 완성도 점검 체크리스트
├── EVALUATION.md          # 동료평가 진행 워크플로우
└── budget_app/            # 구현 코드
    ├── __init__.py             # 패키지 표시 파일
    ├── __main__.py             # 실행 시작점 (python -m budget_app)
    ├── cli.py                  # 화면 입출력 담당
    ├── models.py                # 데이터 상자(Transaction 등) 정의
    ├── storage.py               # 파일 저장/읽기 담당
    ├── services.py              # 검색/요약/예산 등 실제 로직
    └── decorators.py            # 공통 기능 포장지 (실행시간 측정, 오류 처리)

B2-2 (실전 Git 협업 워크 플로우)
└── README.md              # 워크플로우 관련 문서

B3-1 (AWS 클라우드 인프라 구축)
├── README.md                     # 프로젝트 설명 문서
├── setup-infrastructure.sh       # 인프라 구축 스크립트
├── setup-iam.sh                  # IAM 설정 스크립트
├── cleanup-infrastructure.sh     # 인프라 정리 스크립트
├── docs/                         # 문서 (architecture, troubleshooting, why-analysis 등)
└── B3-1 evidence_image/          # VPC/IAM/서브넷 구성 증거 스크린샷

B3-2 (내가 고친 코드 설명을 AI가 대신 써주는 커밋 메시지 도우미, ai-gitgen)
├── README.md              # 프로젝트 설명서 (비전공자용 개념 정리 포함)
├── main.py                # CLI 진입점 (commit / pr 명령)
├── git_collector.py       # git status / git diff 수집
├── ai_client.py           # AI API REST 호출 클라이언트
├── prompts.py             # 커밋/PR 프롬프트 템플릿
├── validators.py          # 출력 형식 검증 및 후처리
├── safe_mode.py           # 민감정보 마스킹 + diff 전송량 제한
├── demo_safe_mode.py      # safe_mode 동작 데모/테스트 스크립트
├── .env                   # AI API 키 등 환경변수 (git에 커밋되지 않음)
└── .gitignore             # __pycache__, .venv, .env 등 제외 규칙

B4-1  (시스템 관제 자동화 스크립트 개발)
├── Screenshot          # 이미지 관련 파일
├── README.md           # 미션 관련 전체 문서
├── B4-1_Concept.md     # 리눅스 개념 문서 정리
├── Result.md           # 미션 수행 문서
├── agent-app           # 앱 실행을 위한 바이너리 파일
└── linux-concepts.html # 리눅스 개념 html 파일

B4-2   (리눅스 프로세스 및 시스템 리소스 트러블 슈팅)
├── B4-2 Concept.md           # (개념 설명 문서)
├── README.md                 # (프로젝트 설명)
├── Result1-2.md              # (결과 분석)
├── Result2.md                # (추가 결과 분석)
├── Dockerfile                # (Docker 설정)
├── monitor.sh                # (모니터링 셸 스크립트)
├── 데드락 발생 관련 메모.md   # (데드락 메모)
├── agent-app-leak            # (애플리케이션 소스 코드)
├── deadlock_evidence/        # (데드락 증거 자료)
└── test/                     # (테스트 및 분석)
    ├── 01_OOM_Analysis.md          # (OOM 분석)
    ├── 02_CPU_Analysis.md          # (CPU 분석)
    ├── 03_Deadlock_Analysis.md     # (데드락 분석)
    ├── CPU_Stress_test.mov         # (CPU 스트레스 테스트 영상)
    ├── screenshot/                 # (스크린샷: DeadLock1/2, OOM_100MB/256MB 등)
    └── logs/                       # (각종 테스트 로그: agent_app_100MB/256mb, deadlock_test, oom_test_100mb/256mb)

B5-1 (정보를 엄청 빠르게 찾아주는 작은 저장소 만들기, Mini Redis)
├── README.md              # 실행 방법 문서
├── MISSION.md             # 미션 요구사항 원문 정리
├── CONCEPT.md             # 자료구조 개념 설명 (비전공자용)
├── CHECKLIST.md           # 완성도 점검 체크리스트
├── EVALUATION.md          # 동료평가 진행 워크플로우
└── mini_redis/            # 구현 코드
    ├── main.py                  # 실행 시작점
    ├── doubly_linked_list.py    # 이중 연결 리스트 직접 구현
    ├── hashmap.py               # 해시맵(체이닝) 직접 구현
    ├── heap.py                  # 최소 힙 직접 구현
    └── store.py                 # 데이터/LRU/TTL 관리 로직

B5-2 (파일이 언제 어떻게 바뀌었는지 기록하는 작은 프로그램 만들기, Mini Git)
├── README.md              # 실행 방법 문서
├── MISSION.md             # 미션 요구사항 원문 정리
├── CONCEPT.md             # 그래프/정렬/역색인 개념 설명
├── CHECKLIST.md           # 완성도 점검 체크리스트
├── EVALUATION.md          # 동료평가 진행 워크플로우
└── mini_git/              # 구현 코드
    ├── main.py                  # 실행 시작점
    ├── graph.py                 # 커밋 그래프(DAG) 관리
    ├── index.py                 # 역색인(키워드/작성자) 관리
    └── algorithms.py            # 위상정렬/BFS/조상탐색/merge sort

B6-1 (SNS 데이터베이스 스키마 설계 및 SQL 실습)
├── README.md              # 프로젝트 설명 문서
├── 01_schema.sql          # 스키마 정의
├── 02_sample_data.sql     # 샘플 데이터
├── 03_queries.sql         # 실습 쿼리 모음
├── querie_results.md      # 쿼리 결과 정리
├── Relationship.png       # ER 관계도
├── SQL Diagram.png        # SQL 다이어그램
└── Screenshot/            # 쿼리 실행 스크린샷 (Q1~Q17)
```

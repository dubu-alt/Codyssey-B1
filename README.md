# Codyssey-B1

본 과정은 AI/SW 기초 단계로 운영체제, 자료구조, 웹, DB, 클라우드까지 소프트웨어의 핵심 기술을 구현하며 차근차근 익히는 단계입니다.\
아래 링크로 원하는 파일에 빠르게 이동할 수 있습니다.

- [B1-1 파일 가기](./B1-1/)  — 시스템 관제 자동화 스크립트 개발
- [B1-2 파일 가기](./B1-2/)  — 리눅스 프로세스 및 시스템 리소스 트러블 슈팅
- [B2-1 파일 가기](./B2-1/)  — 파일 기반 가계부 콘솔 프로그램 생성
- [B2-2 파일 가기](./B2-2/)  — 실전 Git 협업 워크 플로우
- [B4-1 파일 가기](./B4-1/)  — 웹 기초 완성, 나만의 포트폴리오 구축
- [B5-1 파일 가기](./B5-1/)  — SNS 데이터베이스 스키마 설계 및 SQL 실습
- [B6-1 파일 가기](./B6-1/)  — AWS 클라우드 인프라 구축
- [B6-2 파일 가기](./B6-2/)  — AWS 클라우드 미션 개념 정리

```
전체적인 디렉토리 구조:

B1-1  (시스템 관제 자동화 스크립트 개발)
├── Screenshot          # 이미지 관련 파일
├── README.md           # 미션 관련 전체 문서
├── B1-1_Concept.md     # 리눅스 개념 문서 정리
├── Result.md           # 미션 수행 문서
├── agent-app           # 앱 실행을 위한 바이너리 파일
├── linux-concepts.html # 리눅스 개념 html 파일
├── .git/ (Git 저장소)  # git init을 통한 숨김 파일
└── .gitignore          # 무시 가능한 Git 파일

B1-2   (리눅스 프로세스 및 시스템 리소스 트러블 슈팅)
├── B1-2 Concept.md           # (개념 설명 문서)
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
    ├── screenshot/                 # (스크린샷)
    ├── logs/                       # (각종 테스트 로그)
    ├── logs_oom/
    └── logs_oom_256/

B2-1 (파일 기반 가계부 콘솔 프로그램 생성)
├── README.md              # 기술 명세서
└── B2-1 Concept.md        # 알아야 되는 개념들 문서 정리

B2-2 (실전 Git 협업 워크 플로우)
└── README.md              # 워크플로우 관련 문서

B4-1 (웹 기초 완성, 나만의 포트폴리오 구축)
├── README.md              # 프로젝트 설명 문서
├── index.html             # 포트폴리오 메인 페이지
├── css/                   # 스타일시트 (base, layout, components, responsive 등)
├── js/                    # 스크립트 (main, error, empty, rate-limit 등)
└── images/                # 이미지 리소스

B5-1 (SNS 데이터베이스 스키마 설계 및 SQL 실습)
├── README.md              # 프로젝트 설명 문서
├── 01_schema.sql          # 스키마 정의
├── 02_sample_data.sql     # 샘플 데이터
├── 03_queries.sql         # 실습 쿼리 모음
├── querie_results.md      # 쿼리 결과 정리
├── Relationship.png       # ER 관계도
├── SQL Diagram.png        # SQL 다이어그램
└── Screenshot/            # 쿼리 실행 스크린샷 (Q1~Q17)

B6-1 (AWS 클라우드 인프라 구축)
├── README.md                     # 프로젝트 설명 문서
├── setup-infrastructure.sh       # 인프라 구축 스크립트
├── setup-iam.sh                  # IAM 설정 스크립트
├── cleanup-infrastructure.sh     # 인프라 정리 스크립트
└── docs/                         # 문서 (architecture, troubleshooting, why-analysis 등)

B6-2 (AWS 클라우드 미션 개념 정리)
└── README.md              # 비전공자를 위한 개념 설명서
```

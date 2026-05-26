# B1-2 시스템 장애 분석 및 이슈 리포트 수행 내역 (보너스 포함)

> 기준 문서: `B1-2/README.md`

## 0. 수행 목적

`agent-app-leak` 실행 환경을 구성한 뒤, 다음 3가지 장애를 각각 재현/분석하고 GitHub Issue 형식으로 정리한다.

1. OOM Crash (Memory Leak)
2. CPU Spike (Watchdog Abort)
3. Deadlock (무응답 정체)

추가로 보너스 과제인 **스케줄링 알고리즘 추론**을 로그 패턴 기반으로 수행한다.

---

## 1. 사전 준비 및 실행 조건 검증

README의 실행 조건 표를 기준으로 사전 점검을 진행했다.

- 일반 사용자 계정으로 실행 (root 금지)
- `AGENT_HOME` 설정
- `AGENT_PORT=15034`
- `AGENT_UPLOAD_DIR`, `AGENT_KEY_PATH`, `AGENT_LOG_DIR` 경로 생성 및 권한 확인
- `secret.key` 파일 생성 및 값 `agent_api_key_test` 확인
- 환경변수 범위 검증
  - `MEMORY_LIMIT`: 50~512
  - `CPU_MAX_OCCUPY`: 10~100
  - `MULTI_THREAD_ENABLE`: true/false 계열

### 점검 명령 예시

```bash
whoami
printenv | egrep 'AGENT_HOME|AGENT_PORT|AGENT_UPLOAD_DIR|AGENT_KEY_PATH|AGENT_LOG_DIR|MEMORY_LIMIT|CPU_MAX_OCCUPY|MULTI_THREAD_ENABLE'
ls -ld "$AGENT_HOME" "$AGENT_UPLOAD_DIR" "$AGENT_KEY_PATH" "$AGENT_LOG_DIR"
cat "$AGENT_KEY_PATH/secret.key"
```

---

## 2. 공통 관측 방법

세 케이스 모두 아래 절차로 동일하게 수행했다.

1. 앱 실행 시각 기록
2. `monitor.sh` 또는 `top/ps`로 자원 관측 시작
3. 앱 로그 실시간 확인
4. 장애 발생 시각/종료 메시지 수집
5. 조정 변수 변경 후 재실행하여 Before/After 비교

### 관측 명령 예시

```bash
ps -ef | grep agent-app-leak | grep -v grep
top -b -n 1 | head -n 20
ps -L -p <PID> -o pid,tid,psr,pcpu,pmem,stat,cmd
```

---

## 3. [Bug] OOM Crash - MemoryGuard에 의한 강제 종료

## 3-1. Description

기본 설정 실행 시 시간 경과에 따라 메모리 사용량이 지속 상승했고, 임계점 도달 시 프로세스가 종료되었다.

## 3-2. Evidence & Logs

- 관측 로그에서 메모리 사용량이 선형적으로 증가
- 종료 직전/직후 로그에서 아래 유형의 메시지를 확인
  - `Memory limit exceeded ...`
  - `SELF-TERMINATED ...`

### OOM 관측 명령 예시

```bash
export MEMORY_LIMIT=100
./agent-app-leak
```

## 3-3. Root Cause Analysis

메모리 누수로 인해 프로세스의 물리 메모리 점유가 지속 증가했고, 내부 `MemoryGuard`가 임계치 초과를 감지해 보호 목적의 강제 종료를 수행한 것으로 판단했다.

## 3-4. Workaround & Verification

- 조치: `MEMORY_LIMIT` 상향 (예: 100 → 256 또는 512)
- 검증: 재실행 시 종료까지 소요 시간이 유의미하게 증가함을 확인

### Before / After 예시

| 항목 | Before | After |
|---|---:|---:|
| MEMORY_LIMIT | 100MB | 256MB |
| 생존 시간 | 짧음(조기 종료) | 증가 |
| 종료 메시지 | MemoryGuard 강제 종료 | 동일 유형이나 발생 시점 지연 |

---

## 4. [Bug] CPU Spike - Watchdog 보호 종료

## 4-1. Description

실행 중 특정 구간에서 `agent-app-leak` 단일 프로세스 CPU 점유율이 급증하고, 이후 Watchdog 종료 메시지와 함께 프로세스가 종료되었다.

## 4-2. Evidence & Logs

- `top/ps`에서 해당 프로세스 CPU 고점 확인
- 종료 로그에서 아래 유형 메시지 확인
  - `WATCHDOG ...`
  - `SIGTERM ...`

### CPU 관측 명령 예시

```bash
export CPU_MAX_OCCUPY=40
./agent-app-leak
```

## 4-3. Root Cause Analysis

내부 연산 구간에서 CPU 점유가 임계치를 초과했고, 시스템 보호용 Watchdog 정책이 비정상 부하로 판단하여 종료를 수행한 것으로 분석했다.

## 4-4. Workaround & Verification

- 조치: `CPU_MAX_OCCUPY` 상향 조정 (예: 40 → 70)
- 검증: 종료 여부 또는 종료 시점이 완화/지연되는지 비교

### Before / After 예시

| 항목 | Before | After |
|---|---:|---:|
| CPU_MAX_OCCUPY | 40% | 70% |
| 최고 CPU | 빠른 임계치 도달 | 임계치 도달 지연 |
| 종료 상태 | Watchdog 종료 | 종료 지연 또는 생존 시간 증가 |

---

## 5. [Bug] Deadlock - 프로세스 생존 상태 무응답

## 5-1. Description

프로세스 PID는 살아 있으나, CPU/MEM 변화가 거의 없고 로그가 특정 지점 이후 더 이상 진행되지 않는 무응답 상태를 확인했다.

## 5-2. Evidence & Logs

- `ps -ef`로 PID 생존 확인
- `top -H` 또는 `ps -L`에서 스레드 활동 정체 확인
- 마지막 로그에서 `WAITING`/`BLOCKED` 계열 지점 확인

### Deadlock 관측 명령 예시

```bash
export MULTI_THREAD_ENABLE=true
./agent-app-leak
ps -ef | grep agent-app-leak | grep -v grep
ps -L -p <PID> -o pid,tid,pcpu,pmem,stat,cmd
```

## 5-3. Root Cause Analysis

다중 스레드가 상호 락을 점유한 상태에서 상대 자원을 기다리는 순환 대기(circular wait)가 발생해 교착상태가 형성된 것으로 해석했다.

## 5-4. Workaround & Verification

- 조치: `MULTI_THREAD_ENABLE=false`로 단일 스레드 모드 재실행
- 검증: 동일 구간에서 무응답이 재현되지 않고 로그가 연속 진행되는지 확인

### Before / After 예시

| 항목 | Before | After |
|---|---:|---:|
| MULTI_THREAD_ENABLE | true | false |
| PID 상태 | 살아있음 | 살아있음 |
| 응답성 | 무응답 정체 | 정상 진행 |
| 로그 진행 | 특정 지점에서 정지 | 지속 출력 |

---

## 6. 보너스 - 로그 기반 스케줄링 알고리즘 추론

## 6-1. 관찰

타임스탬프 로그를 기준으로 스레드 A/B/C의 실행 순서를 추적한 결과, 한 스레드가 완료되기 전에 다른 스레드가 교대로 실행되는 패턴이 반복되었다.

## 6-2. 비교 추론

- FCFS 가능성 낮음: 선행 작업 완료 전 교체 발생
- Priority 가능성 낮음: 특정 스레드 독점 경향 미약
- Round-Robin 가능성 높음: 짧은 time-slice 단위의 순환 실행 패턴

## 6-3. 결론

현재 동작 패턴은 **Round-Robin 스케줄링**에 가장 부합한다고 판단했다.

## 6-4. 장단점 및 적용 아키텍처

- 장점: 공정성, 응답성 개선
- 단점: 컨텍스트 스위칭 오버헤드
- 적합: 다중 요청 웹 서비스/대화형 응답 시스템
- 비적합(상대적): 긴 배치 작업 위주의 단순 처리 파이프라인

---

## 7. 최종 정리

본 수행에서는 README 요구사항에 맞춰 다음을 완료했다.

- OOM, CPU, Deadlock 각 케이스에 대해
  - 현상 기술
  - 증거 수집 항목 정의
  - 원인 분석
  - 변수 기반 완화 조치 및 Before/After 비교
- 보너스 과제(스케줄링 추론) 수행

향후 개선 항목:

1. 관측 로그를 CSV로 정리해 그래프화
2. 케이스별 재현 시간을 표준화해 반복 실험 통계화
3. 근본 수정안(코드 레벨 메모리 해제/락 획득 순서 표준화) 제안서 분리 작성

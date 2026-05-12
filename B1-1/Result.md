# 미션 수행

초기 도커 컨테이너와 이미지 목록 확인 후 아무것도 없으므로 우분투 컨테이너 생성  
아래 스크린샷은 우분투 이미지를 받고 컨테이너 안으로 진입

![스크린샷](Screenshot/1.png)

---

## 패키지 업데이트 및 설치

각각의 패키지는 보안 설정과 앱 실행 그리고 권한 관리 3가지에 필요한 도구들임  
아래는 패키지와 용도 그리고 미션에 따른 사용 용도를 구분해 놓았음

| 패키지 | 용도 | 상세 미션 |
| :--- | :--- | :--- |
| **openssh-server** | SSH 서버 | SSH 포트 20022 변경, Root 로그인 차단 |
| **ufw** | 방화벽 | 포트 허용 정책 설정 |
| **python3** | Python 실행기 | 제공된 agent 앱 실행 |
| **sudo** | 권한 상승 | 일반 계정에서 필요 시 sudo 사용 권한 부여 |
| **vim** | 텍스트 편집기 | 설정 파일 수정 및 편집 |
| **net-tools** | 네트워크 도구 | `netstat` 명령어로 포트 상태 확인 |
| **iproute2** | 네트워크 도구 | `ss -tulnp` 명령어로 포트 리슨 확인 |
| **acl** | 접근 제어 목록 | 디렉토리 세밀한 권한 설정 (`getfacl`, `setfacl`) |

```bash
apt update && apt install -y \
  openssh-server \
  ufw \
  python3 \
  sudo \
  vim \
  net-tools \
  iproute2 \
  acl
```

![수행사진 2](Screenshot/2.png)![수행사진 2-2](Screenshot/2-2.png)

---

## 1. SSH 설정

먼저 SSH 설정 파일을 열고 Vim 에디터에서 포트를 변경함. 기본값 22에서 요구사항인 20022로 수정

```bash
vim /etc/ssh/sshd_config
```

**Port 변경**
```
Port 20022
```

**Root 로그인 차단**
```
PermitRootLogin no
```

<img src="Screenshot/SSH  포트변경 및 Root 로그인 차단.png" width="200" height="200" alt="포트 변경 전 사진" style="margin-right: 20px;"> <img src="Screenshot/SSH  포트변경 및 Root 로그인 차단2.png" width="200" height="200" alt="포트 변경 사진"> <br>
<img src="Screenshot/SSH 시작.png" alt="SSH 시작">

---

## 문제 발생 (변경 실패)

본 내용은 수행 중 실패를 보고하는 문서다.

### 문제 1. 포트 변경 안됨

**SSH 서버 시작 및 설정 확인**
```bash
service ssh start      # SSH 서버 시작
ss -tulnp | grep sshd  # 포트가 잘 열렸는지 설정 확인

ufw allow 20022/tcp    # ufw 방화벽 20022 포트 허용
ufw allow 15034/tcp    # ufw 방화벽 15034 포트 허용
ufw --force enable     # ufw 적용
ufw status             # ufw 상태 확인
```

![포트 변경 실패 사진](<Screenshot/포트 변경 실패.png>)

### 해결 과정

**원인 파악:** `Port 20022` 앞에 `#`이 붙어 있어서 주석 처리된 상태로, 포트 기본값인 22로 뜸

- 다시 vim 에디터로 가서 `#Port 20022`에서 `#`을 제거하고 저장 후 다시 수행

```bash
vim /etc/ssh/sshd_config  # SSH 설정으로 다시 들어감
Port 20022                # 주석 처리된 '#'을 제거함
PermitRootLogin no        # 주석 처리된 '#'을 제거함

service ssh restart       # SSH 재시작
ss -tulnp | grep sshd     # 포트 및 설정 다시 확인
```

<img src="Screenshot/포트 변경 재수정.png" width="300" height="300" alt="포트 재수정"> <br>
<img src="Screenshot/SSH 재수행.png" alt="SSH 재수행">

---

## UFW 방화벽 설정하기

포트 2개(20022와 15034) 허용 시도 실패

도커 컨테이너에서 UFW가 iptables 권한 거부 문제로 안됨

<img src="Screenshot/UFW_Permission_Denied.png" alt="UFW 권한 거절">

**iptables 권한이란?** 컨테이너 내부에서 호스트 시스템의 네트워크 패킷 필터링 규칙을 조작할 수 있는 권한인데,
보안을 위해 격리되어 있기 때문에 시스템의 네트워크 설정을 바꿀 수 없으나 특정 옵션을 주어서 권한을 허용할 수 있음

현재 컨테이너에서 나가서 `--privileged` 옵션을 추가해서 다시 생성

```bash
# 컨테이너 밖(exit 하고 난 뒤)에서 실행
docker rm -f mission             # 기존에 만들었던 mission 컨테이너 삭제

docker run -it --name mission \  # mission 컨테이너에 privileged 옵션 추가
  --privileged \
  -p 20022:20022 \
  -p 15034:15034 \
  ubuntu:22.04 /bin/bash
```

<img src="Screenshot/Set_Privileged.png" alt="컨테이너 privileged 추가">

### 패키지 다시 설치

```bash
apt update && apt install -y \
  openssh-server \
  ufw \
  python3 \
  sudo \
  vim \
  net-tools \
  iproute2 \
  acl
```

### 포트 및 로그인 권한 옵션 변경, SSH 시작

```bash
vim /etc/ssh/sshd_config    # SSH 다시 설정
Port 20022                  # 포트 20022로 변경
PermitRootLogin no          # 로그인 권한 옵션 no 변경

service ssh start           # SSH 시작
ss -tulnp | grep sshd       # 포트 리슨 다시 확인
```

### UFW 방화벽 설정 및 확인

```bash
ufw allow 20022/tcp    # SSH 포트 허용
ufw allow 15034/tcp    # 앱 포트 허용
ufw --force enable     # 방화벽 활성화
ufw status             # 상태 확인
```

확인 결과
```
Status: active
To                         Action      From
--                         ------      ----
20022/tcp                  ALLOW       Anywhere
15034/tcp                  ALLOW       Anywhere
20022/tcp (v6)             ALLOW       Anywhere (v6)
15034/tcp (v6)             ALLOW       Anywhere (v6)
```

<img src="Screenshot/UFW_Allow_Ports.png" alt="UFW 권한 허용">

---

## 계정 및 그룹 생성

```bash
# 계정 3개 생성
useradd -m -s /bin/bash agent-admin  # 운영/관리, cron 실행자
useradd -m -s /bin/bash agent-dev    # 개발/운영, monitor.sh 작성자
useradd -m -s /bin/bash agent-test   # QA/테스트
```

```bash
# 그룹 2개 생성
groupadd agent-common
groupadd agent-core
```

```bash
# 그룹에 계정 배정
# agent-common: admin, dev, test
usermod -aG agent-common agent-admin    # agent-common 배정
usermod -aG agent-common agent-dev      # agent-common 배정
usermod -aG agent-common agent-test     # agent-common 배정

# agent-core: admin, dev
usermod -aG agent-core agent-admin      # agent-core에 배정
usermod -aG agent-core agent-dev        # agent-core에 배정
```

<img src="Screenshot/User_Setup.png" alt="계정 및 그룹 생성">

## 그룹 배정 확인

```bash
id agent-admin
id agent-dev
id agent-test
```

확인 결과
```
uid=1001(agent-admin) gid=1001(agent-admin) groups=1001(agent-admin),1004(agent-common),1005(agent-core)
uid=1002(agent-dev) gid=1002(agent-dev) groups=1002(agent-dev),1004(agent-common),1005(agent-core)
uid=1003(agent-test) gid=1003(agent-test) groups=1003(agent-test),1004(agent-common)
```

<img src="Screenshot/User_Group_Check.png" alt="계정 및 그룹 확인">

---

## 디렉토리 구조 생성

```bash
mkdir -p /home/agent-admin/agent-app/upload_files
mkdir -p /home/agent-admin/agent-app/api_keys
mkdir -p /var/log/agent-app
```

디렉토리 구조 (최종)
```
$AGENT_HOME (/home/agent-admin/agent-app)
├── upload_files   (그룹: agent-common, 권한: 770)
├── api_keys       (그룹: agent-core,   권한: 770)
└── bin/           (그룹: agent-core,   권한: 750) ← monitor.sh 저장 위치

/var/log/agent-app (그룹: agent-core, 권한: 770)
```

> `bin/` 디렉토리는 monitor.sh 작성 단계에서 생성함

### 각 그룹마다 권한 설정

```bash
# upload_files: agent-common 그룹, R/W
chown -R agent-admin:agent-common /home/agent-admin/agent-app/upload_files
chmod 770 /home/agent-admin/agent-app/upload_files
```

```bash
# api_keys: agent-core 그룹, R/W
chown -R agent-admin:agent-core /home/agent-admin/agent-app/api_keys
chmod 770 /home/agent-admin/agent-app/api_keys
```

```bash
# /var/log/agent-app: agent-core 그룹, R/W
chown -R agent-admin:agent-core /var/log/agent-app
chmod 770 /var/log/agent-app
```

### 권한 확인

```bash
ls -l /home/agent-admin/agent-app/
ls -l /var/log/agent-app
```

<img src="Screenshot/Check_Group_Permissions.png" alt="그룹 권한 확인">

#### 권한 전체 확인표

| 디렉토리 경로 | 소유 그룹 | 권한(Permission) | 현재 상태 |
| :--- | :--- | :--- | :--- |
| `upload_files` | **agent-common** | `770` (drwxrwx---) | 정상 |
| `api_keys` | **agent-core** | `770` (drwxrwx---) | 정상 |
| `/var/log/agent-app` | **agent-core** | `770` (drwxrwx---) | 정상 |

---

## 앱 실행 환경 구성하기

```bash
# agent-admin 계정 환경 변수 설정
echo 'export AGENT_HOME=/home/agent-admin/agent-app' >> /home/agent-admin/.bashrc
echo 'export AGENT_PORT=15034' >> /home/agent-admin/.bashrc
echo 'export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files' >> /home/agent-admin/.bashrc
echo 'export AGENT_KEY_PATH=$AGENT_HOME/api_keys/t_secret.key' >> /home/agent-admin/.bashrc
echo 'export AGENT_LOG_DIR=/var/log/agent-app' >> /home/agent-admin/.bashrc
```

```bash
# 키 파일 생성
echo 'agent_api_key_test' > /home/agent-admin/agent-app/api_keys/t_secret.key

# 확인
cat /home/agent-admin/agent-app/api_keys/t_secret.key
```

<img src="Screenshot/Config_Env.png" alt="환경 변수 설정">

### 환경 변수 의미

| 변수명 | 의미 | 비고 |
| :--- | :--- | :--- |
| **AGENT_HOME** | 앱 루트 경로 | 애플리케이션 최상위 디렉토리 |
| **AGENT_PORT** | 앱이 사용할 포트 번호 | 서비스 리슨(Listen) 포트 |
| **AGENT_UPLOAD_DIR** | 파일 업로드 저장 경로 | `upload_files` 디렉토리와 연결 |
| **AGENT_KEY_PATH** | API 키 파일 경로 | `api_keys` 디렉토리 내 파일 경로 |
| **AGENT_LOG_DIR** | 로그 저장 경로 | `/var/log/agent-app` 등 로그 위치 |

---

## 앱 실행 환경 오류 해결 과정

### 문제 발생: GLIBC 버전 미충족

Ubuntu 22.04는 GLIBC 2.35까지 지원하는데, 제공된 앱이 GLIBC 2.38을 요구해서 실행 불가

```
[PYI-239:ERROR] Failed to load Python shared library '/tmp/_MEIAEZTIk/libpython3.12.so.1.0':
/lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.38' not found
```

### 해결 과정

1. 맥 아키텍처 확인
```bash
uname -m
# x86_64 출력됨
```

2. GLIBC 버전 확인
```bash
ldd --version
# ldd (Ubuntu GLIBC 2.35-0ubuntu3.13) 2.35
```

3. Ubuntu 버전 확인
```bash
cat /etc/os-release
# PRETTY_NAME="Ubuntu 22.04.5 LTS"
```

**원인:** Ubuntu 24.04를 pull 했으나 22.04 이미지가 캐시에서 실행된 것으로 판단  
**해결:** 기존 컨테이너 삭제 후 Ubuntu 24.04 이미지를 명시적으로 새로 받아서 재실행

```bash
docker rm -f mission
docker pull ubuntu:24.04
docker run -it --name mission \
  --privileged \
  -p 20022:20022 \
  -p 15034:15034 \
  ubuntu:24.04 /bin/bash

cat /etc/os-release  # 버전 재확인 → Ubuntu 24.04.4 LTS 확인
```

### Ubuntu 24.04 컨테이너에서 전체 설정 재수행

새 컨테이너이므로 패키지 설치부터 SSH, UFW, 계정/그룹, 디렉토리, 환경 변수, 키 파일 설정을 처음부터 동일하게 재수행함

```bash
# 패키지 재설치
apt update && apt install -y \
  openssh-server ufw python3 sudo vim net-tools iproute2 acl

# SSH 설정
sed -i 's/#Port 22/Port 20022/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
service ssh start

# UFW 설정
ufw allow 20022/tcp
ufw allow 15034/tcp
ufw --force enable

# 계정/그룹 생성 및 배정 (위와 동일하게 재수행)
# 디렉토리 구조 및 권한 설정 (위와 동일하게 재수행)
# 환경 변수 및 키 파일 설정 (위와 동일하게 재수행)
```

---

## 실행 권한 부여 및 앱 실행

파일 복사는 반드시 먼저 수행하고, 그 다음 컨테이너 안에서 실행 권한을 부여해야 함

```bash
# 1. 맥 터미널(컨테이너 밖)에서 파일 복사
docker cp ~/Desktop/Codyssey-B1/B1-1/agent-app mission:/home/agent-admin/agent-app/agent-app

# 2. 컨테이너 재진입
docker exec -it mission /bin/bash

# 3. 실행 권한 부여
chmod +x /home/agent-admin/agent-app/agent-app
```

<img src="Screenshot/permissions.png" alt="실행 권한 부여">

```bash
# agent-admin으로 전환
su - agent-admin

# 환경 변수 로드
source ~/.bashrc

# 앱 실행
$AGENT_HOME/agent-app
```

<img src="Screenshot/Load_Env_Run.png" alt="환경변수 로드 및 실행">

### 앱 부트 시퀀스 출력 결과

```
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
 ... Running as service user 'agent-admin' (uid=1001)
[2/5] Verifying Environment Variables     [OK]
 ... All required Envs correct
[3/5] Checking Required Files             [OK]
 ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]
 ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]
 ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
2026-05-12 11:49:54,267 [INFO] Agent listening at port 15034
2026-05-12 11:49:54,267 [INFO] === Agent Started. Beginning resource cycle. ===
```

<img src="Screenshot/Launch_app.png" alt="앱 실행">

### 현재 과정 이해

| 단계 | 명령어 | 의미 |
| :--- | :--- | :--- |
| 1 | `chmod +x agent-app` | 실행 권한 부여. 없으면 Permission denied 오류 발생 |
| 2 | `su - agent-admin` | root에서 agent-admin으로 전환. 미션 요구사항이 루트 실행 금지이기 때문 |
| 3 | `source ~/.bashrc` | 환경 변수 로드. 안 하면 Boot Sequence 2단계에서 실패 |
| 4 | `$AGENT_HOME/agent-app` | 앱 실행. Boot Sequence 5단계 검증 후 Agent READY 출력 |

**워크로드 시뮬레이션이란?**  
제공된 agent-app은 실제 서비스처럼 CPU와 메모리를 사용하는 척하는 테스트용 앱임
- CPU 레벨을 1~10으로 올렸다 내렸다 하면서 부하를 발생시킴
- monitor.sh가 CPU와 메모리 사용률을 수집하고 경고를 띄우는 걸 테스트하기 위한 부하 발생기 역할

---

## 포트 15034 Listen 상태 확인

agent-app이 켜진 상태로 새 터미널에서 mission 컨테이너로 진입해서 15034 포트 동작 여부 확인

```bash
# 앱을 켜 둔 상태로 새 터미널을 열고 컨테이너에 진입
docker exec -it mission /bin/bash

# 포트 15034 확인
ss -tulnp | grep 15034
```

확인 결과
```
tcp  LISTEN  0  1  0.0.0.0:15034  0.0.0.0:*  users:(("agent-app",pid=4924,fd=4))
```

<img src="Screenshot/Port15034_Listen.png" alt="Port15034_Listen">

---

## monitor.sh 작성

스크립트를 저장할 디렉토리를 생성. 요구사항에서 경로가 `$AGENT_HOME/bin/monitor.sh`이므로 `bin/` 디렉토리 필요

미션 요구사항: 소유자 `agent-dev` | 그룹 `agent-core` | 권한 `750`(rwxr-x---)
- 소유자(agent-dev): 읽기/쓰기/실행 가능
- 그룹(agent-core): 읽기/실행 가능 → agent-admin이 cron으로 실행 가능한 이유
- others: 접근 불가

```bash
mkdir -p /home/agent-admin/agent-app/bin                    # 스크립트 저장 디렉토리 생성
chown agent-dev:agent-core /home/agent-admin/agent-app/bin  # 소유자 | 그룹 지정
chmod 750 /home/agent-admin/agent-app/bin                   # 권한 부여
```

### monitor.sh 스크립트 작성 (최종본)

UFW 상태 확인을 `ufw status` 대신 `/etc/ufw/ufw.conf` 파일로 변경한 이유:  
`ufw status`는 root 권한이 있어야 실행 가능하지만, agent-admin은 일반 계정이므로 권한 오류 발생.  
`/etc/ufw/ufw.conf` 파일은 일반 계정도 읽을 수 있어서 이 방법으로 대체함

```bash
cat > /home/agent-admin/agent-app/bin/monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/agent-app/monitor.log"
MAX_LOG_SIZE=$((10 * 1024 * 1024))  # 10MB
MAX_LOG_COUNT=10
APP_NAME="agent-app"
APP_PORT=15034

echo "====== SYSTEM MONITOR RESULT ======"
echo ""
echo "[HEALTH CHECK]"

# 프로세스 체크: agent-app 프로세스 확인, 없으면 exit 1
PID=$(pgrep -f "$APP_NAME")
if [ -z "$PID" ]; then
    echo "Checking process '$APP_NAME'... [FAIL]"
    echo "[ERROR] Process not running. Exiting."
    exit 1
else
    echo "Checking process '$APP_NAME'... [OK] (PID: $PID)"
fi

# 포트 체크: TCP 15034 LISTEN 확인, 없으면 exit 1
PORT_CHECK=$(ss -tulnp | grep ":$APP_PORT ")
if [ -z "$PORT_CHECK" ]; then
    echo "Checking port $APP_PORT... [FAIL]"
    echo "[ERROR] Port $APP_PORT not listening. Exiting."
    exit 1
else
    echo "Checking port $APP_PORT... [OK]"
fi

echo ""
echo "[FIREWALL CHECK]"

# 방화벽 체크: root 없이 conf 파일로 확인 (ufw status는 root 권한 필요)
UFW_STATUS=$(cat /etc/ufw/ufw.conf 2>/dev/null | grep "ENABLED=yes")
if [ -z "$UFW_STATUS" ]; then
    echo "[WARNING] Firewall is not active."
else
    echo "Firewall status... [OK]"
fi

echo ""
echo "[RESOURCE MONITORING]"

# CPU 사용률
CPU=$(top -bn1 | grep "%Cpu" | awk '{print $2}')
if [ -z "$CPU" ]; then
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
fi

# 메모리 사용률
MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')

# 디스크 사용률 (Root 파티션)
DISK=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)

echo "CPU Usage  : ${CPU}%"
echo "MEM Usage  : ${MEM}%"
echo "DISK Used  : ${DISK}%"
echo ""

# 임계값 경고 (경고만 출력, 종료 안 함)
CPU_INT=$(echo "$CPU" | cut -d'.' -f1)
MEM_INT=$(echo "$MEM" | cut -d'.' -f1)

if [ "$CPU_INT" -gt 20 ]; then
    echo "[WARNING] CPU threshold exceeded (${CPU}% > 20%)"
fi
if [ "$MEM_INT" -gt 10 ]; then
    echo "[WARNING] MEM threshold exceeded (${MEM}% > 10%)"
fi
if [ "$DISK" -gt 80 ]; then
    echo "[WARNING] DISK threshold exceeded (${DISK}% > 80%)"
fi

# 로그 기록
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] PID:$PID CPU:${CPU}% MEM:${MEM}% DISK_USED:${DISK}%" >> "$LOG_FILE"

echo "[INFO] Log appended: $LOG_FILE"
echo ""
echo "======================================"

# 로그 파일 용량 관리: 10MB 초과 시 최대 10개 파일 순환 보관
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -c%s "$LOG_FILE")
    if [ "$LOG_SIZE" -gt "$MAX_LOG_SIZE" ]; then
        for i in $(seq $((MAX_LOG_COUNT-1)) -1 1); do
            if [ -f "${LOG_FILE}.$i" ]; then
                mv "${LOG_FILE}.$i" "${LOG_FILE}.$((i+1))"
            fi
        done
        mv "$LOG_FILE" "${LOG_FILE}.1"
        touch "$LOG_FILE"
        chown agent-dev:agent-core "$LOG_FILE"
        chmod 660 "$LOG_FILE"
    fi
fi
EOF
```

### 권한 설정 및 결과 확인

```bash
# monitor.sh 소유자를 agent-dev, 그룹을 agent-core로 변경
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh

# 권한 750 설정
chmod 750 /home/agent-admin/agent-app/bin/monitor.sh

# 확인 (-rwxr-x--- 형태로 나오면 정상)
ls -l /home/agent-admin/agent-app/bin/monitor.sh
```

확인 결과
```
-rwxr-x--- 1 agent-dev agent-core 2534 May 12 14:54 /home/agent-admin/agent-app/bin/monitor.sh
```

<img src="Screenshot/Monitor_Script_Auth.png" alt="모니터 스크립트 권한">

---

## monitor.sh 실행 테스트

### 문제 발생: 로그 파일 권한 및 UFW 권한 오류

agent-admin으로 monitor.sh를 실행했을 때 두 가지 오류 발생

```bash
# 오류 확인
/home/agent-admin/agent-app/bin/monitor.sh >> /tmp/test.log 2>&1
cat /tmp/test.log
```

오류 내용
```
ERROR: You need to be root to run this script   ← UFW 권한 문제
Permission denied: /var/log/agent-app/monitor.log  ← 로그 쓰기 권한 문제
```

**문제 1.** `ufw status`는 root 권한이 있어야 실행 가능  
**문제 2.** agent-admin이 `/var/log/agent-app/monitor.log`에 쓰기 권한 없음

### 해결 방법

**로그 파일 권한 수정**
```bash
# monitor.log 파일 생성 (없으면 생성, 있으면 그대로)
touch /var/log/agent-app/monitor.log

# 소유자를 agent-admin, 그룹을 agent-core로 변경
# agent-admin이 cron으로 로그를 쓸 수 있어야 하기 때문
chown agent-admin:agent-core /var/log/agent-app/monitor.log

# 664 설정: 소유자(rw-), 그룹(rw-), others(r--)
chmod 664 /var/log/agent-app/monitor.log
```

**UFW 체크 방식 변경**  
`ufw status` 대신 `/etc/ufw/ufw.conf` 파일로 활성화 여부를 확인하도록 monitor.sh 전체를 위의 최종본으로 재작성함

**권한 재설정**
```bash
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh
chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

### agent-admin 패스워드 생성

`su - agent-admin` 전환 시 패스워드가 필요하므로 root에서 설정

```bash
passwd agent-admin
# New password: (입력 시 화면에 표시 안됨)
```

<img src="Screenshot/password.png" alt="agent-admin 패스워드 생성">

### 최종 실행 결과

```bash
su - agent-admin
/home/agent-admin/agent-app/bin/monitor.sh
```

```
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app'... [OK] (PID: 4951)
Checking port 15034... [OK]

[FIREWALL CHECK]
Firewall status... [OK]

[RESOURCE MONITORING]
CPU Usage  : 0.0%
MEM Usage  : 4.3%
DISK Used  : 1%

[INFO] Log appended: /var/log/agent-app/monitor.log

======================================
```

<img src="Screenshot/Monitor_Script_Result.png" alt="모니터 스크립트 결과">

---

## 자동 실행 설정 (cron)

```bash
# mission 터미널로 진입 후 cron 패키지 설치
docker exec -it mission /bin/bash
apt install -y cron

# cron 서비스 시작
service cron start

# agent-admin 계정으로 전환
su - agent-admin

# crontab 편집기 열기
crontab -e
```

crontab에 아래 내용 추가
```
# 매분 자동으로 monitor.sh 실행
# * * * * * = 분 시 일 월 요일 (모두 *이면 매분 실행)
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

<img src="Screenshot/Cron_Job_Register.png" alt="매분 자동 실행">

### cron 주기 설명

| 위치 | 의미 | 범위 | 설정값(*) 의미 |
| :---: | :--- | :--- | :--- |
| **첫 번째** | 분 | 0 - 59 | 매분마다 실행 |
| **두 번째** | 시 | 0 - 23 | 매시마다 실행 |
| **세 번째** | 일 | 1 - 31 | 매일마다 실행 |
| **네 번째** | 월 | 1 - 12 | 매월마다 실행 |
| **다섯 번째** | 요일 | 0 - 7 | 매요일마다 실행 (0, 7: 일요일) |

---

## cron 로그 자동 누적 확인

1~2분 대기 후 로그 확인

```bash
cat /var/log/agent-app/monitor.log
```

확인 결과 (1분 간격으로 자동 누적됨)
```
[2026-05-12 13:40:51] PID:4951 CPU:0.0% MEM:4.6% DISK_USED:1%
[2026-05-12 14:26:01] PID:4951 CPU:0.0% MEM:4.2% DISK_USED:1%
[2026-05-12 14:27:02] PID:4951 CPU:0.0% MEM:5.1% DISK_USED:1%
[2026-05-12 14:28:01] PID:4951 CPU:0.0% MEM:3.8% DISK_USED:1%
```

<img src="Screenshot/Cron_Service_Status.png" alt="cron 로그 누적 확인">

1분 간격으로 로그가 자동 누적되는 것을 확인하여 cron 자동 실행이 정상 동작함을 검증 완료
<img src="Screenshot/Log_Content_Verify.png" alt="cron 누적 확인">
# 미션 수행
초기 도커 컨테이너와 이미지 목록 확인후 아무것도 없으므로 우분투 컨테이너 생성\
아래 스크린샷은 우분투 이미지를 받고 컨테이너 안으로 진입

![스크린샷](Screenshot/1.png)

## 패키지 업데이트 및 설치
각각의 패키지는 보안설정과 앱 실행 그리고 권한 관리 3가지에 필요한 도구들임\
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


```
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

1. SSH 설정
먼저 SSH 설정 파일을 열고 Vim 에디터에서 포트를 변경함 22 에서 수행하라고한 20022로 수정
```
vim /etc/ssh/sshd_config
```
**port 변경**
```
Port 20022
```
**Root로그인 차단**
```
PermitRootLogin no
```
<img src="Screenshot/SSH  포트변경 및 Root 로그인 차단.png" width="200" height="200" alt="포트 변경전 사진" style="margin-right: 20px;"> <img src="Screenshot/SSH  포트변경 및 Root 로그인 차단2.png" width="200" height="200" alt="포트 변경 사진"> <br>
<img src="Screenshot/SSH 시작.png" alt="SSH 시작">

## 문제 발생 (변경 실패)
본 내용은 수행중 실패를 보고하는 문서다.

### 1. 포트 변경 안됨

**SSH 서버 시작 및 설정 확인**
```
service ssh start      # SSH 서버 시작
ss -tulnp | grep sshd  # 포트가 잘 열렸는지 설정 확인 
```
![포트 변경 실패 사진](<Screenshot/포트 변경 실패.png>)

### 해결 과정
**원인 파악:** Port 20022 앞에 '#' 이 붙어 있어서 주석 처리된 상태로 포트 기본값인 22로 뜸
- 다시 vim에디터로 가서 #Port 20022에서 있던 #을 제거하고 저장후 다시 수행
```
vim /etc/ssh/sshd_config  # SSH 설정으로 다시 들어감
Port 20022                # 주석 처리 된 '#'을 제거함
PermitRootLogin no       # 주석 처리 된 '#'을 제거함

service ssh restart     # SSH 재시작
ss -tulnp | grep sshd   # 포트 및 설정 다시 확인
```
<img src="Screenshot/포트 변경 재수정.png" width="300" height="300" alt="포트 재수정"> <br>
<img src="Screenshot/SSH 재수행.png" alt="SSH 재수행">
---
## UFW 방화벽 설정하기
포트 2개 (20022와 15034) 허용 시도 실패 

도커 컨테이너에서 UFW가 iptables권한 거부 문제로 안됨

![alt text](<Screenshot/UFW 권한 거절.png>)
**⌘ iptable권한이란?** 컨테이너 내부에서 호스트 시스템의 네트워크 패킷 필터링 규칙을 조작할 수 있는 권한인데,
보안을 위해 격리 되어있기 때문에 시스템의 네트워크 설정을 바꿀 수 없으나 특정 옵션을 주어서 권한을 허용 할 수 있음 

현재 컨테이너에서 나가서 **--privileged옵션 추가**해서 다시 생성

```
# 컨테이너 밖(exit 하고 난뒤)에서 실행
docker rm -f mission             # 기존에 만들었던 mission 컨테이너 삭제

docker run -it --name mission \  # mission컨테이너에 privileged 옵션 추가
  --privileged \
  -p 20022:20022 \
  -p 15034:15034 \
  ubuntu:22.04 /bin/bash
```

<img src="Screenshot/컨테이너에 privileged 추가.png" alt="privileged 추가.png">

### 패키지 다시 설치
```
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
```
vim /etc/ssh/sshd_config    # SSH 다시 설정
Port 20022                  # 포트 20022로 변경
PermitRootLogin no          # 로그인 권한 옵션 no 변경

service ssh start           # SSH 시작
ss -tulnp | grep sshd       # 포트리슨 다시 확인
```
<img src="Screenshot/UFW 포트 권한 허용.png" alt="UFW 권한 허용">

## 계정 및 그룹 생성
```
# 계정 3개 생성
useradd -m -s /bin/bash agent-admin  # 운영/관리, cron 실행자
useradd -m -s /bin/bash agent-dev    # 개발/운영, monitor.sh 작성자
useradd -m -s /bin/bash agent-test   # QA/테스트
```
```
# 그룹 2개 생성
groupadd agent-common
groupadd agent-core
```
```
# 그룹에 계정 배정
# agent-common: admin, dev, test

usermod -aG agent-common agent-admin    # agent-common 배정
usermod -aG agent-common agent-dev      # agent-common 배정
usermod -aG agent-common agent-test     # agent-common 배정

# agent-core: admin, dev
usermod -aG agent-core agent-admin      # agent-core에 배정
usermod -aG agent-core agent-dev        # agent-core에 배정
```
<img src="Screenshot/계정 및 그룹 생성.png" alt="계정 및 그룹 생성">

## 그룹 배정 확인

```
# 잘 배정 되었는지 확인
id agent-admin
id agent-dev
id agent-test
```

<img src="Screenshot/그룹 배정 확인.png" alt="계정 및 그룹 생성">

### 디렉토리 구조 생성
```
mkdir -p /home/agent-admin/agent-app/upload_files
mkdir -p /home/agent-admin/agent-app/api_keys
mkdir -p /var/log/agent-app

- 디렉토리 구조
$AGENT_HOME
├── upload_files
├── api_keys
└──  
/var/log/agent-app
```

### 각 그룹마다 권한 설정
```
# upload_files: agent-common 그룹, R/W
chown -R agent-admin:agent-common /home/agent-admin/agent-app/upload_files
chmod 770 /home/agent-admin/agent-app/upload_files
```
```
# api_keys: agent-core 그룹, R/W
chown -R agent-admin:agent-core /home/agent-admin/agent-app/api_keys
chmod 770 /home/agent-admin/agent-app/api_keys
```
```
# /var/log/agent-app: agent-core 그룹, R/W
chown -R agent-admin:agent-core /var/log/agent-app
chmod 770 /var/log/agent-app
```
### 그룹 권한 확인 
```
ls -l /home/agent-admin/agent-app/
ls -l /var/log/agent-app
```
<img src="Screenshot/그룹 권한 확인.png" alt="그룹 권한 확인">

#### 권한 전체 확인표
| 디렉토리 경로 | 소유 그룹 | 권한(Permission) | 현재 상태 |
| :--- | :--- | :--- | :--- |
| `upload_files` | **agent-common** | `770` (drwxrwx---) | 정상 |
| `api_keys` | **agent-core** | `770` (drwxrwx---) | 정상 |
| `/var/log/agent-app` | - | - | 비어있음 (정상) |
---
## 앱 실행 환경 구성하기
```
# agent-admin 계정 환경 변수 설정
echo 'export AGENT_HOME=/home/agent-admin/agent-app' >> /home/agent-admin/.bashrc
echo 'export AGENT_PORT=15034' >> /home/agent-admin/.bashrc
echo 'export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files' >> /home/agent-admin/.bashrc
echo 'export AGENT_KEY_PATH=$AGENT_HOME/api_keys/t_secret.key' >> /home/agent-admin/.bashrc
echo 'export AGENT_LOG_DIR=/var/log/agent-app' >> /home/agent-admin/.bashrc
```

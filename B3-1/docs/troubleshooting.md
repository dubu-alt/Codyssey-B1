# 트러블슈팅 보고서

## 사례 1: EC2 인스턴스 생성 후 외부에서 웹 페이지 접속 불가

### 증상 (문제 상황)

EC2 인스턴스 생성 완료 후 `http://<퍼블릭IP>` 접속 시 브라우저에서 "사이트에 연결할 수 없음" 오류 발생. SSH 접속은 정상 동작.

### 원인 가설

외부 HTTP 접속이 안 되는 원인을 아래 순서로 점검:

1. **가설 A**: Security Group 인바운드에 HTTP(80) 규칙이 없음
2. **가설 B**: Nginx가 설치되지 않았거나 실행 중이지 않음
3. **가설 C**: Route Table에 IGW 경로가 누락됨
4. **가설 D**: 퍼블릭 IP가 할당되지 않음

### 검증 방법

**가설 A 검증 — Security Group 확인**:
```bash
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx --region ap-northeast-2 \
  --query 'SecurityGroups[0].IpPermissions'
```
결과: SSH(22)만 존재, HTTP(80) 규칙 없음 → **원인 확인**

**가설 B 검증 — Nginx 상태 확인** (SSH 접속 후):
```bash
sudo systemctl status nginx
# 출력: active (running) → Nginx는 정상 동작 중

curl http://localhost
# 출력: 200 OK, HTML 응답 → 내부 서빙 정상
```

### 조치 내용

Security Group에 HTTP 인바운드 규칙 추가:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp --port 80 \
  --cidr 0.0.0.0/0 \
  --region ap-northeast-2
```

### 결과

```bash
curl -s -o /dev/null -w "%{http_code}" http://<퍼블릭IP>/health
# 출력: 200

curl http://<퍼블릭IP>/health
# 출력: OK
```
외부에서 HTTP 접속 정상 확인.

### 재발 방지

- 인프라 구축 스크립트(`setup-infrastructure.sh`)에 SG 규칙 생성을 포함하여 수동 누락 방지
- 배포 후 자동 검증 단계 추가: `curl -f http://<IP>/health || echo "FAIL"`
- 점검 순서 체크리스트 정리: **라우팅 → SG → 퍼블릭 IP → 서버 프로세스** 순서로 확인

---

## 사례 2: SSH 접속 시 "Permission denied (publickey)" 오류

### 증상 (문제 상황)

```bash
ssh -i my-cloud-key.pem ubuntu@<퍼블릭IP>
# 출력: Permission denied (publickey).
```

### 원인 가설

1. **가설 A**: .pem 파일 권한이 너무 열려 있음 (644 등)
2. **가설 B**: 잘못된 사용자명 (ec2-user vs ubuntu)
3. **가설 C**: 키 페어가 인스턴스와 매칭되지 않음

### 검증 방법

**가설 A 검증**:
```bash
ls -la my-cloud-key.pem
# 출력: -rw-r--r--  (644) → 권한이 너무 개방됨
```
SSH는 프라이빗 키 파일의 권한이 400이 아니면 접속을 거부한다 → **원인 확인**

### 조치 내용

```bash
chmod 400 my-cloud-key.pem
ssh -i my-cloud-key.pem ubuntu@<퍼블릭IP>
```

### 결과

SSH 접속 성공. 정상적으로 인스턴스 셸 진입.

### 재발 방지

- `setup-infrastructure.sh` 스크립트에서 키 생성 직후 `chmod 400` 자동 실행
- Ubuntu AMI는 `ubuntu`, Amazon Linux AMI는 `ec2-user` 사용자명 — AMI별 사용자명 확인 필수

---

## 사례 3: IAM 권한 부족으로 EC2 인스턴스 생성 실패

### 증상 (문제 상황)

```bash
aws ec2 run-instances --image-id ami-xxx --instance-type t2.micro ...
# 출력: An error occurred (UnauthorizedOperation): You are not authorized to perform this operation.
```

### 원인 가설

1. **가설 A**: IAM 정책에 `ec2:RunInstances` 권한이 누락됨
2. **가설 B**: 리전 조건(Condition)이 잘못 설정됨

### 검증 방법

**가설 A 검증 — IAM 정책 시뮬레이션**:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::xxxx:user/cloud-lab-user \
  --action-names ec2:RunInstances \
  --query 'EvaluationResults[0].EvalDecision'
# 출력: "implicitDeny" → 권한 없음 확인
```

**IAM 정책 문서 확인**:
```bash
aws iam get-policy-version --policy-arn arn:aws:iam::xxxx:policy/CloudLabMinimalAccess \
  --version-id v1 --query 'PolicyVersion.Document'
```
결과: `ec2:RunInstances`가 Action 목록에 포함되어 있지만, Condition에 리전 제한이 `ec2:Region`으로 설정됨. `RunInstances`는 `ec2:Region` 조건 키를 지원하지 않는 일부 하위 리소스(네트워크 인터페이스 등)가 있어 부분 차단됨 → **원인 확인**

### 조치 내용

IAM 정책에서 `ec2:RunInstances`에 대한 Condition 블록을 제거하고, 대신 Resource ARN에 리전을 포함시켜 제한:
```json
{
  "Sid": "EC2Management",
  "Effect": "Allow",
  "Action": ["ec2:RunInstances", ...],
  "Resource": "arn:aws:ec2:ap-northeast-2:*:*"
}
```

### 결과

EC2 인스턴스 생성 성공. 서울 리전(ap-northeast-2) 외 리전에서는 여전히 차단됨.

### 재발 방지

- IAM 정책 작성 시 `aws iam simulate-principal-policy`로 사전 검증
- "권한을 무작정 올리지 않고" → 에러 메시지의 Action 이름과 Resource ARN을 확인하여 필요한 최소 범위만 추가
- IAM Policy Simulator 콘솔(https://policysim.aws.amazon.com)을 활용하여 시각적 검증

---

## 트러블슈팅 점검 순서 정리

외부 접속 실패 시 아래 순서로 점검:

```
1. 라우팅 확인
   └─ Route Table에 0.0.0.0/0 → IGW 경로 존재?

2. Security Group 확인
   └─ 인바운드에 해당 프로토콜/포트 허용?

3. 퍼블릭 IP / DNS 확인
   └─ 인스턴스에 퍼블릭 IP 할당?
   └─ Elastic IP 사용 시 연결(Associate) 상태?

4. 서버 프로세스 확인
   └─ Nginx 실행 중? (systemctl status nginx)
   └─ 로컬에서 응답? (curl localhost)

5. 로그 확인
   └─ /var/log/nginx/error.log
   └─ /var/log/syslog
   └─ VPC Flow Logs (활성화한 경우)
```

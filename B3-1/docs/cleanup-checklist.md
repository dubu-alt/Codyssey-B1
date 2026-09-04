# 리소스 정리 체크리스트

실습 종료 후 과금 방지를 위해 아래 순서대로 삭제한다. 순서가 중요하다 — 의존 관계가 있는 리소스는 먼저 삭제해야 상위 리소스를 삭제할 수 있다.

## 정리 순서 및 확인

### 1단계: 컴퓨트 리소스

| # | 리소스 | 확인 명령어 | 과금 요인 | 완료 |
|---|--------|-----------|----------|------|
| 1 | EC2 인스턴스 | `aws ec2 describe-instances --filters "Name=instance-state-name,Values=running,stopped" --region ap-northeast-2` | 실행 시간 기준 과금 (프리 티어 750시간/월 초과 시) | [ ] |
| 2 | EBS 볼륨 | `aws ec2 describe-volumes --filters "Name=status,Values=available" --region ap-northeast-2` | 미사용 볼륨도 GB당 월 과금 ($0.08/GB gp3) | [ ] |

### 2단계: 네트워크 리소스 (할당형)

| # | 리소스 | 확인 명령어 | 과금 요인 | 완료 |
|---|--------|-----------|----------|------|
| 3 | Elastic IP | `aws ec2 describe-addresses --region ap-northeast-2` | 인스턴스 미연결 상태 시 시간당 $0.005 | [ ] |
| 4 | NAT Gateway | `aws ec2 describe-nat-gateways --filter "Name=state,Values=available" --region ap-northeast-2` | 시간당 $0.045 + 데이터 전송 비용 (생성했다면) | [ ] |

### 3단계: 네트워크 인프라

| # | 리소스 | 확인 명령어 | 과금 요인 | 완료 |
|---|--------|-----------|----------|------|
| 5 | Internet Gateway | `aws ec2 describe-internet-gateways --region ap-northeast-2` | 무료이나 VPC 삭제 전 분리 필요 | [ ] |
| 6 | Subnet | `aws ec2 describe-subnets --filters "Name=tag:Name,Values=cloud-lab-*" --region ap-northeast-2` | 무료이나 VPC 삭제 전 삭제 필요 | [ ] |
| 7 | Route Table | `aws ec2 describe-route-tables --filters "Name=tag:Name,Values=cloud-lab-*" --region ap-northeast-2` | 무료이나 VPC 삭제 전 삭제 필요 | [ ] |
| 8 | Security Group | `aws ec2 describe-security-groups --filters "Name=tag:Name,Values=cloud-lab-*" --region ap-northeast-2` | 무료이나 VPC 삭제 전 삭제 필요 | [ ] |
| 9 | VPC | `aws ec2 describe-vpcs --filters "Name=tag:Name,Values=cloud-lab-*" --region ap-northeast-2` | 무료이나 하위 리소스 모두 삭제 후 삭제 가능 | [ ] |

### 4단계: 기타

| # | 리소스 | 확인 명령어 | 과금 요인 | 완료 |
|---|--------|-----------|----------|------|
| 10 | Key Pair | `aws ec2 describe-key-pairs --region ap-northeast-2` | 무료이나 보안상 삭제 권장 | [ ] |
| 11 | IAM 사용자/정책 | `aws iam list-users` | 무료이나 불필요한 접근 경로 제거 | [ ] |
| 12 | ELB/ALB | `aws elbv2 describe-load-balancers --region ap-northeast-2` | 시간당 과금 (생성했다면) | [ ] |
| 13 | RDS | `aws rds describe-db-instances --region ap-northeast-2` | 시간당 과금 (생성했다면) | [ ] |

### 5단계: 최종 확인

| # | 확인 항목 | 방법 | 완료 |
|---|----------|------|------|
| 14 | Billing Dashboard | [AWS Billing 콘솔](https://console.aws.amazon.com/billing/) 접속하여 예상 비용 $0 확인 | [ ] |
| 15 | 리전 확인 | 서울(ap-northeast-2) 외 다른 리전에 실수로 생성한 리소스 없는지 확인 | [ ] |

## 삭제 순서가 중요한 이유

EC2 → EIP → IGW → Subnet → RT → SG → VPC 순서를 지켜야 한다:

- EC2가 Subnet에 존재하면 Subnet 삭제 불가
- IGW가 VPC에 연결되어 있으면 VPC 삭제 불가
- SG가 인스턴스에 연결되어 있으면 SG 삭제 불가

역순(VPC부터)으로 삭제하면 의존성 에러(`DependencyViolation`)가 발생한다.

## 자동화

`cleanup-infrastructure.sh` 스크립트로 위 과정을 자동 실행할 수 있다:

```bash
chmod +x cleanup-infrastructure.sh
./cleanup-infrastructure.sh
```

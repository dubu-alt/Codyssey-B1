#!/bin/bash
# ============================================================
# AWS 클라우드 인프라 구축 스크립트
# Region: ap-northeast-2 (Seoul)
# 실행 전: AWS CLI 설정 완료 필수 (aws configure)
# ============================================================
set -euo pipefail

REGION="ap-northeast-2"
AZ="${REGION}a"
VPC_CIDR="10.0.0.0/16"
SUBNET_CIDR="10.0.1.0/24"
KEY_NAME="my-cloud-key"
INSTANCE_TYPE="t2.micro"
# Ubuntu 22.04 LTS AMI (ap-northeast-2) - 최신 AMI ID는 변경될 수 있음
AMI_ID="ami-0c9c942bd7bf113a2"

echo "===== [1/8] VPC 생성 ====="
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --region $REGION \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=cloud-lab-vpc}]" \
  --query 'Vpc.VpcId' --output text)
echo "VPC 생성 완료: $VPC_ID"

# DNS 호스트네임 활성화 (퍼블릭 IP 연결 시 필요)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}' --region $REGION

echo "===== [2/8] Internet Gateway 생성 및 연결 ====="
IGW_ID=$(aws ec2 create-internet-gateway \
  --region $REGION \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=cloud-lab-igw}]" \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
echo "IGW 생성 및 VPC 연결 완료: $IGW_ID"

echo "===== [3/8] Public Subnet 생성 ====="
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block $SUBNET_CIDR \
  --availability-zone $AZ \
  --region $REGION \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=cloud-lab-public-subnet}]" \
  --query 'Subnet.SubnetId' --output text)
# Subnet에서 생성되는 인스턴스에 자동으로 퍼블릭 IP 할당
aws ec2 modify-subnet-attribute --subnet-id $SUBNET_ID --map-public-ip-on-launch --region $REGION
echo "Public Subnet 생성 완료: $SUBNET_ID"

echo "===== [4/8] Route Table 생성 및 경로 추가 ====="
RTB_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --region $REGION \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=cloud-lab-public-rt}]" \
  --query 'RouteTable.RouteTableId' --output text)
# 기본 경로: 0.0.0.0/0 → IGW (외부 인터넷 통신용)
aws ec2 create-route --route-table-id $RTB_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $REGION
# Subnet에 Route Table 연결
aws ec2 associate-route-table --route-table-id $RTB_ID --subnet-id $SUBNET_ID --region $REGION > /dev/null
echo "Route Table 생성 및 Subnet 연결 완료: $RTB_ID"

echo "===== [5/8] Security Group 생성 ====="
SG_ID=$(aws ec2 create-security-group \
  --group-name cloud-lab-web-sg \
  --description "Web server SG - HTTP 80 open, SSH restricted" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' --output text)
aws ec2 create-tags --resources $SG_ID --tags Key=Name,Value=cloud-lab-web-sg --region $REGION

# HTTP 80: 전체 개방 (웹 서비스)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 80 \
  --cidr 0.0.0.0/0 \
  --region $REGION

# SSH 22: 개인 IP만 허용 (아래 MY_IP를 본인 IP로 변경)
MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 22 \
  --cidr "${MY_IP}/32" \
  --region $REGION

echo "Security Group 생성 완료: $SG_ID"
echo "  - HTTP 80: 0.0.0.0/0 (전체)"
echo "  - SSH 22: ${MY_IP}/32 (본인 IP)"

echo "===== [6/8] Key Pair 생성 ====="
aws ec2 create-key-pair \
  --key-name $KEY_NAME \
  --region $REGION \
  --query 'KeyMaterial' --output text > "${KEY_NAME}.pem"
chmod 400 "${KEY_NAME}.pem"
echo "Key Pair 생성 완료: ${KEY_NAME}.pem (안전한 곳에 보관하세요)"

echo "===== [7/8] EC2 인스턴스 생성 ====="
# User Data: Nginx 설치 + /health 엔드포인트 구성
USER_DATA=$(cat <<'USERDATA'
#!/bin/bash
apt-get update -y
apt-get install -y nginx

# /health 엔드포인트 설정
cat > /etc/nginx/sites-available/default << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html;
    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    location /health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
NGINX

# 기본 페이지 커스터마이징
cat > /var/www/html/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head><title>Cloud Lab</title></head>
<body>
<h1>Hello Cloud!</h1>
<p>AWS Cloud Infrastructure Lab - Successfully Deployed</p>
</body>
</html>
HTML

systemctl restart nginx
systemctl enable nginx
USERDATA
)

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --subnet-id $SUBNET_ID \
  --security-group-ids $SG_ID \
  --user-data "$USER_DATA" \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":8,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=cloud-lab-web-server}]" \
  --region $REGION \
  --query 'Instances[0].InstanceId' --output text)
echo "EC2 인스턴스 생성 중: $INSTANCE_ID"

echo "===== [8/8] 인스턴스 실행 대기 ====="
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $REGION \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "============================================"
echo "  인프라 구축 완료!"
echo "============================================"
echo "  VPC:      $VPC_ID"
echo "  Subnet:   $SUBNET_ID"
echo "  IGW:      $IGW_ID"
echo "  Route:    $RTB_ID"
echo "  SG:       $SG_ID"
echo "  EC2:      $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo ""
echo "  접속 확인 (1~2분 후):"
echo "    브라우저:  http://$PUBLIC_IP"
echo "    헬스체크:  curl http://$PUBLIC_IP/health"
echo "    SSH:      ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo "============================================"

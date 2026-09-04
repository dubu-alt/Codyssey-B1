#!/bin/bash
# ============================================================
# AWS 리소스 정리 스크립트 (과금 방지)
# 삭제 순서: EC2 → EIP → IGW → Subnet → Route Table → VPC
# ============================================================
set -euo pipefail

REGION="ap-northeast-2"

echo "===== 리소스 정리 시작 ====="
echo "⚠️  이 스크립트는 cloud-lab 태그가 붙은 모든 리소스를 삭제합니다."
read -p "계속하시겠습니까? (y/N): " confirm
[[ "$confirm" != "y" && "$confirm" != "Y" ]] && echo "취소됨" && exit 0

# 1. EC2 인스턴스 종료
echo "[1/6] EC2 인스턴스 종료..."
INSTANCE_IDS=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=cloud-lab-*" "Name=instance-state-name,Values=running,stopped" \
  --region $REGION \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$INSTANCE_IDS" ]; then
  aws ec2 terminate-instances --instance-ids $INSTANCE_IDS --region $REGION > /dev/null
  echo "  종료 대기 중: $INSTANCE_IDS"
  aws ec2 wait instance-terminated --instance-ids $INSTANCE_IDS --region $REGION
  echo "  ✅ EC2 종료 완료"
else
  echo "  ⏭️  삭제할 EC2 없음"
fi

# 2. Elastic IP 해제
echo "[2/6] Elastic IP 해제..."
EIP_ALLOCS=$(aws ec2 describe-addresses \
  --filters "Name=tag:Name,Values=cloud-lab-*" \
  --region $REGION \
  --query 'Addresses[].AllocationId' --output text)
if [ -n "$EIP_ALLOCS" ]; then
  for alloc in $EIP_ALLOCS; do
    aws ec2 release-address --allocation-id $alloc --region $REGION
    echo "  ✅ EIP 해제: $alloc"
  done
else
  echo "  ⏭️  해제할 EIP 없음"
fi

# 3. Internet Gateway 분리 및 삭제
echo "[3/6] Internet Gateway 삭제..."
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=cloud-lab-vpc" \
  --region $REGION \
  --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")
if [ -n "$VPC_ID" ] && [ "$VPC_ID" != "None" ]; then
  IGW_ID=$(aws ec2 describe-internet-gateways \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --region $REGION \
    --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null || echo "")
  if [ -n "$IGW_ID" ] && [ "$IGW_ID" != "None" ]; then
    aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
    aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region $REGION
    echo "  ✅ IGW 삭제: $IGW_ID"
  else
    echo "  ⏭️  삭제할 IGW 없음"
  fi

  # 4. Subnet 삭제
  echo "[4/6] Subnet 삭제..."
  SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=cloud-lab-*" \
    --region $REGION \
    --query 'Subnets[].SubnetId' --output text)
  if [ -n "$SUBNET_IDS" ]; then
    for subnet in $SUBNET_IDS; do
      aws ec2 delete-subnet --subnet-id $subnet --region $REGION
      echo "  ✅ Subnet 삭제: $subnet"
    done
  else
    echo "  ⏭️  삭제할 Subnet 없음"
  fi

  # 5. Route Table 삭제 (메인 RT 제외)
  echo "[5/6] Route Table 삭제..."
  RTB_IDS=$(aws ec2 describe-route-tables \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=cloud-lab-*" \
    --region $REGION \
    --query 'RouteTables[].RouteTableId' --output text)
  if [ -n "$RTB_IDS" ]; then
    for rtb in $RTB_IDS; do
      # 연결 해제
      ASSOC_IDS=$(aws ec2 describe-route-tables \
        --route-table-ids $rtb --region $REGION \
        --query 'RouteTables[0].Associations[?!Main].RouteTableAssociationId' --output text)
      for assoc in $ASSOC_IDS; do
        aws ec2 disassociate-route-table --association-id $assoc --region $REGION 2>/dev/null || true
      done
      aws ec2 delete-route-table --route-table-id $rtb --region $REGION
      echo "  ✅ Route Table 삭제: $rtb"
    done
  else
    echo "  ⏭️  삭제할 Route Table 없음"
  fi

  # 6. VPC 삭제
  echo "[6/6] VPC 삭제..."
  # SG 삭제 (기본 SG 제외)
  SG_IDS=$(aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --region $REGION \
    --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text)
  for sg in $SG_IDS; do
    aws ec2 delete-security-group --group-id $sg --region $REGION 2>/dev/null || true
  done
  aws ec2 delete-vpc --vpc-id $VPC_ID --region $REGION
  echo "  ✅ VPC 삭제: $VPC_ID"
else
  echo "  ⏭️  삭제할 VPC 없음"
fi

# 7. 미사용 EBS 볼륨 정리
echo "[추가] 미사용 EBS 볼륨 확인..."
UNUSED_VOLS=$(aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --region $REGION \
  --query 'Volumes[].VolumeId' --output text)
if [ -n "$UNUSED_VOLS" ]; then
  for vol in $UNUSED_VOLS; do
    aws ec2 delete-volume --volume-id $vol --region $REGION
    echo "  ✅ 미사용 EBS 삭제: $vol"
  done
else
  echo "  ⏭️  미사용 EBS 없음"
fi

# 8. Key Pair 삭제
echo "[추가] Key Pair 삭제..."
aws ec2 delete-key-pair --key-name my-cloud-key --region $REGION 2>/dev/null && \
  echo "  ✅ Key Pair 삭제 완료" || echo "  ⏭️  삭제할 Key Pair 없음"

echo ""
echo "============================================"
echo "  ✅ 리소스 정리 완료"
echo "  📌 Billing Dashboard에서 최종 확인하세요"
echo "     https://console.aws.amazon.com/billing/"
echo "============================================"

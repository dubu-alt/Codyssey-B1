#!/bin/bash
# ============================================================
# IAM 최소 권한 설정 스크립트
# 루트 계정이 아닌 IAM 사용자로 실습 환경 접근
# ============================================================
set -euo pipefail

IAM_USER="cloud-lab-user"
POLICY_NAME="CloudLabMinimalAccess"

echo "===== [1/3] IAM 정책 생성 (최소 권한) ====="
cat > /tmp/cloud-lab-policy.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2Management",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeImages",
        "ec2:DescribeKeyPairs",
        "ec2:CreateKeyPair",
        "ec2:DeleteKeyPair",
        "ec2:CreateTags",
        "ec2:DescribeTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:Region": "ap-northeast-2"
        }
      }
    },
    {
      "Sid": "VPCNetworking",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc",
        "ec2:DeleteVpc",
        "ec2:DescribeVpcs",
        "ec2:ModifyVpcAttribute",
        "ec2:CreateSubnet",
        "ec2:DeleteSubnet",
        "ec2:DescribeSubnets",
        "ec2:ModifySubnetAttribute",
        "ec2:CreateInternetGateway",
        "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway",
        "ec2:DetachInternetGateway",
        "ec2:DescribeInternetGateways",
        "ec2:CreateRouteTable",
        "ec2:DeleteRouteTable",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:AssociateRouteTable",
        "ec2:DisassociateRouteTable",
        "ec2:DescribeRouteTables"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecurityGroupManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSecurityGroup",
        "ec2:DeleteSecurityGroup",
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress",
        "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupEgress"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EBSManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVolumes",
        "ec2:DeleteVolume",
        "ec2:CreateVolume",
        "ec2:AttachVolume",
        "ec2:DetachVolume"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ElasticIPManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:DescribeAddresses",
        "ec2:AssociateAddress",
        "ec2:DisassociateAddress"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyBilling",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
POLICY

POLICY_ARN=$(aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document file:///tmp/cloud-lab-policy.json \
  --query 'Policy.Arn' --output text)
echo "IAM 정책 생성 완료: $POLICY_ARN"

echo "===== [2/3] IAM 사용자 생성 ====="
aws iam create-user --user-name $IAM_USER
aws iam attach-user-policy --user-name $IAM_USER --policy-arn $POLICY_ARN

# 콘솔 로그인 활성화
LOGIN_PROFILE=$(aws iam create-login-profile \
  --user-name $IAM_USER \
  --password "ChangeMe!2024#" \
  --password-reset-required)
echo "IAM 사용자 생성 완료: $IAM_USER"

echo "===== [3/3] 액세스 키 생성 (CLI용) ====="
ACCESS_KEY=$(aws iam create-access-key \
  --user-name $IAM_USER \
  --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text)
echo "액세스 키 생성 완료 (안전한 곳에 보관하세요):"
echo "$ACCESS_KEY"

ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

echo ""
echo "============================================"
echo "  IAM 설정 완료"
echo "============================================"
echo "  콘솔 로그인 URL: https://${ACCOUNT_ID}.signin.aws.amazon.com/console"
echo "  사용자명: $IAM_USER"
echo "  초기 비밀번호: ChangeMe!2024# (첫 로그인 시 변경 필수)"
echo "  정책: $POLICY_NAME (EC2/VPC/SG만 허용)"
echo ""
echo "  ⚠️  AdministratorAccess 미부여 확인"
echo "  ⚠️  S3, RDS 등 실습 외 서비스 접근 차단됨"
echo "============================================"

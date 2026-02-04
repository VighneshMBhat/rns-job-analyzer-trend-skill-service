# AWS Deployment Guide

## 📋 Prerequisites

1. AWS Account
2. AWS CLI installed
3. AWS SAM CLI installed

---

## 🔧 Step 1: Create New IAM User

### Go to AWS Console → IAM → Users → Create User

**User Name**: `trend-skill-deployer` (or any name you prefer)

### Attach Permissions (Create Custom Policy)

Create a new policy with this JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudFormationAccess",
            "Effect": "Allow",
            "Action": [
                "cloudformation:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "LambdaAccess",
            "Effect": "Allow",
            "Action": [
                "lambda:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "APIGatewayAccess",
            "Effect": "Allow",
            "Action": [
                "apigateway:*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMAccess",
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:GetRole",
                "iam:PassRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRolePolicy",
                "iam:TagRole",
                "iam:UntagRole"
            ],
            "Resource": "*"
        },
        {
            "Sid": "LogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Create Access Keys

After creating the user:
1. Go to **Security credentials** tab
2. Click **Create access key**
3. Choose **Command Line Interface (CLI)**
4. Download and save the Access Key ID and Secret Access Key

---

## 🔧 Step 2: Configure AWS CLI with New Profile

Open terminal and run:

```bash
aws configure --profile trend-skill-deployer
```

Enter:
- Access Key ID: `<your_access_key_id>`
- Secret Access Key: `<your_secret_access_key>`
- Default region: `us-east-1`
- Default output format: `json`

---

## 🚀 Step 3: Deploy to AWS Lambda

Navigate to the service directory:

```bash
cd d:\rns-job-analyzer\trend_skill_service
```

### Build the application:

```bash
sam build --profile trend-skill-deployer
```

### Deploy the application:

```bash
sam deploy --stack-name trend-skill-service ^
  --resolve-s3 ^
  --capabilities CAPABILITY_IAM ^
  --region us-east-1 ^
  --profile trend-skill-deployer ^
  --parameter-overrides ^
    SupabaseUrl="https://rokptxcawrmhqcmrsjca.supabase.co" ^
    SupabaseKey="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJva3B0eGNhd3JtaHFjbXJzamNhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAxOTUzNTUsImV4cCI6MjA4NTc3MTM1NX0.h-RQaxCQHahK4RgsROIF2nHe7LxN1Nd2YhXFn4o2IGc" ^
    SupabaseServiceRoleKey="YOUR_SERVICE_ROLE_KEY" ^
    SerpApiKey="YOUR_SERP_API_KEY" ^
    ApifyApiToken="YOUR_APIFY_TOKEN"
```

---

## ✅ Step 4: Get API Endpoint

After deployment, SAM will output the API Gateway URL:

```
TrendSkillServiceApi = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

Save this URL - this is your production API endpoint!

---

## 🔄 Step 5: Set Up Weekly CRON (Optional)

### Go to AWS Console → EventBridge → Rules → Create Rule

1. **Name**: `trend-skill-weekly-collection`
2. **Schedule expression**: `cron(0 0 ? * SUN *)` (Every Sunday at midnight UTC)
3. **Target**: Lambda function `trend-skill-service-TrendSkillServiceFunction`
4. **Configure input**: Constant (JSON text)

```json
{
    "httpMethod": "POST",
    "path": "/api/cron/run-full",
    "body": "{}"
}
```

---

## 📊 Monitoring

### View Logs:

```bash
sam logs --stack-name trend-skill-service --profile trend-skill-deployer --tail
```

### View in CloudWatch:

AWS Console → CloudWatch → Log Groups → `/aws/lambda/trend-skill-service-TrendSkillServiceFunction`

---

## 🗑️ Cleanup (If needed)

To delete the stack:

```bash
sam delete --stack-name trend-skill-service --profile trend-skill-deployer
```

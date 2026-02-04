# AWS EventBridge CRON Setup - Step by Step Guide

This guide shows how to set up weekly CRON jobs for both services.

---

## 📋 Lambda Functions We Need to Schedule

| Service | Lambda ARN |
|---------|------------|
| **Trend Skill Service** | `arn:aws:lambda:us-east-1:497927597469:function:trend-skill-service-TrendSkillServiceFunction-8tuTaNa43elV` |
| **GitHub Service** | `arn:aws:lambda:us-east-1:497927597469:function:github-service-GithubServiceFunction-wGtVkNqGeSDL` |

---

# CRON Job 1: Trend Skill Service (Weekly Data Collection)

### Step 1: Open EventBridge Scheduler

1. Go to: **https://us-east-1.console.aws.amazon.com/scheduler/home?region=us-east-1#schedules**
2. Or: AWS Console → Search "EventBridge Scheduler" → Click "Schedules"

### Step 2: Click "Create schedule"

Click the **"Create schedule"** button (orange button)

### Step 3: Specify schedule detail

| Field | Value |
|-------|-------|
| **Schedule name** | `trend-skill-weekly-collection` |
| **Description** | `Weekly job and Reddit discussion collection` |
| **Schedule group** | `default` |

### Step 4: Define the schedule

| Field | Value |
|-------|-------|
| **Occurrence** | ✅ Select **Recurring schedule** |
| **Schedule type** | ✅ Select **Cron-based schedule** |
| **Cron expression** | `0 0 ? * SUN *` |
| **Flexible time window** | Select **Off** |

> **Cron explanation**: `0 0 ? * SUN *` = Every Sunday at 00:00 UTC (5:30 AM IST)

### Step 5: Click "Next"

### Step 6: Select target

| Field | Value |
|-------|-------|
| **Target API** | Select **AWS Lambda → Invoke** |
| **Lambda function** | Select `trend-skill-service-TrendSkillServiceFunction-8tuTaNa43elV` |

### Step 7: Configure the input (Payload)

Click **"Additional settings"** (expand it)

For **Input**, paste this JSON:

```json
{
    "resource": "/api/cron/run-full",
    "path": "/api/cron/run-full",
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json"
    },
    "queryStringParameters": null,
    "body": null,
    "isBase64Encoded": false,
    "requestContext": {
        "resourcePath": "/api/cron/run-full",
        "httpMethod": "POST"
    }
}
```

### Step 8: Click "Next"

### Step 9: Configure settings (Optional)

| Field | Value |
|-------|-------|
| **Action after schedule completion** | NONE (keep it running) |
| **Retry policy** | Enable (default settings are fine) |
| **Dead-letter queue** | None |

### Step 10: Click "Next"

### Step 11: Review and create

1. Review all settings
2. Click **"Create schedule"**

### ✅ DONE for Trend Skill Service!

---

# CRON Job 2: GitHub Service (Weekly Skill Extraction)

### Step 1: Open EventBridge Scheduler

1. Go to: **https://us-east-1.console.aws.amazon.com/scheduler/home?region=us-east-1#schedules**
2. Click **"Create schedule"**

### Step 2: Specify schedule detail

| Field | Value |
|-------|-------|
| **Schedule name** | `github-skill-weekly-sync` |
| **Description** | `Weekly GitHub repo sync and skill extraction` |
| **Schedule group** | `default` |

### Step 3: Define the schedule

| Field | Value |
|-------|-------|
| **Occurrence** | ✅ Select **Recurring schedule** |
| **Schedule type** | ✅ Select **Cron-based schedule** |
| **Cron expression** | `0 2 ? * SUN *` |
| **Flexible time window** | Select **Off** |

> **Cron explanation**: `0 2 ? * SUN *` = Every Sunday at 02:00 UTC (7:30 AM IST)
> 
> This runs 2 hours AFTER the trend service to avoid overlap.

### Step 4: Click "Next"

### Step 5: Select target

| Field | Value |
|-------|-------|
| **Target API** | Select **AWS Lambda → Invoke** |
| **Lambda function** | Select `github-service-GithubServiceFunction-wGtVkNqGeSDL` |

### Step 6: Configure the input (Payload)

Click **"Additional settings"** (expand it)

For **Input**, paste this JSON:

```json
{
    "resource": "/api/github/sync/cron/run",
    "path": "/api/github/sync/cron/run",
    "httpMethod": "POST",
    "headers": {
        "Content-Type": "application/json"
    },
    "queryStringParameters": null,
    "body": null,
    "isBase64Encoded": false,
    "requestContext": {
        "resourcePath": "/api/github/sync/cron/run",
        "httpMethod": "POST"
    }
}
```

### Step 7: Click "Next"

### Step 8: Configure settings

| Field | Value |
|-------|-------|
| **Action after schedule completion** | NONE |
| **Retry policy** | Enable |
| **Dead-letter queue** | None |

### Step 9: Click "Next"

### Step 10: Review and create

1. Review all settings
2. Click **"Create schedule"**

### ✅ DONE for GitHub Service!

---

# 📊 Summary of CRON Jobs

| Schedule Name | CRON Expression | Time (UTC) | Time (IST) | What It Does |
|---------------|-----------------|------------|------------|--------------|
| `trend-skill-weekly-collection` | `0 0 ? * SUN *` | Sunday 00:00 | Sunday 05:30 | Collects jobs & Reddit discussions |
| `github-skill-weekly-sync` | `0 2 ? * SUN *` | Sunday 02:00 | Sunday 07:30 | Syncs GitHub repos, extracts skills |

---

# 🧪 Testing the CRON Jobs Manually

You can test the CRON jobs without waiting for Sunday:

### Test Trend Skill Service:
```bash
curl -X POST https://mi9j34716l.execute-api.us-east-1.amazonaws.com/Prod/api/cron/run-full
```

### Test GitHub Service:
```bash
curl -X POST https://12dbzw94lh.execute-api.us-east-1.amazonaws.com/Prod/api/github/sync/cron/run
```

---

# ❓ Troubleshooting

### If schedule doesn't trigger:

1. Check CloudWatch Logs:
   - AWS Console → CloudWatch → Log Groups
   - Look for `/aws/lambda/trend-skill-service-*` or `/aws/lambda/github-service-*`

2. Check EventBridge metrics:
   - AWS Console → EventBridge → Schedules → Click on schedule → View metrics

3. Verify IAM permissions:
   - The scheduler needs permission to invoke Lambda
   - EventBridge usually creates this automatically

---

# 📝 Quick Reference Links

| Resource | Link |
|----------|------|
| EventBridge Scheduler | https://us-east-1.console.aws.amazon.com/scheduler/home?region=us-east-1#schedules |
| Trend Skill Lambda Logs | https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Ftrend-skill-service-TrendSkillServiceFunction |
| GitHub Service Lambda Logs | https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Fgithub-service-GithubServiceFunction |

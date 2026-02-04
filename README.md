# Trend & Skill Data Collection Service

## Overview

This service collects and stores:
1. **Job Listings** from Google Jobs via SERP API
2. **Skill Discussions** from Reddit via Apify

It **only collects data** - no AI analysis. That's handled by a separate consumer service.

---

## 🔑 How to Get API Keys

### 1. SERP API Key (for Google Jobs)

**Website**: [https://serpapi.com/](https://serpapi.com/)

**Steps**:
1. Go to [serpapi.com](https://serpapi.com/)
2. Click **"Get Free API Key"** or **"Sign Up"**
3. Create an account (you can use Google/GitHub OAuth)
4. After signup, go to **Dashboard** → **API Key**
5. Copy your API key

**Free Tier**:
- 100 searches/month free
- No credit card required
- Valid for Google Jobs, Google Search, etc.

**Usage in this service**:
- 1 search = 1 job role query
- ~15 job roles × 1 weekly run = 15 searches/week = ~60/month

---

### 2. Apify API Token (for Reddit)

**Website**: [https://apify.com/](https://apify.com/)

**Steps**:
1. Go to [apify.com](https://apify.com/)
2. Click **"Start for free"** or **"Sign Up"**
3. Create an account
4. After login, click your profile icon → **Settings** → **Integrations**
5. Or go directly to: [https://console.apify.com/account/integrations](https://console.apify.com/account/integrations)
6. Copy your **Personal API Token**

**Free Tier**:
- $5 free credits/month (enough for ~500-1000 Reddit posts)
- No credit card required
- Uses the Reddit Scraper actor: `trudax/reddit-scraper`

**Usage in this service**:
- ~10 queries × 15 posts = 150 posts/week
- Well within free tier

---

## 📁 Project Structure

```
trend_skill_service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Configuration
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── serp_collector.py      # Google Jobs fetcher
│   │   └── apify_collector.py     # Reddit fetcher
│   ├── services/
│   │   ├── __init__.py
│   │   ├── persistence_service.py # Database storage
│   │   └── normalizer_service.py  # Skill extraction
│   └── routers/
│       ├── __init__.py
│       ├── jobs.py                # Job endpoints
│       ├── discussions.py         # Discussion endpoints
│       └── cron.py                # Scheduled collection
├── .env                           # Environment variables
├── requirements.txt
└── template.yaml                  # AWS SAM template
```

---

## ⚙️ Environment Variables

After getting your API keys, update `.env`:

```env
# Server Config
HOST_URL=http://localhost:8002

# Supabase Config (already set)
SUPABASE_URL=https://rokptxcawrmhqcmrsjca.supabase.co
SUPABASE_KEY=<anon_key>
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>

# SERP API (Get from https://serpapi.com/)
SERP_API_KEY=paste_your_serp_api_key_here

# Apify API (Get from https://apify.com/)
APIFY_API_TOKEN=paste_your_apify_token_here
```

---

## 🗄️ Database Tables Created

| Table | Purpose |
|-------|---------|
| `fetched_jobs` | Raw job listings from Google Jobs |
| `fetched_discussions` | Raw Reddit posts |
| `job_extracted_skills` | Skills extracted from job descriptions |
| `skill_trends` | Aggregated skill popularity over time |

---

## 📡 API Endpoints

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs/fetch` | Fetch jobs for a single query |
| POST | `/api/jobs/fetch-batch` | Fetch jobs for multiple queries |
| GET | `/api/jobs/stats` | Get job storage statistics |
| POST | `/api/jobs/extract-skills/{job_id}` | Extract skills from a job |

### Discussions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/discussions/fetch` | Fetch Reddit posts for a query |
| POST | `/api/discussions/fetch-batch` | Fetch for multiple queries |
| GET | `/api/discussions/stats` | Get discussion statistics |

### Cron (Scheduled Collection)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cron/run-jobs` | Run weekly job collection |
| POST | `/api/cron/run-discussions` | Run weekly discussion collection |
| POST | `/api/cron/run-full` | Run both jobs + discussions |
| POST | `/api/cron/aggregate-trends` | Create skill trend snapshot |
| GET | `/api/cron/config` | Get current cron configuration |

---

## 🚀 Local Development

```bash
cd trend_skill_service

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## ☁️ AWS Deployment

```bash
cd trend_skill_service

# Build
sam build --profile rns-auth

# Deploy
sam deploy --stack-name trend-skill-service \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --profile rns-auth \
  --parameter-overrides \
    SupabaseUrl="https://rokptxcawrmhqcmrsjca.supabase.co" \
    SupabaseKey="<anon_key>" \
    SupabaseServiceRoleKey="<service_role_key>" \
    SerpApiKey="<your_serp_api_key>" \
    ApifyApiToken="<your_apify_token>"
```

---

## 🔄 Weekly Cron Setup

After deployment, set up AWS EventBridge to trigger weekly:

1. Go to AWS Console → EventBridge → Rules
2. Create rule:
   - Schedule: `cron(0 0 ? * SUN *)` (Every Sunday at midnight UTC)
   - Target: Lambda function `trend-skill-service-TrendSkillServiceFunction`
   - Input: `{"path": "/api/cron/run-full", "httpMethod": "POST"}`

---

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULER (Weekly)                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌───────────────────────┐               ┌───────────────────────┐
│   SERP API            │               │   APIFY API           │
│   (Google Jobs)       │               │   (Reddit Scraper)    │
└───────────────────────┘               └───────────────────────┘
        │                                           │
        ▼                                           ▼
┌───────────────────────┐               ┌───────────────────────┐
│   Job Normalization   │               │   Post Normalization  │
│   + Deduplication     │               │   + Deduplication     │
└───────────────────────┘               └───────────────────────┘
        │                                           │
        ▼                                           ▼
┌───────────────────────┐               ┌───────────────────────┐
│   fetched_jobs        │               │   fetched_discussions │
│   (Supabase)          │               │   (Supabase)          │
└───────────────────────┘               └───────────────────────┘
        │                                           │
        └─────────────────────┬─────────────────────┘
                              ▼
                ┌───────────────────────┐
                │   Skill Extraction    │
                │   (Keyword Matching)  │
                └───────────────────────┘
                              │
                              ▼
                ┌───────────────────────┐
                │   skill_trends        │
                │   (Supabase)          │
                └───────────────────────┘
                              │
                              ▼
                ┌───────────────────────┐
                │   Future AI Consumer  │
                │   (Skill Gap Analysis)│
                └───────────────────────┘
```

---

## ✅ Summary

| Step | Action |
|------|--------|
| 1 | Get SERP API key from serpapi.com |
| 2 | Get Apify token from apify.com |
| 3 | Update `.env` with both keys |
| 4 | Deploy to AWS Lambda |
| 5 | Set up weekly EventBridge trigger |

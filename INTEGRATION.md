# Trend & Skill Data Collection Service - Frontend Integration Guide

## 🔗 Service Overview

This service collects job listings and Reddit discussions for skill trend analysis.

**Repository**: [https://github.com/VighneshMBhat/rns-job-analyzer-trend-skill-service](https://github.com/VighneshMBhat/rns-job-analyzer-trend-skill-service)

---

## 🌐 API Base URL

| Environment | Base URL |
|-------------|----------|
| **Production** | `https://<API_GATEWAY_ID>.execute-api.us-east-1.amazonaws.com/Prod` |
| **Local** | `http://localhost:8002` |

> **Note**: The production URL will be provided after AWS deployment.

---

## 📡 API Endpoints

### 1. Jobs Endpoints

#### Fetch Jobs (Single Query)
```http
POST /api/jobs/fetch
Content-Type: application/json

{
    "query": "Python Developer",
    "location": "United States",
    "num_results": 10
}
```

**Response:**
```json
{
    "status": "success",
    "query": "Python Developer",
    "jobs_fetched": 10,
    "storage_result": {
        "inserted": 10,
        "skipped": 0,
        "errors": 0,
        "total": 10
    }
}
```

#### Fetch Jobs (Batch)
```http
POST /api/jobs/fetch-batch
Content-Type: application/json

{
    "queries": ["React Developer", "Node.js Developer", "DevOps Engineer"],
    "location": "United States",
    "num_per_query": 5
}
```

#### Get Job Statistics
```http
GET /api/jobs/stats
```

**Response:**
```json
{
    "total_jobs": 150,
    "recent_jobs": 25
}
```

---

### 2. Discussions Endpoints

#### Fetch Reddit Discussions
```http
POST /api/discussions/fetch
Content-Type: application/json

{
    "query": "Python developer career",
    "max_items": 20,
    "sort": "relevance"
}
```

**Response:**
```json
{
    "status": "success",
    "query": "Python developer career",
    "subreddits": ["programming", "learnprogramming", "cscareerquestions", ...],
    "discussions_fetched": 20,
    "storage_result": {
        "inserted": 20,
        "skipped": 0,
        "errors": 0,
        "total": 20
    }
}
```

#### Fetch Hot Posts from a Subreddit
```http
POST /api/discussions/fetch-hot/{subreddit}?limit=25
```

Example: `POST /api/discussions/fetch-hot/cscareerquestions?limit=25`

#### Get Discussion Statistics
```http
GET /api/discussions/stats
```

---

### 3. CRON Endpoints (Scheduled Collection)

#### Run Full Weekly Collection
```http
POST /api/cron/run-full
```

**Response:**
```json
{
    "status": "completed",
    "jobs": {
        "queries_processed": 15,
        "jobs_fetched": 150,
        "storage_result": {...}
    },
    "discussions": {
        "queries_processed": 10,
        "discussions_fetched": 100,
        "storage_result": {...}
    }
}
```

#### Run Only Jobs Collection
```http
POST /api/cron/run-jobs
```

#### Run Only Discussions Collection
```http
POST /api/cron/run-discussions
```

#### Aggregate Skill Trends
```http
POST /api/cron/aggregate-trends
```

**Response:**
```json
{
    "status": "completed",
    "snapshot_date": "2026-02-05",
    "unique_skills": 45,
    "update_result": {
        "inserted": 30,
        "updated": 15,
        "errors": 0
    }
}
```

#### Get CRON Configuration
```http
GET /api/cron/config
```

---

### 4. Health Check
```http
GET /
```

**Response:**
```json
{
    "service": "Trend & Skill Data Collection Service",
    "version": "1.0.0",
    "status": "running",
    "endpoints": {
        "jobs": "/api/jobs",
        "discussions": "/api/discussions",
        "cron": "/api/cron"
    }
}
```

---

## 🗄️ Database Schema

### `fetched_jobs` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `job_hash` | TEXT | Unique hash for deduplication |
| `title` | TEXT | Job title |
| `company_name` | TEXT | Company name |
| `location` | TEXT | Job location |
| `description` | TEXT | Job description |
| `posted_date` | TEXT | When job was posted |
| `salary_text` | TEXT | Salary information |
| `job_url` | TEXT | URL to job listing |
| `apply_url` | TEXT | URL to apply |
| `source` | TEXT | Data source (serp_google_jobs) |
| `work_type` | TEXT | Remote/onsite/hybrid |
| `experience_level` | TEXT | Junior/Mid/Senior |
| `fetched_at` | TIMESTAMPTZ | When data was fetched |

### `fetched_discussions` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `post_hash` | TEXT | Unique hash for deduplication |
| `post_id` | TEXT | Reddit post ID |
| `title` | TEXT | Post title |
| `body` | TEXT | Post content |
| `subreddit` | TEXT | Subreddit name |
| `author` | TEXT | Reddit username |
| `upvotes` | INTEGER | Upvote count |
| `comments_count` | INTEGER | Number of comments |
| `post_url` | TEXT | URL to post |
| `created_utc` | TIMESTAMPTZ | When post was created |
| `source` | TEXT | Data source (reddit_api) |
| `search_query` | TEXT | Query used to find this |
| `fetched_at` | TIMESTAMPTZ | When data was fetched |

### `skill_trends` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `snapshot_date` | DATE | Date of the snapshot |
| `skill_name` | TEXT | Skill name |
| `skill_name_normalized` | TEXT | Lowercase normalized name |
| `job_mention_count` | INTEGER | Mentions in job listings |
| `discussion_mention_count` | INTEGER | Mentions in discussions |
| `trend_direction` | TEXT | up/down/stable |

---

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SCHEDULER (Weekly)                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌───────────────────────┐               ┌───────────────────────┐
│   SERP API            │               │   Reddit JSON API     │
│   (Google Jobs)       │               │   (Public & Free)     │
└───────────────────────┘               └───────────────────────┘
        │                                           │
        ▼                                           ▼
┌───────────────────────────────────────────────────────────────┐
│                      SUPABASE                                  │
│  ┌──────────────┐ ┌──────────────────┐ ┌──────────────────┐  │
│  │ fetched_jobs │ │ fetched_discussions│ │  skill_trends   │  │
│  └──────────────┘ └──────────────────┘ └──────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                    AI ANALYSIS SERVICE                         │
│            (Future - Skill Gap Analysis)                       │
└───────────────────────────────────────────────────────────────┘
```

---

## 📊 Frontend Integration Examples

### 1. Fetching Skill Trends (React/TypeScript)

```typescript
interface SkillTrend {
  id: string;
  skill_name: string;
  job_mention_count: number;
  discussion_mention_count: number;
  trend_direction: 'up' | 'down' | 'stable';
  snapshot_date: string;
}

// Fetch trends from Supabase directly
const fetchSkillTrends = async () => {
  const { data, error } = await supabase
    .from('skill_trends')
    .select('*')
    .order('job_mention_count', { ascending: false })
    .limit(20);
  
  return data as SkillTrend[];
};
```

### 2. Fetching Latest Jobs

```typescript
interface FetchedJob {
  id: string;
  title: string;
  company_name: string;
  location: string;
  description: string;
  salary_text: string;
  job_url: string;
  apply_url: string;
  fetched_at: string;
}

const fetchLatestJobs = async (limit = 50) => {
  const { data, error } = await supabase
    .from('fetched_jobs')
    .select('*')
    .order('fetched_at', { ascending: false })
    .limit(limit);
  
  return data as FetchedJob[];
};
```

### 3. Fetching Discussions

```typescript
interface FetchedDiscussion {
  id: string;
  title: string;
  body: string;
  subreddit: string;
  upvotes: number;
  comments_count: number;
  post_url: string;
}

const fetchDiscussions = async (limit = 50) => {
  const { data, error } = await supabase
    .from('fetched_discussions')
    .select('*')
    .order('upvotes', { ascending: false })
    .limit(limit);
  
  return data as FetchedDiscussion[];
};
```

### 4. Triggering Data Collection (Admin Only)

```typescript
const triggerDataCollection = async (baseUrl: string) => {
  const response = await fetch(`${baseUrl}/api/cron/run-full`, {
    method: 'POST'
  });
  return response.json();
};
```

---

## 🔒 Security Notes

1. **No Authentication Required**: This service doesn't require user authentication
2. **Public Data**: All data collected is from public sources (Google Jobs, Reddit)
3. **Rate Limiting**: Reddit API has rate limits (~60 requests/minute)
4. **SERP API Credits**: SERP API has 100 free searches/month

---

## 📅 Recommended Usage

| Operation | Frequency | Endpoint |
|-----------|-----------|----------|
| Full Collection | Weekly (Sundays) | `POST /api/cron/run-full` |
| Skill Aggregation | After collection | `POST /api/cron/aggregate-trends` |
| Manual Job Search | As needed | `POST /api/jobs/fetch` |
| Manual Discussion Search | As needed | `POST /api/discussions/fetch` |

---

## 🚀 Quick Start for Frontend

1. **Read data directly from Supabase** for displaying:
   - `fetched_jobs` - Latest job listings
   - `fetched_discussions` - Reddit discussions
   - `skill_trends` - Aggregated skill popularity

2. **Call the API** only for:
   - Triggering new data collection
   - Admin operations

3. **Supabase Project**: `rokptxcawrmhqcmrsjca`

---

## 📞 Contact

For any questions about this service, contact the backend team.

**GitHub Repository**: [rns-job-analyzer-trend-skill-service](https://github.com/VighneshMBhat/rns-job-analyzer-trend-skill-service)

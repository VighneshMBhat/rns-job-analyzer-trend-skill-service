# Trend & Skill Data Collection Service - Frontend Integration Guide

## 🔗 What This Service Does

This is a **backend-only CRON service** that runs automatically on a weekly schedule. It:

1. ✅ Collects job listings from Google Jobs
2. ✅ Collects discussions from Reddit
3. ✅ Stores everything in Supabase
4. ✅ Aggregates skill trends

**⚠️ IMPORTANT: The frontend does NOT call this service's API directly!**

---

## 🔄 How It Works

```
┌──────────────────────────────────────────────────────────────┐
│            TREND SKILL SERVICE (This Service)                 │
│                     Runs Weekly via AWS EventBridge          │
│                                                               │
│  1. Fetches Google Jobs via SERP API                         │
│  2. Fetches Reddit discussions                               │
│  3. Extracts skills from job descriptions                    │
│  4. Stores all data in Supabase                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    SUPABASE      │
                    │                  │
                    │  fetched_jobs    │
                    │  fetched_discus. │
                    │  skill_trends    │
                    └──────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                     YOUR FRONTEND                             │
│                                                               │
│  - Reads DIRECTLY from Supabase using Supabase client        │
│  - NO API calls to this service needed                       │
│  - Just query the database tables                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 What the Frontend Should Do

### Query Supabase Directly

The frontend should use the Supabase client to read from these tables:

| Table | Purpose | Frontend Usage |
|-------|---------|----------------|
| `fetched_jobs` | Job listings | Display job trends, latest jobs |
| `fetched_discussions` | Reddit posts | Show skill discussions |
| `skill_trends` | Aggregated skills | Show skill popularity charts |

---

## 🗄️ Database Tables & Queries

### Supabase Project: `rokptxcawrmhqcmrsjca`

### 1. Get Latest Jobs

```typescript
const { data: jobs } = await supabase
  .from('fetched_jobs')
  .select('id, title, company_name, location, salary_text, job_url, apply_url, fetched_at')
  .order('fetched_at', { ascending: false })
  .limit(50);
```

### 2. Get Reddit Discussions

```typescript
const { data: discussions } = await supabase
  .from('fetched_discussions')
  .select('id, title, subreddit, upvotes, comments_count, post_url')
  .order('upvotes', { ascending: false })
  .limit(50);
```

### 3. Get Skill Trends (Most Popular Skills)

```typescript
const { data: trends } = await supabase
  .from('skill_trends')
  .select('skill_name, job_mention_count, discussion_mention_count, trend_direction')
  .order('job_mention_count', { ascending: false })
  .limit(20);
```

### 4. Search Jobs by Skill

```typescript
const { data: pythonJobs } = await supabase
  .from('fetched_jobs')
  .select('*')
  .ilike('description', '%python%')
  .order('fetched_at', { ascending: false })
  .limit(20);
```

---

## 📈 Example: Display Skill Popularity Chart

```typescript
// Fetch top 10 skills by job mentions
const fetchTopSkills = async () => {
  const { data, error } = await supabase
    .from('skill_trends')
    .select('skill_name, job_mention_count, discussion_mention_count')
    .order('job_mention_count', { ascending: false })
    .limit(10);
  
  if (error) throw error;
  
  // Format for chart library (e.g., Chart.js, Recharts)
  return data.map(skill => ({
    name: skill.skill_name,
    jobs: skill.job_mention_count,
    discussions: skill.discussion_mention_count
  }));
};
```

---

## 🗂️ Database Schema Reference

### `fetched_jobs` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `title` | TEXT | Job title |
| `company_name` | TEXT | Company name |
| `location` | TEXT | Job location |
| `description` | TEXT | Full job description |
| `salary_text` | TEXT | Salary info (if available) |
| `job_url` | TEXT | Link to job listing |
| `apply_url` | TEXT | Direct apply link |
| `work_type` | TEXT | Remote/onsite/hybrid |
| `fetched_at` | TIMESTAMPTZ | When job was collected |

### `fetched_discussions` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `title` | TEXT | Post title |
| `body` | TEXT | Post content |
| `subreddit` | TEXT | Subreddit name |
| `author` | TEXT | Reddit username |
| `upvotes` | INTEGER | Post score |
| `comments_count` | INTEGER | Number of comments |
| `post_url` | TEXT | Link to Reddit post |
| `search_query` | TEXT | Query that found this |
| `fetched_at` | TIMESTAMPTZ | When collected |

### `skill_trends` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `snapshot_date` | DATE | Date of snapshot |
| `skill_name` | TEXT | Skill name (e.g., "Python") |
| `job_mention_count` | INTEGER | Times mentioned in jobs |
| `discussion_mention_count` | INTEGER | Times in discussions |
| `trend_direction` | TEXT | up/down/stable |

---

## ✅ Summary for Frontend Developer

1. **Don't call this service's API** - it's a CRON job, not a user-facing API
2. **Query Supabase directly** using the Supabase client
3. **Tables to use**:
   - `fetched_jobs` - for job listings
   - `fetched_discussions` - for Reddit posts
   - `skill_trends` - for skill popularity data
4. **Data is refreshed weekly** automatically

---

## 🔗 Resources

- **Supabase Project ID**: `rokptxcawrmhqcmrsjca`
- **Supabase Dashboard**: [https://supabase.com/dashboard/project/rokptxcawrmhqcmrsjca](https://supabase.com/dashboard/project/rokptxcawrmhqcmrsjca)
- **GitHub Repository**: [https://github.com/VighneshMBhat/rns-job-analyzer-trend-skill-service](https://github.com/VighneshMBhat/rns-job-analyzer-trend-skill-service)
- **Production API URL**: `https://mi9j34716l.execute-api.us-east-1.amazonaws.com/Prod/`

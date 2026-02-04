"""
Cron Router - Scheduled job endpoints for weekly data collection.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.collectors.serp_collector import fetch_jobs_batch
from app.collectors.reddit_collector import fetch_discussions_batch
from app.services.persistence_service import store_jobs, store_discussions, update_skill_trends
from app.services.normalizer_service import extract_skills_from_text
import requests
from app.core.config import settings
from collections import Counter

router = APIRouter()

SUPABASE_REST_URL = f"{settings.SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "Content-Type": "application/json"
}


# Default job role queries
DEFAULT_JOB_QUERIES = [
    "Software Developer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Data Engineer",
    "Mobile Developer",
    "Python Developer",
    "Java Developer",
    "JavaScript Developer",
    "React Developer",
    "Node.js Developer"
]

# Default skill trend queries for Reddit
DEFAULT_SKILL_QUERIES = [
    "programming skills 2026",
    "software developer skills",
    "backend developer technologies",
    "frontend framework comparison",
    "cloud certification worth it",
    "machine learning career",
    "kubernetes docker devops",
    "react angular vue comparison",
    "python vs javascript",
    "AI developer jobs"
]


@router.post("/run-jobs")
def run_jobs_collection():
    """
    Run weekly job collection cron.
    Fetches jobs for all default queries and stores them.
    """
    try:
        print(f"Starting job collection at {datetime.now(timezone.utc)}")
        
        jobs = fetch_jobs_batch(
            queries=DEFAULT_JOB_QUERIES,
            location="United States",
            num_per_query=10
        )
        
        result = store_jobs(jobs)
        
        return {
            "status": "completed",
            "queries_processed": len(DEFAULT_JOB_QUERIES),
            "jobs_fetched": len(jobs),
            "storage_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-discussions")
def run_discussions_collection():
    """
    Run weekly discussion collection cron.
    Fetches Reddit posts for skill trend queries.
    """
    try:
        print(f"Starting discussion collection at {datetime.now(timezone.utc)}")
        
        discussions = fetch_discussions_batch(
            queries=DEFAULT_SKILL_QUERIES,
            max_per_query=15
        )
        
        result = store_discussions(discussions)
        
        return {
            "status": "completed",
            "queries_processed": len(DEFAULT_SKILL_QUERIES),
            "discussions_fetched": len(discussions),
            "storage_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-full")
def run_full_collection():
    """
    Run complete weekly collection: jobs + discussions.
    """
    jobs_result = run_jobs_collection()
    discussions_result = run_discussions_collection()
    
    return {
        "status": "completed",
        "jobs": jobs_result,
        "discussions": discussions_result
    }


@router.post("/aggregate-trends")
def aggregate_skill_trends():
    """
    Aggregate skill mentions from jobs and discussions for trend analysis.
    Creates a snapshot of skill popularity.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Get all jobs
    jobs_url = f"{SUPABASE_REST_URL}/fetched_jobs?select=description"
    jobs_resp = requests.get(jobs_url, headers=HEADERS, timeout=30)
    jobs = jobs_resp.json() if jobs_resp.status_code == 200 else []
    
    # Get all discussions
    disc_url = f"{SUPABASE_REST_URL}/fetched_discussions?select=title,body"
    disc_resp = requests.get(disc_url, headers=HEADERS, timeout=30)
    discussions = disc_resp.json() if disc_resp.status_code == 200 else []
    
    # Count skill mentions
    job_skill_counts = Counter()
    discussion_skill_counts = Counter()
    
    # Extract from jobs
    for job in jobs:
        skills = extract_skills_from_text(job.get("description", ""))
        for skill in skills:
            job_skill_counts[skill["skill_name_normalized"]] += skill["mention_count"]
    
    # Extract from discussions
    for disc in discussions:
        text = f"{disc.get('title', '')} {disc.get('body', '')}"
        skills = extract_skills_from_text(text)
        for skill in skills:
            discussion_skill_counts[skill["skill_name_normalized"]] += skill["mention_count"]
    
    # Combine and prepare trend data
    all_skills = set(job_skill_counts.keys()) | set(discussion_skill_counts.keys())
    
    skill_data = []
    for skill in all_skills:
        skill_data.append({
            "skill_name": skill,
            "job_count": job_skill_counts.get(skill, 0),
            "discussion_count": discussion_skill_counts.get(skill, 0),
            "trend_direction": "stable"
        })
    
    # Update trends in database
    result = update_skill_trends(today, skill_data)
    
    return {
        "status": "completed",
        "snapshot_date": today,
        "unique_skills": len(all_skills),
        "update_result": result
    }


@router.get("/config")
def get_cron_config():
    """
    Get current cron configuration.
    """
    return {
        "job_queries": DEFAULT_JOB_QUERIES,
        "skill_queries": DEFAULT_SKILL_QUERIES,
        "schedule": "weekly"
    }

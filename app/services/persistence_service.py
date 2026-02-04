"""
Persistence Service - Handles database storage and deduplication.
Uses direct REST API calls to bypass client library issues.
"""
import requests
from app.core.config import settings
from datetime import datetime, timezone
import traceback
import json

SUPABASE_REST_URL = f"{settings.SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": settings.SUPABASE_KEY,
    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def store_jobs(jobs: list[dict]) -> dict:
    """
    Store fetched jobs in database with deduplication.
    Uses direct REST API calls.
    """
    inserted = 0
    skipped = 0
    errors = 0
    error_messages = []
    
    for job in jobs:
        try:
            # Prepare job data - remove raw_data and ensure proper types
            job_data = {
                "job_hash": job.get("job_hash", ""),
                "title": job.get("title", ""),
                "company_name": job.get("company_name", ""),
                "location": job.get("location", ""),
                "description": job.get("description", ""),
                "posted_date": job.get("posted_date", ""),
                "salary_text": job.get("salary_text", ""),
                "job_url": job.get("job_url", ""),
                "apply_url": job.get("apply_url", ""),
                "source": job.get("source", "serp_google_jobs"),
                "source_job_id": job.get("source_job_id", ""),
                "work_type": str(job.get("work_type", "")),
                "experience_level": job.get("experience_level", "")
            }
            
            # Check if job already exists
            check_url = f"{SUPABASE_REST_URL}/fetched_jobs?job_hash=eq.{job_data['job_hash']}&select=id"
            check_resp = requests.get(check_url, headers=HEADERS, timeout=10)
            
            if check_resp.status_code == 200 and check_resp.json():
                skipped += 1
                continue
            
            # Insert new job
            insert_url = f"{SUPABASE_REST_URL}/fetched_jobs"
            insert_resp = requests.post(
                insert_url,
                headers=HEADERS,
                json=job_data,
                timeout=10
            )
            
            if insert_resp.status_code in [200, 201]:
                inserted += 1
                print(f"Inserted job: {job_data.get('title', 'Unknown')[:50]}")
            else:
                errors += 1
                error_messages.append(f"HTTP {insert_resp.status_code}: {insert_resp.text[:100]}")
                print(f"Insert error: {insert_resp.status_code} - {insert_resp.text[:200]}")
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"Error storing job: {error_msg}")
            errors += 1
            error_messages.append(error_msg)
    
    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "total": len(jobs),
        "error_details": error_messages[:5] if error_messages else None
    }


def store_discussions(discussions: list[dict]) -> dict:
    """
    Store fetched discussions in database with deduplication.
    """
    inserted = 0
    skipped = 0
    errors = 0
    error_messages = []
    
    for post in discussions:
        try:
            # Prepare post data
            post_data = {
                "post_hash": post.get("post_hash", ""),
                "post_id": post.get("post_id", ""),
                "title": post.get("title", ""),
                "body": post.get("body", ""),
                "subreddit": post.get("subreddit", ""),
                "author": post.get("author", ""),
                "upvotes": int(post.get("upvotes", 0)),
                "comments_count": int(post.get("comments_count", 0)),
                "post_url": post.get("post_url", ""),
                "created_utc": post.get("created_utc", None),
                "source": post.get("source", "apify_reddit"),
                "search_query": post.get("search_query", "")
            }
            
            # Handle created_utc
            if not post_data["created_utc"]:
                del post_data["created_utc"]
            
            # Check if post already exists
            check_url = f"{SUPABASE_REST_URL}/fetched_discussions?post_hash=eq.{post_data['post_hash']}&select=id"
            check_resp = requests.get(check_url, headers=HEADERS, timeout=10)
            
            if check_resp.status_code == 200 and check_resp.json():
                skipped += 1
                continue
            
            # Insert new post
            insert_url = f"{SUPABASE_REST_URL}/fetched_discussions"
            insert_resp = requests.post(
                insert_url,
                headers=HEADERS,
                json=post_data,
                timeout=10
            )
            
            if insert_resp.status_code in [200, 201]:
                inserted += 1
                print(f"Inserted discussion: {post_data.get('title', 'Unknown')[:50]}")
            else:
                errors += 1
                error_messages.append(f"HTTP {insert_resp.status_code}: {insert_resp.text[:100]}")
                
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"Error storing discussion: {error_msg}")
            errors += 1
            error_messages.append(error_msg)
    
    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "total": len(discussions),
        "error_details": error_messages[:5] if error_messages else None
    }


def get_job_stats() -> dict:
    """Get statistics about stored jobs."""
    try:
        url = f"{SUPABASE_REST_URL}/fetched_jobs?select=id"
        headers_with_count = {**HEADERS, "Prefer": "count=exact"}
        resp = requests.get(url, headers=headers_with_count, timeout=10)
        
        count = int(resp.headers.get("content-range", "0-0/0").split("/")[-1])
        
        return {
            "total_jobs": count,
            "recent_jobs": count  # Simplified for now
        }
    except Exception as e:
        return {"error": str(e)}


def get_discussion_stats() -> dict:
    """Get statistics about stored discussions."""
    try:
        url = f"{SUPABASE_REST_URL}/fetched_discussions?select=id"
        headers_with_count = {**HEADERS, "Prefer": "count=exact"}
        resp = requests.get(url, headers=headers_with_count, timeout=10)
        
        count = int(resp.headers.get("content-range", "0-0/0").split("/")[-1])
        
        return {
            "total_discussions": count
        }
    except Exception as e:
        return {"error": str(e)}


def update_skill_trends(snapshot_date: str, skill_data: list[dict]) -> dict:
    """
    Update skill trends for a specific date.
    """
    inserted = 0
    updated = 0
    errors = 0
    
    for skill in skill_data:
        skill_normalized = skill["skill_name"].lower().strip()
        
        try:
            # Check if exists
            check_url = f"{SUPABASE_REST_URL}/skill_trends?snapshot_date=eq.{snapshot_date}&skill_name_normalized=eq.{skill_normalized}&select=id"
            check_resp = requests.get(check_url, headers=HEADERS, timeout=10)
            
            if check_resp.status_code == 200 and check_resp.json():
                # Update
                record_id = check_resp.json()[0]["id"]
                update_url = f"{SUPABASE_REST_URL}/skill_trends?id=eq.{record_id}"
                update_data = {
                    "job_mention_count": skill.get("job_count", 0),
                    "discussion_mention_count": skill.get("discussion_count", 0),
                    "trend_direction": skill.get("trend_direction", "stable")
                }
                requests.patch(update_url, headers=HEADERS, json=update_data, timeout=10)
                updated += 1
            else:
                # Insert
                insert_url = f"{SUPABASE_REST_URL}/skill_trends"
                insert_data = {
                    "snapshot_date": snapshot_date,
                    "skill_name": skill["skill_name"],
                    "skill_name_normalized": skill_normalized,
                    "job_mention_count": skill.get("job_count", 0),
                    "discussion_mention_count": skill.get("discussion_count", 0),
                    "trend_direction": skill.get("trend_direction", "stable")
                }
                requests.post(insert_url, headers=HEADERS, json=insert_data, timeout=10)
                inserted += 1
                
        except Exception as e:
            print(f"Error updating skill trend: {e}")
            errors += 1
    
    return {
        "inserted": inserted,
        "updated": updated,
        "errors": errors
    }

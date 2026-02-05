"""
SERP Collector - Fetches job listings from Google Jobs via SerpAPI.
"""
import requests
import hashlib
from datetime import datetime, timezone
from app.core.config import settings
from app.services.key_service import get_serp_key


def generate_job_hash(title: str, company: str, location: str) -> str:
    """Generate unique hash for job deduplication."""
    key = f"{title}|{company}|{location}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


def _get_serp_api_key() -> str:
    """Get SERP API key (database first, then env fallback)."""
    api_key = get_serp_key(fallback=settings.SERP_API_KEY)
    if not api_key or api_key == "your_serp_api_key_here":
        raise ValueError("SERP_API_KEY not configured. Add it via Admin Portal or get one from https://serpapi.com/")
    return api_key


def fetch_jobs_from_serp(
    query: str,
    location: str = "United States",
    num_results: int = 20
) -> list[dict]:
    """
    Fetch job listings from Google Jobs via SERP API.
    
    Args:
        query: Job search query (e.g., "Backend Developer")
        location: Location to search in
        num_results: Number of results to fetch
        
    Returns:
        List of normalized job records
    """
    api_key = _get_serp_api_key()
    
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": settings.DEFAULT_LANGUAGE,
        "gl": settings.DEFAULT_REGION,
        "api_key": api_key,
        "num": num_results
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        jobs = data.get("jobs_results", [])
        normalized_jobs = []
        
        for job in jobs:
            title = job.get("title", "")
            company = job.get("company_name", "")
            location = job.get("location", "")
            
            normalized = {
                "job_hash": generate_job_hash(title, company, location),
                "title": title,
                "company_name": company,
                "location": location,
                "description": job.get("description", ""),
                "posted_date": job.get("detected_extensions", {}).get("posted_at", ""),
                "salary_text": job.get("detected_extensions", {}).get("salary", ""),
                "job_url": job.get("share_link", ""),
                "apply_url": job.get("apply_options", [{}])[0].get("link", "") if job.get("apply_options") else "",
                "source": "serp_google_jobs",
                "source_job_id": job.get("job_id", ""),
                "work_type": job.get("detected_extensions", {}).get("work_from_home", "onsite"),
                "experience_level": "",  # Not always available
                "raw_data": job,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
            normalized_jobs.append(normalized)
        
        return normalized_jobs
        
    except requests.RequestException as e:
        print(f"SERP API error: {e}")
        return []


def fetch_jobs_batch(
    queries: list[str],
    location: str = "United States",
    num_per_query: int = 10
) -> list[dict]:
    """
    Fetch jobs for multiple queries in batch.
    
    Args:
        queries: List of job role keywords
        location: Location to search
        num_per_query: Results per query
        
    Returns:
        Combined list of all job results
    """
    all_jobs = []
    seen_hashes = set()
    
    for query in queries:
        print(f"Fetching jobs for: {query}")
        jobs = fetch_jobs_from_serp(query, location, num_per_query)
        
        for job in jobs:
            if job["job_hash"] not in seen_hashes:
                seen_hashes.add(job["job_hash"])
                all_jobs.append(job)
        
        print(f"  Found {len(jobs)} jobs, {len(all_jobs)} total unique")
    
    return all_jobs

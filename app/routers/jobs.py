"""
Jobs Router - Endpoints for job data collection.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.collectors.serp_collector import fetch_jobs_from_serp, fetch_jobs_batch
from app.services.persistence_service import store_jobs, get_job_stats
from app.services.normalizer_service import extract_skills_from_text

router = APIRouter()


class JobFetchRequest(BaseModel):
    query: str
    location: str = "United States"
    num_results: int = 20


class BatchJobFetchRequest(BaseModel):
    queries: list[str]
    location: str = "United States"
    num_per_query: int = 10


@router.post("/fetch")
def fetch_jobs(request: JobFetchRequest):
    """
    Fetch job listings for a single query.
    """
    try:
        jobs = fetch_jobs_from_serp(
            query=request.query,
            location=request.location,
            num_results=request.num_results
        )
        
        # Store in database
        result = store_jobs(jobs)
        
        return {
            "status": "success",
            "query": request.query,
            "jobs_fetched": len(jobs),
            "storage_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.post("/fetch-batch")
def fetch_jobs_batch_endpoint(request: BatchJobFetchRequest):
    """
    Fetch job listings for multiple queries in batch.
    """
    try:
        jobs = fetch_jobs_batch(
            queries=request.queries,
            location=request.location,
            num_per_query=request.num_per_query
        )
        
        # Store in database
        result = store_jobs(jobs)
        
        return {
            "status": "success",
            "queries": request.queries,
            "jobs_fetched": len(jobs),
            "storage_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.get("/stats")
def get_stats():
    """
    Get statistics about stored jobs.
    """
    return get_job_stats()


@router.post("/extract-skills/{job_id}")
def extract_job_skills(job_id: str):
    """
    Extract skills from a specific job's description.
    """
    from supabase import create_client
    from app.core.config import settings
    
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    
    # Get job
    job = supabase.table("fetched_jobs").select("description").eq("id", job_id).single().execute()
    
    if not job.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Extract skills
    skills = extract_skills_from_text(job.data["description"])
    
    # Store extracted skills
    for skill in skills:
        try:
            supabase.table("job_extracted_skills").insert({
                "job_id": job_id,
                "skill_name": skill["skill_name"],
                "skill_name_normalized": skill["skill_name_normalized"],
                "mention_count": skill["mention_count"]
            }).execute()
        except Exception:
            pass  # Ignore duplicates
    
    return {
        "job_id": job_id,
        "skills_extracted": len(skills),
        "skills": skills
    }

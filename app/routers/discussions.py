"""
Discussions Router - Endpoints for Reddit discussion collection.
Uses Reddit's public JSON API for reliable data collection.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.collectors.reddit_collector import fetch_reddit_discussions, fetch_discussions_batch, get_subreddit_hot_posts
from app.services.persistence_service import store_discussions, get_discussion_stats

router = APIRouter()


class DiscussionFetchRequest(BaseModel):
    query: str
    subreddits: list[str] = None
    max_items: int = 50
    sort: str = "relevance"


class BatchDiscussionFetchRequest(BaseModel):
    queries: list[str]
    subreddits: list[str] = None
    max_per_query: int = 20


# Default tech subreddits for skill discussions
DEFAULT_SUBREDDITS = [
    "programming",
    "learnprogramming",
    "cscareerquestions",
    "webdev",
    "javascript",
    "python",
    "java",
    "devops",
    "machinelearning",
    "datascience",
    "aws",
    "docker",
    "kubernetes"
]


@router.post("/fetch")
def fetch_discussions(request: DiscussionFetchRequest):
    """
    Fetch Reddit discussions for a single query.
    Uses Reddit's public JSON API.
    """
    try:
        subreddits = request.subreddits or DEFAULT_SUBREDDITS
        
        discussions = fetch_reddit_discussions(
            search_query=request.query,
            subreddits=subreddits,
            max_items=request.max_items,
            sort=request.sort
        )
        
        # Store in database
        result = store_discussions(discussions)
        
        return {
            "status": "success",
            "query": request.query,
            "subreddits": subreddits,
            "discussions_fetched": len(discussions),
            "storage_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch discussions: {str(e)}")


@router.post("/fetch-batch")
def fetch_discussions_batch_endpoint(request: BatchDiscussionFetchRequest):
    """
    Fetch discussions for multiple queries in batch.
    """
    try:
        subreddits = request.subreddits or DEFAULT_SUBREDDITS
        
        discussions = fetch_discussions_batch(
            queries=request.queries,
            subreddits=subreddits,
            max_per_query=request.max_per_query
        )
        
        # Store in database
        result = store_discussions(discussions)
        
        return {
            "status": "success",
            "queries": request.queries,
            "discussions_fetched": len(discussions),
            "storage_result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch discussions: {str(e)}")


@router.post("/fetch-hot/{subreddit}")
def fetch_hot_discussions(subreddit: str, limit: int = 25):
    """
    Fetch hot/trending posts from a specific subreddit.
    Good for finding current trending discussions.
    """
    try:
        discussions = get_subreddit_hot_posts(subreddit, limit)
        
        # Store in database
        result = store_discussions(discussions)
        
        return {
            "status": "success",
            "subreddit": subreddit,
            "discussions_fetched": len(discussions),
            "storage_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hot discussions: {str(e)}")


@router.get("/stats")
def get_stats():
    """
    Get statistics about stored discussions.
    """
    return get_discussion_stats()


@router.get("/subreddits")
def get_default_subreddits():
    """
    Get list of default subreddits being monitored.
    """
    return {
        "subreddits": DEFAULT_SUBREDDITS
    }

"""
Reddit Collector - Fetches Reddit discussions using Reddit's public JSON API.

This uses Reddit's public API endpoints which don't require authentication
for basic read operations. Much more reliable than scraping.
"""
import requests
import hashlib
from datetime import datetime, timezone
import time


def generate_post_hash(title: str, subreddit: str, created_time: str) -> str:
    """Generate unique hash for post deduplication."""
    key = f"{title}|{subreddit}|{created_time}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


# Reddit requires a User-Agent header
HEADERS = {
    "User-Agent": "TrendSkillService/1.0 (Data Collection Bot)"
}


def fetch_reddit_discussions(
    search_query: str,
    subreddits: list[str] = None,
    max_items: int = 50,
    sort: str = "relevance"
) -> list[dict]:
    """
    Fetch Reddit discussions using Reddit's public JSON API.
    
    Args:
        search_query: Search query for posts
        subreddits: List of subreddits to search (optional)
        max_items: Maximum posts to fetch
        sort: Sort order (relevance, hot, new, top)
        
    Returns:
        List of normalized discussion records
    """
    all_posts = []
    
    # Default tech subreddits for skill discussions
    default_subreddits = subreddits or [
        "programming",
        "learnprogramming",
        "cscareerquestions",
        "webdev",
        "python",
        "javascript",
        "java",
        "devops",
        "machinelearning",
        "datascience"
    ]
    
    # Calculate posts per subreddit
    posts_per_subreddit = max(5, max_items // len(default_subreddits))
    
    for subreddit in default_subreddits:
        try:
            posts = search_subreddit(subreddit, search_query, posts_per_subreddit, sort)
            all_posts.extend(posts)
            
            if len(all_posts) >= max_items:
                break
                
            # Rate limiting - Reddit allows ~60 requests per minute
            time.sleep(1)
            
        except Exception as e:
            print(f"Error fetching from r/{subreddit}: {e}")
            continue
    
    # Also search Reddit globally
    try:
        global_posts = search_reddit_global(search_query, min(25, max_items), sort)
        all_posts.extend(global_posts)
    except Exception as e:
        print(f"Error in global search: {e}")
    
    # Deduplicate by post_hash
    seen_hashes = set()
    unique_posts = []
    for post in all_posts:
        if post["post_hash"] not in seen_hashes:
            seen_hashes.add(post["post_hash"])
            unique_posts.append(post)
    
    print(f"Fetched {len(unique_posts)} unique Reddit posts for query: {search_query}")
    return unique_posts[:max_items]


def search_subreddit(subreddit: str, query: str, limit: int = 10, sort: str = "relevance") -> list[dict]:
    """
    Search within a specific subreddit.
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "on",  # Restrict to this subreddit
        "sort": sort,
        "t": "all",  # Time filter: all time
        "limit": limit
    }
    
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    
    if response.status_code != 200:
        print(f"Reddit API error for r/{subreddit}: {response.status_code}")
        return []
    
    data = response.json()
    posts = data.get("data", {}).get("children", [])
    
    return [normalize_reddit_post(post["data"], query) for post in posts if post.get("data")]


def search_reddit_global(query: str, limit: int = 25, sort: str = "relevance") -> list[dict]:
    """
    Search Reddit globally across all subreddits.
    """
    url = "https://www.reddit.com/search.json"
    params = {
        "q": query,
        "sort": sort,
        "t": "all",
        "limit": limit,
        "type": "link"  # Only posts, not comments
    }
    
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    
    if response.status_code != 200:
        print(f"Reddit global search error: {response.status_code}")
        return []
    
    data = response.json()
    posts = data.get("data", {}).get("children", [])
    
    return [normalize_reddit_post(post["data"], query) for post in posts if post.get("data")]


def normalize_reddit_post(post_data: dict, search_query: str) -> dict:
    """
    Normalize a Reddit post to our standard format.
    """
    title = post_data.get("title", "")
    subreddit = post_data.get("subreddit", "")
    created_utc = post_data.get("created_utc", 0)
    
    # Convert Unix timestamp to ISO format
    created_iso = ""
    if created_utc:
        try:
            created_iso = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
        except:
            created_iso = str(created_utc)
    
    return {
        "post_hash": generate_post_hash(title, subreddit, str(created_utc)),
        "post_id": post_data.get("id", ""),
        "title": title,
        "body": post_data.get("selftext", "")[:5000],  # Limit body length
        "subreddit": subreddit,
        "author": post_data.get("author", ""),
        "upvotes": int(post_data.get("score", 0)),
        "comments_count": int(post_data.get("num_comments", 0)),
        "post_url": f"https://reddit.com{post_data.get('permalink', '')}",
        "created_utc": created_iso,
        "source": "reddit_api",
        "search_query": search_query,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def fetch_discussions_batch(
    queries: list[str],
    subreddits: list[str] = None,
    max_per_query: int = 20
) -> list[dict]:
    """
    Fetch discussions for multiple queries.
    """
    all_posts = []
    seen_hashes = set()
    
    for query in queries:
        print(f"Fetching Reddit discussions for: {query}")
        posts = fetch_reddit_discussions(query, subreddits, max_per_query)
        
        for post in posts:
            if post["post_hash"] not in seen_hashes:
                seen_hashes.add(post["post_hash"])
                all_posts.append(post)
        
        print(f"  Found {len(posts)} posts, {len(all_posts)} total unique")
        
        # Rate limiting between queries
        time.sleep(2)
    
    return all_posts


def get_subreddit_hot_posts(subreddit: str, limit: int = 25) -> list[dict]:
    """
    Get hot posts from a specific subreddit (for trending topics).
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    params = {"limit": limit}
    
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    posts = data.get("data", {}).get("children", [])
    
    return [normalize_reddit_post(post["data"], f"hot:{subreddit}") for post in posts if post.get("data")]

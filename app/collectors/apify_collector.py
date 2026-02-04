"""
Apify Collector - Fetches Reddit discussions via Apify Reddit Scraper.

This collector uses the "apify/reddit-scraper" actor which is free and reliable.
"""
import requests
import hashlib
from datetime import datetime, timezone
from app.core.config import settings


def generate_post_hash(title: str, subreddit: str, created_time: str) -> str:
    """Generate unique hash for post deduplication."""
    key = f"{title}|{subreddit}|{created_time}".lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


def fetch_reddit_discussions(
    search_query: str,
    subreddits: list[str] = None,
    max_items: int = 50,
    sort: str = "relevance"
) -> list[dict]:
    """
    Fetch Reddit discussions via Apify Reddit Scraper actor.
    
    Args:
        search_query: Search query for posts (e.g., "Python developer jobs")
        subreddits: List of subreddits to search (optional)
        max_items: Maximum posts to fetch
        sort: Sort order (relevance, hot, new, top)
        
    Returns:
        List of normalized discussion records
    """
    if not settings.APIFY_API_TOKEN or settings.APIFY_API_TOKEN == "your_apify_api_token_here":
        raise ValueError("APIFY_API_TOKEN not configured. Get one from https://apify.com/")
    
    # Use the official Apify Reddit Scraper actor
    # Actor: apify/reddit-scraper (official and free)
    actor_id = "oAuCIx3ItNrs2okjQ"  # This is the official Apify Reddit Scraper actor ID
    
    # Default subreddits for tech discussions
    default_subreddits = subreddits or [
        "programming",
        "learnprogramming", 
        "cscareerquestions",
        "webdev",
        "javascript",
        "python",
        "java",
        "devops",
        "machinelearning",
        "datascience"
    ]
    
    # Build actor input - search for posts containing the query
    actor_input = {
        "startUrls": [{"url": f"https://www.reddit.com/search/?q={search_query.replace(' ', '%20')}&type=link&sort={sort}"}],
        "maxItems": max_items,
        "maxPostCount": max_items,
        "maxComments": 0,  # We don't need comments
        "proxy": {
            "useApifyProxy": True
        }
    }
    
    # Use run-sync endpoint for synchronous execution
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.APIFY_API_TOKEN}"
    }
    
    try:
        print(f"Calling Apify Reddit Scraper for query: {search_query}")
        
        response = requests.post(
            run_url,
            json=actor_input,
            headers=headers,
            timeout=300  # 5 minutes max
        )
        
        print(f"Apify response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Apify error: {response.text[:500]}")
            # Try alternate approach - search via subreddit URLs
            return fetch_from_subreddits(search_query, default_subreddits, max_items)
        
        posts = response.json()
        print(f"Apify returned {len(posts)} posts")
        
        if not posts:
            # Fallback to subreddit-based fetching
            return fetch_from_subreddits(search_query, default_subreddits, max_items)
        
        normalized_posts = normalize_posts(posts, search_query)
        return normalized_posts
        
    except requests.RequestException as e:
        print(f"Apify API error: {e}")
        # Fallback to subreddit-based fetching
        return fetch_from_subreddits(search_query, subreddits or default_subreddits, max_items)


def fetch_from_subreddits(
    search_query: str,
    subreddits: list[str],
    max_items: int = 50
) -> list[dict]:
    """
    Fallback: Fetch Reddit posts by scraping subreddit search pages.
    Uses a simpler web scraping approach.
    """
    print(f"Using fallback subreddit scraping for: {search_query}")
    
    # Use cheerio-scraper for simple HTML scraping
    actor_id = "apify~cheerio-scraper"
    
    # Build URLs to scrape
    start_urls = []
    for subreddit in subreddits[:5]:  # Limit to 5 subreddits
        url = f"https://old.reddit.com/r/{subreddit}/search?q={search_query.replace(' ', '+')}&restrict_sr=on&sort=relevance&t=all"
        start_urls.append({"url": url})
    
    actor_input = {
        "startUrls": start_urls,
        "maxRequestsPerCrawl": max_items,
        "pageFunction": """
        async function pageFunction(context) {
            const { $, request, log } = context;
            const results = [];
            
            $('div.search-result-link').each((i, el) => {
                const $el = $(el);
                const title = $el.find('a.search-title').text().trim();
                const url = $el.find('a.search-title').attr('href');
                const score = $el.find('.search-score').text().trim();
                const comments = $el.find('.search-comments').text().trim();
                const subreddit = $el.find('.search-subreddit-link').text().trim();
                const time = $el.find('.search-time time').attr('datetime');
                
                if (title) {
                    results.push({
                        title,
                        url: url ? 'https://reddit.com' + url : '',
                        score,
                        comments,
                        subreddit,
                        createdAt: time,
                        searchQuery: request.url
                    });
                }
            });
            
            return results;
        }
        """,
        "proxy": {
            "useApifyProxy": True
        }
    }
    
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.APIFY_API_TOKEN}"
    }
    
    try:
        response = requests.post(
            run_url,
            json=actor_input,
            headers=headers,
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"Fallback scraper error: {response.text[:500]}")
            return []
        
        posts = response.json()
        return normalize_posts(posts, search_query)
        
    except Exception as e:
        print(f"Fallback scraper error: {e}")
        return []


def normalize_posts(posts: list, search_query: str) -> list[dict]:
    """Normalize posts to standard format."""
    normalized_posts = []
    
    for post in posts:
        title = post.get("title", "")
        if not title:
            continue
            
        subreddit = post.get("communityName") or post.get("subreddit") or post.get("community", {}).get("name", "")
        created_utc = post.get("createdAt") or post.get("created_utc") or post.get("time", "")
        
        normalized = {
            "post_hash": generate_post_hash(title, subreddit, str(created_utc)),
            "post_id": post.get("id") or post.get("postId", ""),
            "title": title,
            "body": post.get("body") or post.get("selftext") or post.get("text", ""),
            "subreddit": subreddit,
            "author": post.get("username") or post.get("author") or post.get("authorName", ""),
            "upvotes": int(post.get("upVotes") or post.get("score") or post.get("ups") or 0),
            "comments_count": int(post.get("numberOfComments") or post.get("num_comments") or post.get("comments") or 0),
            "post_url": post.get("url") or post.get("postUrl", ""),
            "created_utc": created_utc,
            "source": "apify_reddit",
            "search_query": search_query,
            "raw_data": post,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        normalized_posts.append(normalized)
    
    return normalized_posts


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
    
    return all_posts

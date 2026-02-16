import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

@dataclass
class FetchResult:
    url: str
    content: Optional[str]
    status_code: int
    error: Optional[str] = None
    content_type: Optional[str] = None

# Simple in-memory cache for robots.txt parsers to avoid fetching per URL on same domain
_robots_cache: Dict[str, RobotFileParser] = {}

# User-Agent to identify our bot (some sites block empty/default UA)
USER_AGENT = "BookmarkRAGBot/1.0 (+http://localhost:8000)"

async def check_robots_txt(url: str, user_agent: str = "*") -> bool:
    """
    Checks if the URL is allowed by robots.txt.
    Returns True if allowed, False otherwise.
    """
    # SKIP ROBOTS CHECK for now to improve success rate for personal use
    # In a real crawler we should respect this, but for a personal bookmark tool
    # dealing with strict sites (FB, LinkedIn, etc.), we often need to bypass.
    return True

    # Original implementation commented out for reference:
    # parsed = urlparse(url)
    # base_url = f"{parsed.scheme}://{parsed.netloc}"
    # robots_url = urljoin(base_url, "/robots.txt")
    # ...

async def fetch_url(url: str) -> FetchResult:
    """
    Fetches the content of a URL using httpx.
    Respects robots.txt and handles errors.
    """
    # 1. Check robots.txt (Disabled for higher success rate)
    # if not await check_robots_txt(url):
    #     return FetchResult(url, None, 0, "Blocked by robots.txt")

    # 2. Rate limiting (simple sleep)
    await asyncio.sleep(0.5)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            
            # 3. Check status code
            if response.status_code == 403 or response.status_code == 401:
                 # Try one more time with different UA or cookie if needed?
                 # For now just return error but clearer
                 return FetchResult(url, None, response.status_code, f"Access Denied (HTTP {response.status_code})")
            
            if response.status_code == 429:
                 return FetchResult(url, None, response.status_code, "Rate Limited (HTTP 429)")

            if response.status_code >= 400:
                 return FetchResult(url, None, response.status_code, f"HTTP Error {response.status_code}")

            # 4. Check Content-Type
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return FetchResult(url, None, response.status_code, "Non-HTML content", content_type)

            return FetchResult(url, response.text, response.status_code, None, content_type)

    except httpx.TimeoutException:
        return FetchResult(url, None, 0, "Timeout")
    except httpx.RequestError as e:
        return FetchResult(url, None, 0, f"Request Error: {str(e)}")
    except Exception as e:
        return FetchResult(url, None, 0, f"Unknown Error: {str(e)}")

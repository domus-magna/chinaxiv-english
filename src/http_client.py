"""
HTTP client for ChinaXiv English translation.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_proxies


DEFAULT_TIMEOUT = (10, 60)  # connect, read
USER_AGENT = "chinaxiv-english/1.0 (+https://github.com/)"


class HttpError(Exception):
    """HTTP-related errors."""
    pass


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=20),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(HttpError),
)
def http_get(
    url: str, 
    *, 
    headers: Optional[dict] = None, 
    params: Optional[dict] = None, 
    timeout: Tuple[int, int] = DEFAULT_TIMEOUT
) -> requests.Response:
    """
    Make HTTP GET request with retry logic and proxy support.
    
    Args:
        url: URL to request
        headers: Optional headers
        params: Optional query parameters
        timeout: Request timeout (connect, read)
        
    Returns:
        Response object
        
    Raises:
        HttpError: On request failure or non-OK status
    """
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    
    proxies, source = get_proxies()
    eff_timeout = (15, 90) if source != "none" else timeout
    
    try:
        if source == "config" and proxies:
            resp = requests.get(url, headers=h, params=params, timeout=eff_timeout, proxies=proxies)
        else:
            # Use trust_env behavior so NO_PROXY is honored for env proxies
            resp = requests.get(url, headers=h, params=params, timeout=eff_timeout)
    except requests.RequestException as e:
        raise HttpError(str(e))
    
    if not resp.ok:
        raise HttpError(f"GET {url} -> {resp.status_code}")
    
    return resp


def openrouter_headers() -> dict:
    """
    Get headers for OpenRouter API requests.
    
    Returns:
        Headers dictionary
        
    Raises:
        RuntimeError: If OPENROUTER_API_KEY not set
    """
    from .config import load_dotenv
    
    # Load from .env if present and not already set
    load_dotenv()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/",
        "X-Title": "chinaxiv-english",
    }

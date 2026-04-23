"""Shared HTTP client for all source connectors.

Provides a consistent HTTP layer with:
- Configurable timeouts and retries (via tenacity)
- Respectful User-Agent rotation
- Session management with cookie support
- Rate limiting between requests
"""

from __future__ import annotations

import random
import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from imti.core.logger import get_logger

logger = get_logger("http")

# Respectful User-Agent pool — rotates to avoid blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
]

# Minimum delay between requests to the same domain (seconds)
MIN_REQUEST_INTERVAL = 1.5


class HttpClient:
    """Shared HTTP client with built-in retry, timeout, and respectful scraping."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._last_request_time: dict[str, float] = {}  # domain -> timestamp
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers=self._random_headers(),
        )

    def _random_headers(self) -> dict[str, str]:
        """Generate headers with a random User-Agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _rate_limit(self, domain: str) -> None:
        """Enforce minimum delay between requests to the same domain."""
        last = self._last_request_time.get(domain, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time[domain] = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request with retry, rate limiting, and respectful headers."""
        domain = url.split("/")[2] if "/" in url else url
        self._rate_limit(domain)

        headers = kwargs.pop("headers", {})
        headers.update(self._random_headers())

        logger.debug(f"GET {url}")
        response = self._client.get(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    def get_json(self, url: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request and return parsed JSON."""
        response = self.get(url, **kwargs)
        return response.json()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

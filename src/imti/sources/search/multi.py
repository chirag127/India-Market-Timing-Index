"""Multi-search API source connector for news discovery.

Provides: News headlines from Google Custom Search, Tavily, Brave, and NewsAPI.
These are used as input to the LLM analyzer for sentiment scoring.

Uses multiple search APIs with fallback so that news collection
never fails due to a single API outage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from imti.config.settings import get_settings
from imti.core.logger import get_logger
from imti.sources.base import BaseSource

logger = get_logger("source.search")

# Search queries for Indian market news
SEARCH_QUERIES = [
    "Indian stock market Nifty Sensex today",
    "FII DII activity India market",
    "RBI monetary policy India",
    "India VIX market volatility",
    "Nifty options put call ratio",
    "India economy GDP inflation",
    "global markets impact India",
    "SEBI regulation market impact",
]


class MultiSearchSource(BaseSource):
    """Multi-search API source — collects news via Google, Tavily, Brave, NewsAPI.

    Tries APIs in order: Google → Tavily → Brave → NewsAPI.
    Stops as soon as one returns results.
    """

    name = "multi_search"
    priority = 18
    timeout_seconds = 45.0  # Search can be slow
    max_retries = 1

    provides = ["search_headlines"]

    def __init__(self) -> None:
        super().__init__()
        self._settings = get_settings()

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch news headlines from multiple search APIs."""
        result: dict[str, Any] = {}
        all_headlines: list[str] = []

        # Try Google Custom Search first
        if self._settings.search_google_api_key and self._settings.search_google_cx:
            headlines = self._search_google()
            if headlines:
                all_headlines.extend(headlines)
                logger.info(f"Google returned {len(headlines)} headlines")

        # Try Tavily
        if self._settings.search_tavily_api_key:
            headlines = self._search_tavily()
            if headlines:
                all_headlines.extend(headlines)
                logger.info(f"Tavily returned {len(headlines)} headlines")

        # Try Brave
        if self._settings.search_brave_api_key:
            headlines = self._search_brave()
            if headlines:
                all_headlines.extend(headlines)
                logger.info(f"Brave returned {len(headlines)} headlines")

        # Try NewsAPI
        if self._settings.newsapi_key:
            headlines = self._search_newsapi()
            if headlines:
                all_headlines.extend(headlines)
                logger.info(f"NewsAPI returned {len(headlines)} headlines")

        # Deduplicate headlines
        seen: set[str] = set()
        unique: list[str] = []
        for h in all_headlines:
            h_lower = h.lower().strip()
            if h_lower not in seen and len(h) > 15:
                seen.add(h_lower)
                unique.append(h)

        result["search_headlines"] = unique[:50]  # Cap at 50 headlines
        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
            "headline_count": len(unique),
            "apis_used": self._apis_used(),
        }
        return result

    def _search_google(self) -> list[str]:
        """Search via Google Custom Search API."""
        headlines: list[str] = []
        try:
            for query in SEARCH_QUERIES[:3]:  # Limit to 3 queries to save quota
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self._settings.search_google_api_key,
                    "cx": self._settings.search_google_cx,
                    "q": query,
                    "num": 5,
                }
                response = httpx.get(url, params=params, timeout=10.0)
                data = response.json()
                for item in data.get("items", []):
                    title = item.get("title", "")
                    if title:
                        headlines.append(title)
        except Exception as e:
            logger.warning(f"Google search failed: {e}")
        return headlines

    def _search_tavily(self) -> list[str]:
        """Search via Tavily API."""
        headlines: list[str] = []
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self._settings.search_tavily_api_key,
                "query": "Indian stock market Nifty today",
                "max_results": 10,
                "search_depth": "basic",
            }
            response = httpx.post(url, json=payload, timeout=15.0)
            data = response.json()
            for result in data.get("results", []):
                title = result.get("title", "")
                if title:
                    headlines.append(title)
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
        return headlines

    def _search_brave(self) -> list[str]:
        """Search via Brave Search API."""
        headlines: list[str] = []
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {"X-Subscription-Token": self._settings.search_brave_api_key}
            params = {"q": "Indian stock market Nifty today", "count": 10}
            response = httpx.get(url, headers=headers, params=params, timeout=10.0)
            data = response.json()
            for result in data.get("web", {}).get("results", []):
                title = result.get("title", "")
                if title:
                    headlines.append(title)
        except Exception as e:
            logger.warning(f"Brave search failed: {e}")
        return headlines

    def _search_newsapi(self) -> list[str]:
        """Search via NewsAPI."""
        headlines: list[str] = []
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": self._settings.newsapi_key,
                "q": "Nifty OR Sensex OR Indian stock market",
                "language": "en",
                "pageSize": 15,
                "sortBy": "publishedAt",
            }
            response = httpx.get(url, params=params, timeout=10.0)
            data = response.json()
            for article in data.get("articles", []):
                title = article.get("title", "")
                if title:
                    headlines.append(title)
        except Exception as e:
            logger.warning(f"NewsAPI search failed: {e}")
        return headlines

    def _apis_used(self) -> list[str]:
        """List which APIs are configured."""
        apis: list[str] = []
        if self._settings.search_google_api_key:
            apis.append("google")
        if self._settings.search_tavily_api_key:
            apis.append("tavily")
        if self._settings.search_brave_api_key:
            apis.append("brave")
        if self._settings.newsapi_key:
            apis.append("newsapi")
        return apis

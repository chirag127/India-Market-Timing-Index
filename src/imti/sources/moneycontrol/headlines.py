"""Moneycontrol headline scraper for news sentiment.

Scrapes top market headlines from Moneycontrol (one of India's largest
financial news portals) for use in LLM news analysis.
"""

from __future__ import annotations

from typing import Any

from imti.core.logger import get_logger
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.moneycontrol")

MONEYCONTROL_MARKETS_URL = "https://www.moneycontrol.com/news/markets/"


class MoneycontrolHeadlinesSource(BaseSource):
    """Moneycontrol headlines scraper — provides news headline data for LLM analysis.

    This source collects headlines rather than numeric indicators.
    The headlines are fed into the LLM analyzer for sentiment scoring.
    """

    name = "moneycontrol_headlines"
    priority = 15
    timeout_seconds = 20.0
    max_retries = 2

    provides = ["moneycontrol_headlines"]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Scrape top market headlines from Moneycontrol."""
        result: dict[str, Any] = {}

        try:
            from bs4 import BeautifulSoup

            response = self._http.get(MONEYCONTROL_MARKETS_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            headlines: list[str] = []

            # Strategy 1: Look for standard headline tags
            for tag in soup.find_all(["h2", "h3"], class_=True):
                classes = " ".join(tag.get("class", []))
                if any(kw in classes.lower() for kw in ["headline", "title", "story"]):
                    text = tag.get_text(strip=True)
                    if text and len(text) > 15:
                        headlines.append(text)

            # Strategy 2: Look for <a> tags with story URLs
            if not headlines:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    text = a_tag.get_text(strip=True)
                    if "/news/" in href and text and len(text) > 20:
                        headlines.append(text)

            # Deduplicate and limit
            seen = set()
            unique_headlines = []
            for h in headlines:
                if h not in seen:
                    seen.add(h)
                    unique_headlines.append(h)
                if len(unique_headlines) >= 30:
                    break

            result["moneycontrol_headlines"] = unique_headlines  # type: ignore[assignment]
            result["_metadata"] = {
                "status": "success",
                "headline_count": len(unique_headlines),
            }

        except Exception as e:
            result["_metadata"] = {"errors": [str(e)]}
            logger.warning(f"Failed to fetch Moneycontrol headlines: {e}")

        return result

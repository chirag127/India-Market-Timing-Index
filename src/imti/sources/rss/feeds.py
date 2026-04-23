"""RSS feed source connector for financial news aggregation.

Provides: Headlines from Indian financial news RSS feeds.
RSS feeds are free, reliable, and rarely blocked — good as a
primary news source with search APIs as fallback.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.rss")

# Indian financial news RSS feeds
RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://economictimes.indiatimes.com/rss/markets.cms",
    "https://economictimes.indiatimes.com/rss/news/economy.cms",
    "https://www.livemint.com/rss/market",
    "https://www.business-standard.com/rss/markets-106.rss",
]


class RSSFeedsSource(BaseSource):
    """RSS feed source — provides headlines from multiple Indian financial feeds.

    RSS feeds are reliable and rarely blocked, making them a good
    primary source for news collection. Falls back to search APIs
    if RSS feeds are unavailable.
    """

    name = "rss_feeds"
    priority = 14  # Higher priority than search APIs — RSS is free and reliable
    timeout_seconds = 30.0
    max_retries = 2

    provides = ["rss_headlines"]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch headlines from RSS feeds."""
        result: dict[str, Any] = {}
        all_headlines: list[str] = []

        for feed_url in RSS_FEEDS:
            try:
                headlines = self._parse_feed(feed_url)
                all_headlines.extend(headlines)
            except Exception as e:
                logger.warning(f"Failed to parse RSS feed {feed_url}: {e}")

        # Deduplicate
        seen: set[str] = set()
        unique: list[str] = []
        for h in all_headlines:
            h_lower = h.lower().strip()
            if h_lower not in seen and len(h) > 15:
                seen.add(h_lower)
                unique.append(h)

        result["rss_headlines"] = unique[:60]
        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
            "headline_count": len(unique),
            "feeds_checked": len(RSS_FEEDS),
        }
        return result

    def _parse_feed(self, url: str) -> list[str]:
        """Parse an RSS feed and extract headlines."""
        headlines: list[str] = []
        try:
            response = self._http.get(url)
            root = ET.fromstring(response.text)

            # Handle both RSS 2.0 and Atom feeds
            # RSS 2.0: <rss><channel><item><title>
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    headlines.append(title_el.text.strip())

            # Atom: <feed><entry><title>
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title_el = entry.find("{http://www.w3.org/2005/Atom}title")
                if title_el is not None and title_el.text:
                    headlines.append(title_el.text.strip())

        except ET.ParseError as e:
            logger.debug(f"XML parse error for {url}: {e}")
        except Exception as e:
            logger.debug(f"Feed fetch error for {url}: {e}")

        return headlines

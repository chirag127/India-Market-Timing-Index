"""Tickertape Market Mood Index (MMI) scraper.

The MMI is the highest-weight indicator in the IMTI system.
It provides a 0–100 sentiment score for Indian markets, updated
every 3 minutes during market hours.

Source: https://www.tickertape.in/market-mood-index
"""

from __future__ import annotations

from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.tickertape")

MMI_URL = "https://www.tickertape.in/market-mood-index"


class TickertapeMMISource(BaseSource):
    """Tickertape Market Mood Index scraper — primary sentiment indicator.

    The MMI is the most important indicator in the system (highest weight).
    It aggregates FII activity, India VIX, market momentum, breadth,
    price strength, and gold demand into a single 0–100 score.

    Contrarian interpretation (per the INVERTED score system):
    - MMI < 25 (Extreme Fear) → BUY OPPORTUNITY → contributes to LOW danger score
    - MMI > 75 (Extreme Greed) → SELL DANGER → contributes to HIGH danger score
    """

    name = "tickertape_mmi"
    priority = 1  # Highest priority — this is the primary sentiment source
    timeout_seconds = 20.0
    max_retries = 3

    provides = ["tickertape_mmi"]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Scrape the Tickertape MMI value from the market mood index page.

        The MMI value is typically available in the page's JavaScript
        or embedded data. We try multiple extraction strategies.
        """
        result: dict[str, Any] = {}

        try:
            response = self._http.get(MMI_URL)
            html = response.text

            # Strategy 1: Look for MMI value in embedded JSON/state
            mmi_value = self._extract_mmi_from_html(html)

            if mmi_value is not None:
                result["tickertape_mmi"] = mmi_value
                result["_metadata"] = {"status": "success", "url": MMI_URL}
            else:
                # Strategy 2: Try the API endpoint if available
                mmi_value = self._try_api_endpoint()
                if mmi_value is not None:
                    result["tickertape_mmi"] = mmi_value
                    result["_metadata"] = {"status": "success", "source": "api"}
                else:
                    result["_metadata"] = {"errors": ["Could not extract MMI value"]}

        except Exception as e:
            result["_metadata"] = {"errors": [str(e)]}
            logger.warning(f"Failed to fetch Tickertape MMI: {e}")

        return result

    def _extract_mmi_from_html(self, html: str) -> float | None:
        """Extract MMI value from the HTML page content.

        Tries multiple patterns since the page structure may change.
        """
        import re

        # Pattern 1: Look for __NEXT_DATA__ or similar embedded state
        patterns = [
            r'"marketMoodIndex":\s*([\d.]+)',
            r'"mmi":\s*([\d.]+)',
            r'"moodIndex":\s*([\d.]+)',
            r'"currentValue":\s*([\d.]+)',  # Generic current value
            r'Market Mood Index.*?(\d+\.?\d*)',  # Text near the label
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                value = safe_float(match.group(1))
                if 0 <= value <= 100:
                    return value

        return None

    def _try_api_endpoint(self) -> float | None:
        """Try fetching MMI from a potential API endpoint."""
        try:
            # Tickertape may have an API behind the scenes
            api_url = "https://www.tickertape.in/api/market-mood-index"
            data = self._http.get_json(api_url)
            if isinstance(data, dict):
                # Try common key names
                for key in ("mmi", "value", "currentValue", "marketMoodIndex"):
                    if key in data:
                        value = safe_float(data[key])
                        if 0 <= value <= 100:
                            return value
            elif isinstance(data, (int, float)):
                value = safe_float(data)
                if 0 <= value <= 100:
                    return value
        except Exception:
            pass

        return None

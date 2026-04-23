"""RBI (Reserve Bank of India) source connector.

Provides: Repo rate, reverse repo rate, CRR, SLR, and monetary policy stance.
RBI monetary policy directly affects market sentiment and institutional flows.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.rbi")

RBI_RATES_URL = "https://www.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=2147"


class RBIRatesSource(BaseSource):
    """RBI source — provides monetary policy rates and banking data.

    RBI repo rate and monetary policy stance are key macro inputs.
    Rate cuts = dovish = bullish (lower danger score in our system).
    Rate hikes = hawkish = bearish (but contrarianly may signal opportunity).
    """

    name = "rbi_rates"
    priority = 30
    timeout_seconds = 25.0
    max_retries = 2

    provides = [
        "rbi_repo_rate",
        "rbi_reverse_repo_rate",
        "crr",
        "india_10y_yield",  # Fallback for Investing.com
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch RBI monetary policy rates."""
        result: dict[str, Any] = {}

        try:
            from bs4 import BeautifulSoup

            response = self._http.get(RBI_RATES_URL)
            soup = BeautifulSoup(response.text, "html.parser")

            # Parse the rates table
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    cell_texts = [c.get_text(strip=True) for c in cells]

                    if len(cell_texts) >= 2:
                        label = cell_texts[0].lower()
                        value_text = cell_texts[1].replace("%", "").strip()

                        if "repo" in label and "reverse" not in label:
                            result["rbi_repo_rate"] = safe_float(value_text, default=0.0)
                        elif "reverse repo" in label:
                            result["rbi_reverse_repo_rate"] = safe_float(value_text, default=0.0)
                        elif "crr" in label:
                            result["crr"] = safe_float(value_text, default=0.0)

        except Exception as e:
            logger.error(f"Failed to fetch RBI rates: {e}")
            raise

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
        }
        return result

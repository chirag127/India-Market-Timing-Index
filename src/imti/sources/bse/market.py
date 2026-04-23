"""BSE (Bombay Stock Exchange) source connector.

Provides: Sensex price, BSE advance-decline, BSE 500 breadth data.
Acts as a fallback/confirmation for NSE data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.bse")

BSE_INDICES_URL = "https://api.bseindia.com/BseIndiaAPI/api/IndexChartNew/w"
BSE_MARKET_STATUS = "https://api.bseindia.com/BseIndiaAPI/api/MktStatus/w"


class BSEMarketSource(BaseSource):
    """BSE source — provides Sensex data and breadth as NSE fallback.

    BSE data serves as confirmation and fallback for NSE readings.
    The Sensex advance-decline is computed differently and provides
    a useful cross-check for NSE breadth data.
    """

    name = "bse_market"
    priority = 50  # Lower priority — primarily a fallback for NSE
    timeout_seconds = 25.0
    max_retries = 2

    provides = [
        "sensex_close",
        "advance_decline_ratio",  # Fallback for NSE A/D
        "bse_500_breadth",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch BSE market data."""
        result: dict[str, Any] = {}

        try:
            response = self._http.get_json(
                f"{BSE_INDICES_URL}?IndexID=10&FromDate=01/01/2025&ToDate=31/12/2025"
            )
            if isinstance(response, dict):
                # Parse latest Sensex value
                data_points = response.get("Data", [])
                if data_points:
                    latest = data_points[-1]
                    result["sensex_close"] = safe_float(latest.get("clos", 0), default=0.0)

        except Exception as e:
            logger.warning(f"Failed to fetch BSE index data: {e}")

        try:
            response = self._http.get_json(BSE_MARKET_STATUS)
            if isinstance(response, dict):
                adv = safe_float(response.get("advances", 0), default=0.0)
                dec = safe_float(response.get("declines", 0), default=0.0)
                if dec > 0:
                    result["advance_decline_ratio"] = adv / dec
                elif adv > 0:
                    result["advance_decline_ratio"] = adv  # All advances, no declines

        except Exception as e:
            logger.warning(f"Failed to fetch BSE market status: {e}")

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
        }
        return result

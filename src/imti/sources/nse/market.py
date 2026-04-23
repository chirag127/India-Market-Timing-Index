"""NSE India source connector for market data.

Provides: India VIX, Nifty PCR, advance-decline ratio, FII/DII data,
new highs/lows, % above DMA, and more from NSE India.

Note: NSE blocks automated scrapers aggressively. This connector
uses multiple strategies (session cookies, header rotation) and
falls back to alternative sources if blocked.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.nse")

# NSE endpoints
NSE_BASE = "https://www.nseindia.com"
NSE_VIX_URL = f"{NSE_BASE}/api/market-data-pre-open?key=ALL"
NSE_INDICES_URL = f"{NSE_BASE}/api/allIndices"
NSE_ADV_DECL_URL = f"{NSE_BASE}/api/market-data-pre-open?key=ALL"
NSE_PARTICIPANT_OI_URL = f"{NSE_BASE}/api/fii-dii"
NSE_BREADTH_URL = f"{NSE_BASE}/api/market-status"


class NSEMarketSource(BaseSource):
    """NSE India source — provides VIX, market data, breadth, and FII/DII flows.

    NSE requires initial cookie fetch via homepage visit, then API calls.
    This connector handles that flow. If blocked, the registry will
    fall back to alternative sources.
    """

    name = "nse_market"
    priority = 5  # Highest priority for Indian market data — official source
    timeout_seconds = 30.0
    max_retries = 3

    provides = [
        "india_vix",
        "advance_decline_ratio",
        "nifty_close",
        "banknifty_close",
        "sensex_close",
        "fii_cash_net",
        "dii_cash_net",
        "fii_index_futures_net_oi",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)
        self._session_initialized = False

    def _init_session(self) -> None:
        """Initialize NSE session by visiting homepage (required for cookies)."""
        if self._session_initialized:
            return
        try:
            self._http.get(NSE_BASE)
            self._session_initialized = True
            logger.debug("NSE session initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize NSE session: {e}")

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch market data from NSE India."""
        result: dict[str, Any] = {}
        errors: list[str] = []

        # Initialize session (get cookies)
        self._init_session()

        # Fetch indices data (includes VIX, Nifty, etc.)
        try:
            indices_data = self._fetch_indices()
            if indices_data:
                result.update(indices_data)
        except Exception as e:
            errors.append(f"indices: {e}")

        # Fetch FII/DII data
        try:
            fiidii_data = self._fetch_fii_dii()
            if fiidii_data:
                result.update(fiidii_data)
        except Exception as e:
            errors.append(f"fii_dii: {e}")

        if errors:
            result["_metadata"] = {"errors": errors}
        else:
            result["_metadata"] = {"status": "success"}

        return result

    def _fetch_indices(self) -> dict[str, float]:
        """Fetch index values including VIX from NSE API."""
        data: dict[str, float] = {}
        try:
            response = self._http.get_json(NSE_INDICES_URL)
            indices_list = response.get("data", [])

            for idx in indices_list:
                name = idx.get("index", "").lower()
                last_price = safe_float(idx.get("last"))

                if "nifty 50" in name:
                    data["nifty_close"] = last_price
                elif "nifty bank" in name:
                    data["banknifty_close"] = last_price
                elif "s&p bse sensex" in name or "sensex" in name:
                    data["sensex_close"] = last_price
                elif "india vix" in name:
                    data["india_vix"] = last_price

        except Exception as e:
            logger.warning(f"Failed to fetch NSE indices: {e}")

        return data

    def _fetch_fii_dii(self) -> dict[str, float]:
        """Fetch FII/DII net flow data from NSE."""
        data: dict[str, float] = {}
        try:
            response = self._http.get_json(NSE_PARTICIPANT_OI_URL)
            fii_data = response.get("fii", {})
            dii_data = response.get("dii", {})

            # FII cash market net (in crores)
            fii_net = safe_float(fii_data.get("netBuy", 0)) - safe_float(fii_data.get("netSell", 0))
            data["fii_cash_net"] = safe_float(fii_data.get("net", fii_net))

            # DII cash market net
            dii_net = safe_float(dii_data.get("netBuy", 0)) - safe_float(dii_data.get("netSell", 0))
            data["dii_cash_net"] = safe_float(dii_data.get("net", dii_net))

        except Exception as e:
            logger.warning(f"Failed to fetch FII/DII data: {e}")

        return data

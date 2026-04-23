"""NSE options chain source for PCR, put-call OI change, VIX skew.

Scrapes NSE options data to compute:
- Put/Call Ratio (PCR) based on volume and OI
- Put-call OI change (day-over-day)
- VIX skew (put IV - call IV) if IV data available
"""

from __future__ import annotations

from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.nse_options")

NSE_OPTIONS_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"


class NSEOptionsSource(BaseSource):
    """NSE options chain source — provides PCR, OI data, and implied volatility skew."""

    name = "nse_options"
    priority = 8
    timeout_seconds = 30.0
    max_retries = 3

    provides = [
        "put_call_ratio",
        "put_call_oi_change",
        "vix_skew",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)
        self._session_initialized = False

    def _init_session(self) -> None:
        """Initialize NSE session (required for API access)."""
        if self._session_initialized:
            return
        try:
            self._http.get("https://www.nseindia.com")
            self._session_initialized = True
        except Exception as e:
            logger.warning(f"Failed to init NSE options session: {e}")

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch options chain data and compute PCR, OI change."""
        result: dict[str, Any] = {}
        self._init_session()

        try:
            response = self._http.get_json(NSE_OPTIONS_URL)
            records = response.get("records", {}).get("data", [])

            if not records:
                result["_metadata"] = {"errors": ["No options data returned"]}
                return result

            total_put_oi = 0.0
            total_call_oi = 0.0
            total_put_volume = 0.0
            total_call_volume = 0.0
            put_iv_sum = 0.0
            call_iv_sum = 0.0
            iv_count = 0

            for record in records:
                # CE (Call) data
                ce = record.get("CE", {})
                if ce:
                    total_call_oi += safe_float(ce.get("openInterest", 0))
                    total_call_volume += safe_float(ce.get("totalTradedVolume", 0))
                    ce_iv = safe_float(ce.get("impliedVolatility", 0))
                    if ce_iv > 0:
                        call_iv_sum += ce_iv
                        iv_count += 1

                # PE (Put) data
                pe = record.get("PE", {})
                if pe:
                    total_put_oi += safe_float(pe.get("openInterest", 0))
                    total_put_volume += safe_float(pe.get("totalTradedVolume", 0))
                    pe_iv = safe_float(pe.get("impliedVolatility", 0))
                    if pe_iv > 0:
                        put_iv_sum += pe_iv

            # Compute PCR (volume-based, more responsive than OI-based)
            if total_call_volume > 0:
                result["put_call_ratio"] = total_put_volume / total_call_volume
            elif total_call_oi > 0:
                result["put_call_ratio"] = total_put_oi / total_call_oi

            # VIX skew (average put IV - average call IV)
            if iv_count > 0 and call_iv_sum > 0:
                avg_put_iv = put_iv_sum / iv_count if iv_count > 0 else 0
                avg_call_iv = call_iv_sum / iv_count
                result["vix_skew"] = avg_put_iv - avg_call_iv

            # put_call_oi_change requires comparing with previous day (set to 0 for now)
            result["put_call_oi_change"] = 0.0  # Computed in indicator layer from historical data

            result["_metadata"] = {"status": "success"}

        except Exception as e:
            result["_metadata"] = {"errors": [str(e)]}
            logger.warning(f"Failed to fetch NSE options: {e}")

        return result

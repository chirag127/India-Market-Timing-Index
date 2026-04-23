"""Investing.com source connector for macro/valuation data.

Provides: India 10Y yield, India 5Y CDS, Nifty P/E, Nifty P/B,
earnings yield, dividend yield, and other valuation metrics.

Note: Investing.com aggressively blocks scrapers. This connector
uses respectful scraping with header rotation and falls back to
alternative sources (Yahoo Finance, RBI) if blocked.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource
from imti.sources.http import HttpClient

logger = get_logger("source.investing")

# Investing.com URLs for Indian market data
INVESTING_INDIA_10Y = "https://www.investing.com/rates-bonds/india-10-year-bond-yield"
INVESTING_NIFTY_PE = "https://www.investing.com/indices/nifty-50-ratio"
INVESTING_USDINR = "https://www.investing.com/currencies/usd-inr"


class InvestingEconSource(BaseSource):
    """Investing.com source — provides macro and valuation data.

    Good for India 10Y yield, valuation ratios, and CDS spreads.
    Falls back to Yahoo/RBI if blocked.
    """

    name = "investing_econ"
    priority = 20  # Lower priority — often blocks scrapers
    timeout_seconds = 25.0
    max_retries = 2

    provides = [
        "india_10y_yield",
        "nifty_pe",
        "nifty_pb",
        "earnings_yield",
        "dividend_yield",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._http = HttpClient(timeout=self.timeout_seconds)

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch macro/valuation data from Investing.com."""
        result: dict[str, Any] = {}

        try:
            self._fetch_yield(result)
        except Exception as e:
            logger.warning(f"Failed to fetch India 10Y yield from Investing.com: {e}")

        try:
            self._fetch_valuation(result)
        except Exception as e:
            logger.warning(f"Failed to fetch valuation data from Investing.com: {e}")

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
        }
        return result

    def _fetch_yield(self, result: dict[str, Any]) -> None:
        """Fetch India 10Y bond yield."""
        try:
            from bs4 import BeautifulSoup

            response = self._http.get(INVESTING_INDIA_10Y)
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for the last price in the overview section
            price_el = soup.find("span", {"data-test": "instrument-price-last"})
            if price_el:
                result["india_10y_yield"] = safe_float(
                    price_el.get_text(strip=True).replace("%", ""),
                    default=0.0,
                )
        except Exception as e:
            logger.debug(f"Yield parsing failed: {e}")

    def _fetch_valuation(self, result: dict[str, Any]) -> None:
        """Fetch Nifty P/E and P/B ratios."""
        try:
            from bs4 import BeautifulSoup

            response = self._http.get(INVESTING_NIFTY_PE)
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for P/E ratio in the data table
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_text = cells[1].get_text(strip=True).replace(",", "")

                    if "p/e" in label or "price/earnings" in label:
                        result["nifty_pe"] = safe_float(value_text, default=0.0)
                    elif "p/b" in label or "price/book" in label:
                        result["nifty_pb"] = safe_float(value_text, default=0.0)
                    elif "dividend" in label:
                        result["dividend_yield"] = safe_float(value_text, default=0.0)
                    elif "earnings" in label and "yield" in label:
                        result["earnings_yield"] = safe_float(value_text, default=0.0)

        except Exception as e:
            logger.debug(f"Valuation parsing failed: {e}")

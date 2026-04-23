"""Yahoo Finance source connector for global market data, commodities, and forex.

Provides: Nifty/Sensex/BankNifty prices, S&P 500, Nikkei, DXY, Brent, Gold, USD/INR, US 10Y yield.
Uses yfinance library which is free and reliable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import yfinance as yf

from imti.core.logger import get_logger
from imti.core.validation import safe_float
from imti.sources.base import BaseSource

logger = get_logger("source.yahoo")

# Yahoo Finance tickers for Indian and global markets
TICKER_MAP: dict[str, str] = {
    "nifty_close": "^NSEI",           # Nifty 50
    "sensex_close": "^BSESN",         # BSE Sensex
    "banknifty_close": "^NSEBANK",    # Nifty Bank
    "sp500_close": "^GSPC",           # S&P 500
    "sp500_overnight": "^GSPC",       # Same — computed as % change
    "nasdaq_close": "^IXIC",          # Nasdaq
    "nikkei_close": "^N225",          # Nikkei 225
    "hang_seng_close": "^HSI",        # Hang Seng
    "dxy": "DX-Y.NYB",               # Dollar Index
    "brent_crude": "BZ=F",            # Brent Crude Futures
    "gold": "GC=F",                   # Gold Futures
    "usd_inr": "INR=X",              # USD/INR
    "us_10y_yield": "^TNX",           # US 10-Year Treasury Yield
    "vix": "^VIX",                    # CBOE VIX (US)
}


class YahooFinanceSource(BaseSource):
    """Yahoo Finance source — provides global market data via yfinance.

    Free, reliable, no API key needed. Good as primary source for
    price data, commodities, forex, and global indices.
    """

    name = "yahoo_finance"
    priority = 10  # High priority — reliable and free
    timeout_seconds = 45.0  # yfinance can be slow
    max_retries = 3

    provides = list(TICKER_MAP.keys())

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch latest data from Yahoo Finance for all tracked tickers."""
        result: dict[str, Any] = {}
        errors: list[str] = []

        for indicator_name, ticker in TICKER_MAP.items():
            try:
                data = self._fetch_ticker(ticker)
                if data is not None:
                    result[indicator_name] = data
                else:
                    errors.append(f"{indicator_name} ({ticker}): no data returned")
            except Exception as e:
                errors.append(f"{indicator_name} ({ticker}): {e}")
                logger.warning(f"Failed to fetch {ticker}: {e}")

        if errors:
            result["_metadata"] = {"errors": errors, "error_count": len(errors)}
        else:
            result["_metadata"] = {"status": "all_success"}

        return result

    def _fetch_ticker(self, ticker: str) -> float | None:
        """Fetch the latest closing price for a ticker."""
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")  # Get 5 days for context
            if hist.empty:
                return None
            # Return the latest close price
            latest = hist["Close"].iloc[-1]
            return safe_float(latest)
        except Exception as e:
            logger.debug(f"Ticker {ticker} fetch failed: {e}")
            return None

    def fetch_history(self, ticker: str, period: str = "1y") -> list[dict[str, Any]]:
        """Fetch historical OHLCV data for a ticker.

        Args:
            ticker: Yahoo Finance ticker symbol
            period: Period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)

        Returns:
            List of dicts with date, open, high, low, close, volume
        """
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period=period)
            if hist.empty:
                return []
            records = []
            for idx, row in hist.iterrows():
                records.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": safe_float(row.get("Open")),
                    "high": safe_float(row.get("High")),
                    "low": safe_float(row.get("Low")),
                    "close": safe_float(row.get("Close")),
                    "volume": safe_float(row.get("Volume")),
                })
            return records
        except Exception as e:
            logger.error(f"Failed to fetch history for {ticker}: {e}")
            return []

    def fetch_nifty_history(self, period: str = "1y") -> list[dict[str, Any]]:
        """Convenience method: fetch Nifty 50 historical data."""
        return self.fetch_history("^NSEI", period)

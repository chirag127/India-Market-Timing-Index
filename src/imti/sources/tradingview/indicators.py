"""TradingView source connector for technical indicators.

Provides: RSI, MACD, Stochastic, ADX, CCI, Bollinger Bands,
Supertrend, and other computed technical indicators.

Uses yfinance price data to compute indicators using the `ta` library,
rather than scraping TradingView directly. This is more reliable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from imti.core.logger import get_logger
from imti.sources.base import BaseSource

logger = get_logger("source.tradingview")

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    logger.warning("ta library not installed — technical indicators will be unavailable")


class TradingViewSource(BaseSource):
    """Technical indicator source — computes indicators from price data.

    Uses the `ta` (technical analysis) library to compute 20+ technical
    indicators from OHLCV data obtained via Yahoo Finance.

    In the INVERTED scoring system:
    - Oversold RSI, oversold Stochastic = BUY opportunity → LOW danger
    - Overbought RSI, overbought Stochastic = SELL danger → HIGH danger
    """

    name = "tradingview_tech"
    priority = 12  # Medium priority — computed, not scraped
    timeout_seconds = 60.0  # Needs to fetch price history
    max_retries = 1

    provides = [
        "rsi_14",
        "rsi_7",
        "rsi_21",
        "stochastic_k",
        "stochastic_d",
        "williams_r",
        "macd_line",
        "macd_signal",
        "macd_histogram",
        "adx",
        "cci",
        "bollinger_pct_b",
        "bollinger_bandwidth",
        "atr_pct",
        "roc_10",
        "roc_20",
        "ema_90_30_momentum",
        "supertrend",
        "obv_slope",
        "vwap_distance",
    ]

    def __init__(self) -> None:
        super().__init__()

    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Compute technical indicators from price data."""
        result: dict[str, Any] = {}

        if not TA_AVAILABLE:
            logger.warning("ta library unavailable — skipping technical indicators")
            result["_metadata"] = {"source": self.name, "error": "ta library not installed"}
            return result

        try:
            import yfinance as yf

            # Fetch Nifty 50 OHLCV data (6 months for indicator computation)
            ticker = yf.Ticker("^NSEI")
            hist = ticker.history(period="6mo")

            if hist.empty:
                logger.warning("No price data returned from Yahoo Finance")
                result["_metadata"] = {"source": self.name, "error": "no price data"}
                return result

            close = hist["Close"]
            high = hist["High"]
            low = hist["Low"]
            volume = hist["Volume"]

            # --- RSI ---
            result["rsi_14"] = self._latest(ta.momentum.rsi(close, window=14))
            result["rsi_7"] = self._latest(ta.momentum.rsi(close, window=7))
            result["rsi_21"] = self._latest(ta.momentum.rsi(close, window=21))

            # --- Stochastic ---
            stoch = ta.momentum.StochasticOscillator(high, low, close)
            result["stochastic_k"] = self._latest(stoch.stoch())
            result["stochastic_d"] = self._latest(stoch.stoch_signal())

            # --- Williams %R ---
            result["williams_r"] = self._latest(ta.momentum.williams_r(high, low, close))

            # --- MACD ---
            macd = ta.trend.MACD(close)
            result["macd_line"] = self._latest(macd.macd())
            result["macd_signal"] = self._latest(macd.macd_signal())
            result["macd_histogram"] = self._latest(macd.macd_diff())

            # --- ADX ---
            result["adx"] = self._latest(ta.trend.adx(high, low, close))

            # --- CCI ---
            result["cci"] = self._latest(ta.trend.cci(high, low, close))

            # --- Bollinger Bands ---
            bb = ta.volatility.BollingerBands(close)
            result["bollinger_pct_b"] = self._latest(bb.bollinger_pband())
            result["bollinger_bandwidth"] = self._latest(bb.bollinger_wband())

            # --- ATR % ---
            atr = ta.volatility.AverageTrueRange(high, low, close)
            atr_val = self._latest(atr.average_true_range())
            last_close = float(close.iloc[-1])
            result["atr_pct"] = (atr_val / last_close * 100) if last_close > 0 else 0.0

            # --- ROC ---
            result["roc_10"] = self._latest(ta.momentum.roc(close, window=10))
            result["roc_20"] = self._latest(ta.momentum.roc(close, window=20))

            # --- EMA momentum ---
            ema_30 = ta.trend.ema_indicator(close, window=30)
            ema_90 = ta.trend.ema_indicator(close, window=90)
            ema_momentum = ((ema_30 - ema_90) / ema_90 * 100) if ema_90.iloc[-1] > 0 else 0.0
            result["ema_90_30_momentum"] = float(ema_momentum) if not pd.isna(ema_momentum) else 0.0

            # --- Supertrend (simplified: 1=bullish, -1=bearish) ---
            result["supertrend"] = self._compute_supertrend(high, low, close)

            # --- OBV slope ---
            obv = ta.volume.on_balance_volume(close, volume)
            if len(obv) >= 10:
                result["obv_slope"] = float(obv.iloc[-1] - obv.iloc[-10])
            else:
                result["obv_slope"] = 0.0

        except Exception as e:
            logger.error(f"Failed to compute technical indicators: {e}")

        result["_metadata"] = {
            "source": self.name,
            "fetched_at": datetime.now().isoformat(),
            "indicators_computed": len([k for k in result if k != "_metadata"]),
        }
        return result

    @staticmethod
    def _latest(series: pd.Series) -> float:
        """Get the latest non-NaN value from a pandas Series."""
        valid = series.dropna()
        if valid.empty:
            return 0.0
        return float(valid.iloc[-1])

    @staticmethod
    def _compute_supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
                            period: int = 10, multiplier: float = 3.0) -> float:
        """Compute simplified Supertrend signal: 1=bullish, -1=bearish."""
        if len(close) < period + 1:
            return 0.0

        atr_series = ta.volatility.AverageTrueRange(high, low, close, window=period)
        atr_val = TradingViewSource._latest(atr_series.average_true_range())

        hl2 = (high + low) / 2
        upper_band = float(hl2.iloc[-1]) + multiplier * atr_val
        lower_band = float(hl2.iloc[-1]) - multiplier * atr_val
        last_close = float(close.iloc[-1])

        if last_close > upper_band:
            return 1.0  # Bullish
        elif last_close < lower_band:
            return -1.0  # Bearish
        return 0.0

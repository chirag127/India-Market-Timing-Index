"""Feature store — maintains indicator history and produces ML-ready features.

The feature store:
- Accumulates hourly indicator values into a CSV
- Computes rolling statistics (z-scores, percentiles) for normalization
- Produces a feature vector suitable for the XGBoost model
- Tracks feature stability and missing data patterns
"""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from imti.core.logger import get_logger
from imti.core.types import IndicatorValue, Snapshot
from imti.core.enums import IndicatorCategory

logger = get_logger("indicators.feature_store")


class FeatureStore:
    """Feature store — accumulates indicators and produces ML features.

    The feature store maintains a time-series DataFrame of all indicator
    values, computes rolling normalizations, and produces the final
    feature vector for the scoring model.
    """

    # Expected indicator names (50+ indicators across all categories)
    EXPECTED_INDICATORS: list[str] = [
        # Sentiment
        "tickertape_mmi", "cnn_fear_greed", "custom_india_fg",
        "llm_danger_score", "llm_panic_score", "llm_euphoria_score", "llm_opportunity_score",
        # Volatility
        "india_vix", "vix_5d_zscore", "vix_skew",
        # Breadth
        "advance_decline_ratio", "pct_above_20dma", "pct_above_50dma",
        "pct_above_200dma", "pct_near_52w_high_minus_low", "trin",
        # Flow
        "fii_cash_net", "dii_cash_net", "fii_index_futures_net_oi",
        "fii_long_short_ratio", "sip_monthly_flow",
        # Technical
        "nifty_pct_change", "ema_90_30_momentum", "rsi_14", "rsi_7", "rsi_21",
        "stochastic_k", "stochastic_d", "williams_r",
        "macd_line", "macd_signal", "macd_histogram",
        "adx", "cci", "supertrend", "bollinger_pct_b", "bollinger_bandwidth",
        "atr_pct", "roc_10", "roc_20", "obv_slope",
        # Derivatives
        "put_call_ratio", "put_call_oi_change",
        # Macro / Global
        "usd_inr", "dxy", "brent_crude", "gold", "gold_nifty_ratio",
        "india_10y_yield", "us_10y_yield", "sp500_overnight",
        "nikkei_overnight", "rbi_repo_rate",
        # Valuation
        "nifty_pe", "nifty_pb", "earnings_yield", "dividend_yield",
    ]

    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            from imti.core.paths import ProjectPaths
            paths = ProjectPaths()
            data_dir = paths.features
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._history: pd.DataFrame | None = None

    def load_history(self) -> pd.DataFrame:
        """Load historical indicator data from CSV."""
        csv_path = self.data_dir / "indicator_history.csv"
        if csv_path.exists():
            self._history = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            logger.info(f"Loaded {len(self._history)} historical records")
        else:
            self._history = pd.DataFrame()
            logger.info("No historical data found — starting fresh")
        return self._history

    def add_snapshot(self, snapshot: Snapshot) -> pd.DataFrame:
        """Add indicator values from a snapshot to the feature store."""
        if self._history is None:
            self.load_history()

        # Extract indicator values
        row: dict[str, Any] = {"timestamp": snapshot.timestamp}
        for name, iv in snapshot.indicators.items():
            row[name] = iv.value

        # Create a single-row DataFrame
        new_row = pd.DataFrame([row]).set_index("timestamp")

        # Append to history
        if self._history is not None and not self._history.empty:
            self._history = pd.concat([self._history, new_row])
            # Remove duplicate timestamps (keep latest)
            self._history = self._history[~self._history.index.duplicated(keep="last")]
        else:
            self._history = new_row

        logger.info(f"Added snapshot to feature store: {len(row) - 1} indicators")
        return self._history

    def save_history(self) -> None:
        """Save indicator history to CSV."""
        if self._history is not None and not self._history.empty:
            csv_path = self.data_dir / "indicator_history.csv"
            self._history.to_csv(csv_path)
            logger.info(f"Saved {len(self._history)} records to {csv_path}")

    def compute_feature_vector(self, snapshot: Snapshot) -> dict[str, float]:
        """Compute the ML-ready feature vector from a snapshot.

        For each indicator:
        1. Get the raw value
        2. Compute z-score over rolling 63-day window
        3. Compute percentile rank over rolling 252-day window
        4. Return both raw + normalized features

        The feature vector has 50+ indicators × 3 (raw, zscore, percentile) = 150+ features.
        """
        if self._history is None:
            self.load_history()

        features: dict[str, float] = {}

        for name, iv in snapshot.indicators.items():
            raw = iv.value
            if raw is None:
                raw = 0.0

            features[f"{name}_raw"] = raw

            # Compute rolling statistics if we have enough history
            # NOTE: Data is hourly, so 63 rows ≈ 2.6 days, not 3 months.
            # Use appropriate row counts for hourly granularity:
            #   ~3 months = 63 trading days × 7 hours = 441 rows
            #   ~1 year   = 252 trading days × 7 hours = 1764 rows
            if self._history is not None and name in self._history.columns:
                series = self._history[name].dropna()

                # Window sizes for hourly data
                zscore_window = 441   # ~3 months of hourly data
                pctrank_window = 1764 # ~1 year of hourly data

                if len(series) >= 10:
                    # Z-score over ~3 months of hourly data
                    tail_zscore = series.tail(min(zscore_window, len(series)))
                    mean_z = tail_zscore.mean()
                    std_z = tail_zscore.std()
                    zscore = (raw - mean_z) / std_z if std_z > 0 else 0.0
                    features[f"{name}_zscore_3m"] = zscore

                    # Percentile rank over ~1 year of hourly data
                    tail_pct = series.tail(min(pctrank_window, len(series)))
                    if len(tail_pct) > 5:
                        pct_rank = (tail_pct < raw).sum() / len(tail_pct) * 100
                        features[f"{name}_pctrank_1y"] = pct_rank
                    else:
                        features[f"{name}_pctrank_1y"] = 50.0

                    # 5-row change (~5 hours)
                    if len(series) >= 5:
                        prev = series.iloc[-5]
                        change_5d = raw - prev if prev != 0 else 0.0
                        features[f"{name}_5d_change"] = change_5d
                else:
                    features[f"{name}_zscore_3m"] = 0.0
                    features[f"{name}_pctrank_1y"] = 50.0
            else:
                features[f"{name}_zscore_3m"] = 0.0
                features[f"{name}_pctrank_1y"] = 50.0

        # Add time-based features
        now = snapshot.timestamp
        features["hour_of_day"] = now.hour
        features["day_of_week"] = now.weekday()
        features["is_market_hours"] = 1.0 if snapshot.market_status.value == "open" else 0.0
        features["is_holiday"] = 1.0 if snapshot.is_holiday else 0.0

        return features

    def get_missing_indicators(self, snapshot: Snapshot) -> list[str]:
        """Find which expected indicators are missing from the snapshot."""
        available = set(snapshot.indicators.keys())
        missing = [name for name in self.EXPECTED_INDICATORS if name not in available]
        return missing

    @property
    def indicator_coverage(self) -> float:
        """Percentage of expected indicators that have data."""
        if self._history is None or self._history.empty:
            return 0.0
        available = set(self._history.columns) & set(self.EXPECTED_INDICATORS)
        return len(available) / len(self.EXPECTED_INDICATORS) * 100

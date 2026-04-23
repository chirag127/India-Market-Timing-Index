"""Score thresholds, indicator validation ranges, and normalization config.

These thresholds define the boundaries for score zones, validation of
indicator values, and normalization methods.
"""

from imti.core.enums import ScoreZone

# ============================================================
# Score Zone Thresholds (INVERTED: 0=strong buy, 100=strong sell)
# ============================================================
SCORE_THRESHOLDS: dict[ScoreZone, tuple[float, float]] = {
    ScoreZone.EXTREME_BUY: (0, 15),
    ScoreZone.STRONG_BUY: (16, 30),
    ScoreZone.BUY_LEAN: (31, 45),
    ScoreZone.NEUTRAL: (46, 55),
    ScoreZone.SELL_LEAN: (56, 69),
    ScoreZone.STRONG_SELL: (70, 84),
    ScoreZone.EXTREME_SELL: (85, 100),
}

# ============================================================
# Indicator Validation Ranges
# Values outside these ranges are flagged as suspicious
# and replaced with last known good value
# ============================================================
INDICATOR_RANGES: dict[str, tuple[float, float]] = {
    # Sentiment / Mood
    "tickertape_mmi": (0, 100),
    "cnn_fear_greed": (0, 100),
    "custom_india_fg": (0, 100),
    "india_vix": (5, 80),
    "vix_5d_zscore": (-4, 4),
    "vix_skew": (-50, 50),
    "llm_news_score": (0, 100),
    "llm_panic_score": (0, 100),
    "llm_euphoria_score": (0, 100),
    "llm_opportunity_score": (0, 100),
    "moneycontrol_sentiment": (-1, 1),

    # Flow / Institutional
    "fii_cash_net": (-10000, 10000),  # crores
    "dii_cash_net": (-10000, 10000),
    "fii_index_futures_net_oi": (-50000, 50000),
    "fii_long_short_ratio": (0, 5),
    "sip_flow": (0, 30000),  # monthly crores

    # Breadth
    "advance_decline_ratio": (0, 10),
    "pct_above_20dma": (0, 100),
    "pct_above_50dma": (0, 100),
    "pct_above_200dma": (0, 100),
    "pct_near_52w_high_minus_low": (-100, 100),
    "mcclellan_oscillator": (-200, 200),
    "trin": (0, 5),
    "smallcap_outperformance": (-10, 10),
    "banknifty_nifty_ratio": (0.5, 3.0),

    # Technical
    "nifty_pct_change": (-15, 15),
    "ema_90_30_momentum": (-10, 10),
    "rsi_14": (0, 100),
    "stochastic_k": (0, 100),
    "stochastic_d": (0, 100),
    "williams_r": (-100, 0),
    "roc_10": (-20, 20),
    "macd_line": (-500, 500),
    "macd_histogram": (-200, 200),
    "adx": (0, 100),
    "cci": (-300, 300),
    "supertrend": (-1, 1),  # -1 = bearish, 1 = bullish
    "bollinger_pct_b": (-0.5, 1.5),
    "bollinger_bandwidth": (0, 50),
    "atr_pct": (0, 10),

    # Put/Call / Derivatives
    "put_call_ratio": (0.1, 5.0),
    "pcr_change": (-2, 2),
    "put_call_oi_change": (-50, 50),

    # Macro / Global
    "usd_inr": (70, 90),
    "dxy": (90, 120),
    "brent_crude": (30, 150),
    "gold": (1500, 3500),
    "gold_nifty_ratio": (0, 5),
    "india_10y_yield": (5, 10),
    "us_10y_yield": (2, 6),
    "india_us_10y_spread": (0, 8),
    "sp500_overnight": (-5, 5),
    "nikkei_overnight": (-5, 5),
    "gift_nifty_change": (-5, 5),
    "cpi_inflation": (1, 10),
    "rbi_repo_rate": (3, 9),

    # Valuation
    "nifty_pe": (5, 50),
    "nifty_pb": (1, 8),
    "earnings_yield_10y_spread": (-5, 10),
    "mcap_to_gdp": (20, 150),
    "dividend_yield": (0.5, 3.5),
}

# ============================================================
# Normalization Method Per Indicator Category
# ============================================================
NORMALIZATION_METHODS: dict[str, str] = {
    "sentiment": "rolling_percentile_252",  # Percentile rank over 1 year
    "flow": "zscore_63",                   # Z-score over 3 months
    "breadth": "min_max_252",              # Min-max scale over 1 year
    "technical": "rolling_percentile_252",
    "volatility": "rolling_percentile_252",
    "macro": "zscore_63",
    "valuation": "rolling_percentile_252",
    "news": "min_max_0_100",               # Already on 0-100 scale from LLM
}

# ============================================================
# Indian Market Trading Hours (IST)
# ============================================================
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30
MARKET_TIMEZONE = "Asia/Kolkata"

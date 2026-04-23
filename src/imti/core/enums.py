"""Core enumerations for the IMTI system."""

from enum import Enum


class ScoreZone(str, Enum):
    """IMTI score interpretation zones.

    IMPORTANT: Score is INVERTED — low score = buy opportunity, high score = sell/danger.
    This is an opportunity-seeking system, NOT conservative.
    """

    EXTREME_BUY = "extreme_buy"       # 0–15: Maximum buy opportunity
    STRONG_BUY = "strong_buy"         # 16–30: Strong buy signal
    BUY_LEAN = "buy_lean"             # 31–45: Leaning buy
    NEUTRAL = "neutral"               # 46–55: No strong conviction
    SELL_LEAN = "sell_lean"           # 56–69: Leaning sell
    STRONG_SELL = "strong_sell"       # 70–84: Strong sell / danger
    EXTREME_SELL = "extreme_sell"     # 85–100: Maximum danger

    @classmethod
    def from_score(cls, score: float) -> "ScoreZone":
        """Determine score zone from a 0–100 score value."""
        if score < 0 or score > 100:
            raise ValueError(f"Score must be 0–100, got {score}")
        if score <= 15:
            return cls.EXTREME_BUY
        if score <= 30:
            return cls.STRONG_BUY
        if score <= 45:
            return cls.BUY_LEAN
        if score <= 55:
            return cls.NEUTRAL
        if score <= 69:
            return cls.SELL_LEAN
        if score <= 84:
            return cls.STRONG_SELL
        return cls.EXTREME_SELL

    @property
    def is_buy_zone(self) -> bool:
        """True if this zone suggests buying."""
        return self in (ScoreZone.EXTREME_BUY, ScoreZone.STRONG_BUY, ScoreZone.BUY_LEAN)

    @property
    def is_sell_zone(self) -> bool:
        """True if this zone suggests selling."""
        return self in (ScoreZone.SELL_LEAN, ScoreZone.STRONG_SELL, ScoreZone.EXTREME_SELL)

    @property
    def color(self) -> str:
        """Hex color for UI display."""
        colors = {
            ScoreZone.EXTREME_BUY: "#00C853",   # Bright green
            ScoreZone.STRONG_BUY: "#4CAF50",     # Green
            ScoreZone.BUY_LEAN: "#8BC34A",       # Light green
            ScoreZone.NEUTRAL: "#FFC107",        # Amber
            ScoreZone.SELL_LEAN: "#FF9800",      # Orange
            ScoreZone.STRONG_SELL: "#F44336",    # Red
            ScoreZone.EXTREME_SELL: "#B71C1C",   # Dark red
        }
        return colors[self]

    @property
    def emoji(self) -> str:
        """Emoji for email/display."""
        emojis = {
            ScoreZone.EXTREME_BUY: "🟢🟢",
            ScoreZone.STRONG_BUY: "🟢",
            ScoreZone.BUY_LEAN: "🟡🟢",
            ScoreZone.NEUTRAL: "🟡",
            ScoreZone.SELL_LEAN: "🟡🔴",
            ScoreZone.STRONG_SELL: "🔴",
            ScoreZone.EXTREME_SELL: "🔴🔴",
        }
        return emojis[self]


class MarketStatus(str, Enum):
    """Current market status."""

    OPEN = "open"
    CLOSED = "closed"
    HOLIDAY = "holiday"
    HALF_DAY = "half_day"
    PRE_OPEN = "pre_open"


class RunType(str, Enum):
    """Type of pipeline run."""

    MARKET_HOURS = "market_hours"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"


class IndexName(str, Enum):
    """Tracked Indian market indices."""

    NIFTY_50 = "nifty_50"
    SENSEX = "sensex"
    NIFTY_BANK = "nifty_bank"


class IndicatorCategory(str, Enum):
    """Categories of indicators.

    NOTE: TECHNICAL indicators are collected for display only —
    they have ZERO weight in the scoring model.
    FUNDAMENTAL valuation is the primary driver.
    """

    SENTIMENT = "sentiment"
    FLOW = "flow"
    BREADTH = "breadth"
    TECHNICAL = "technical"  # Display only — zero model weight
    VOLATILITY = "volatility"
    MACRO = "macro"
    VALUATION = "valuation"
    NEWS = "news"
    FUNDAMENTAL = "fundamental"  # Primary driver — 35% weight
    ANALYST = "analyst"  # Stock screener only — not in market score


class MTFSafetyTier(int, Enum):
    """MTF (Margin Trading Facility) safety tier for stocks.

    Tier 1 = safest (blue-chip, low drawdown)
    Tier 4 = dangerous (avoid for MTF)
    """

    TIER_1_SAFEST = 1   # Max drawdown <30% (Reliance, HDFC Bank, ICICI Bank, Infosys, TCS)
    TIER_2_SAFE = 2     # Max drawdown 30-40% (SBI, Axis Bank, Bharti Airtel, L&T, HUL)
    TIER_3_MODERATE = 3 # Max drawdown 40-50% (Tata Motors, Tata Steel, Maruti, Wipro)
    TIER_4_RISKY = 4    # Max drawdown >50% (Mid-caps, cyclicals — AVOID for MTF)

    @classmethod
    def from_drawdown(cls, max_drawdown_pct: float) -> "MTFSafetyTier":
        """Determine MTF safety tier from historical max drawdown."""
        if max_drawdown_pct < 30:
            return cls.TIER_1_SAFEST
        if max_drawdown_pct < 40:
            return cls.TIER_2_SAFE
        if max_drawdown_pct < 50:
            return cls.TIER_3_MODERATE
        return cls.TIER_4_RISKY

    @property
    def is_mtf_safe(self) -> bool:
        """True if this tier is safe for MTF/pay-later trading."""
        return self in (MTFSafetyTier.TIER_1_SAFEST, MTFSafetyTier.TIER_2_SAFE)


class StockRecommendation(str, Enum):
    """Stock-level recommendation from the screener."""

    STRONG_BUY = "STRONG_BUY"     # Composite score > 80, analyst buy > 60%
    BUY = "BUY"                   # Composite score > 65, analyst buy > 50%
    ACCUMULATE = "ACCUMULATE"     # Composite score > 50, analyst buy > 40%
    WATCH = "WATCH"               # Composite score > 35, borderline
    AVOID = "AVOID"               # Composite score < 35 or MTF Tier 4


class SourceStatus(str, Enum):
    """Status of a data source fetch."""

    SUCCESS = "success"
    FALLBACK_USED = "fallback_used"
    STALE_DATA = "stale_data"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class SignalAction(str, Enum):
    """Trade action derived from score zone."""

    STRONG_BUY = "STRONG_BUY"       # 100% long
    BUY = "BUY"                     # 75% long
    ACCUMULATE = "ACCUMULATE"       # 50% long
    NEUTRAL = "NEUTRAL"             # 25% long
    REDUCE = "REDUCE"               # 10% long / defensive
    SELL = "SELL"                   # 0% long (flat)
    STRONG_SELL = "STRONG_SELL"     # 0% long, consider hedge

    @classmethod
    def from_score(cls, score: float) -> "SignalAction":
        """Map score to trading action."""
        zone = ScoreZone.from_score(score)
        mapping = {
            ScoreZone.EXTREME_BUY: cls.STRONG_BUY,
            ScoreZone.STRONG_BUY: cls.BUY,
            ScoreZone.BUY_LEAN: cls.ACCUMULATE,
            ScoreZone.NEUTRAL: cls.NEUTRAL,
            ScoreZone.SELL_LEAN: cls.REDUCE,
            ScoreZone.STRONG_SELL: cls.SELL,
            ScoreZone.EXTREME_SELL: cls.STRONG_SELL,
        }
        return mapping[zone]

    @property
    def exposure_pct(self) -> float:
        """Suggested equity exposure percentage for this action."""
        exposures = {
            SignalAction.STRONG_BUY: 1.0,
            SignalAction.BUY: 0.75,
            SignalAction.ACCUMULATE: 0.50,
            SignalAction.NEUTRAL: 0.25,
            SignalAction.REDUCE: 0.10,
            SignalAction.SELL: 0.0,
            SignalAction.STRONG_SELL: 0.0,
        }
        return exposures[self]

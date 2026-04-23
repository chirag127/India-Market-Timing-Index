"""MTF (Margin Trading Facility) safety calculator for Indian stocks.

Determines which stocks are safe for 3x leveraged MTF/pay-later trading
based on historical drawdowns, liquidity, and volatility.
"""

from __future__ import annotations

from typing import Any

from imti.config.settings import get_settings
from imti.core.enums import MTFSafetyTier
from imti.core.logger import get_logger

logger = get_logger("sources.mtf_safety")

# Historical max drawdown estimates for major Indian stocks
# Based on 2018, 2020, and 2022 market crashes
HISTORICAL_DRAWDOWNS: dict[str, float] = {
    "RELIANCE.NS": 35.0,
    "TCS.NS": 30.0,
    "HDFCBANK.NS": 32.0,
    "ICICIBANK.NS": 38.0,
    "INFY.NS": 28.0,
    "HINDUNILVR.NS": 22.0,
    "ITC.NS": 25.0,
    "SBIN.NS": 42.0,
    "BHARTIARTL.NS": 35.0,
    "KOTAKBANK.NS": 35.0,
    "LT.NS": 38.0,
    "AXISBANK.NS": 40.0,
    "BAJFINANCE.NS": 45.0,
    "ASIANPAINT.NS": 25.0,
    "MARUTI.NS": 35.0,
    "TITAN.NS": 32.0,
    "SUNPHARMA.NS": 28.0,
    "HCLTECH.NS": 30.0,
    "ULTRACEMCO.NS": 30.0,
    "WIPRO.NS": 32.0,
    "ONGC.NS": 45.0,
    "NTPC.NS": 30.0,
    "NESTLEIND.NS": 18.0,
    "POWERGRID.NS": 25.0,
    "ADANIENT.NS": 65.0,
    "TATAMOTORS.NS": 50.0,
    "TECHM.NS": 35.0,
    "COALINDIA.NS": 35.0,
    "GRASIM.NS": 38.0,
    "JSWSTEEL.NS": 48.0,
    "TATASTEEL.NS": 52.0,
    "M&M.NS": 38.0,
    "BAJAJFINSV.NS": 42.0,
    "HINDALCO.NS": 48.0,
    "CIPLA.NS": 28.0,
    "DRREDDY.NS": 25.0,
    "SBILIFE.NS": 32.0,
    "HDFCLIFE.NS": 28.0,
    "EICHERMOT.NS": 30.0,
    "BRITANNIA.NS": 22.0,
    "APOLLOHOSP.NS": 35.0,
    "ADANIPORTS.NS": 45.0,
    "BAJAJ-AUTO.NS": 28.0,
    "DIVISLAB.NS": 30.0,
    "TATACONSUM.NS": 28.0,
    "HEROMOTOCO.NS": 35.0,
    "INDUSINDBK.NS": 48.0,
    "UPL.NS": 42.0,
}

# Daily average volume in crores (estimated)
AVERAGE_VOLUME_CR: dict[str, float] = {
    "RELIANCE.NS": 800.0,
    "TCS.NS": 400.0,
    "HDFCBANK.NS": 600.0,
    "ICICIBANK.NS": 700.0,
    "INFY.NS": 500.0,
    "SBIN.NS": 900.0,
    "ITC.NS": 600.0,
    "BHARTIARTL.NS": 400.0,
    "TATAMOTORS.NS": 1200.0,
    "ADANIENT.NS": 800.0,
}


class MTFSafetyCalculator:
    """Calculates MTF safety metrics for individual stocks.

    With 3x leverage:
    - 10% stock fall = 30% capital loss
    - 20% stock fall = 60% capital loss (margin call likely)
    - 33% stock fall = 100% capital loss (total wipeout)

    Therefore we ONLY recommend stocks with max drawdown < 40%.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_tier(self, symbol: str) -> MTFSafetyTier:
        """Get MTF safety tier for a stock."""
        max_dd = self.get_max_drawdown(symbol)
        return MTFSafetyTier.from_drawdown(max_dd)

    def get_max_drawdown(self, symbol: str) -> float:
        """Get estimated max drawdown for a stock.

        First tries to compute from historical price data,
        falls back to hardcoded estimates.
        """
        # Try to compute from price history
        try:
            computed = self._compute_max_drawdown(symbol)
            if computed > 0:
                return computed
        except Exception as e:
            logger.debug(f"Could not compute drawdown for {symbol}: {e}")

        # Fallback to hardcoded estimates
        return HISTORICAL_DRAWDOWNS.get(symbol, 50.0)

    def _compute_max_drawdown(self, symbol: str) -> float:
        """Compute max drawdown from 5-year price history."""
        import yfinance as yf

        hist = yf.download(symbol, period="5y", interval="1wk", progress=False)
        if hist.empty or len(hist) < 52:
            return 0.0

        prices = hist["Close"].values
        peak = prices[0]
        max_dd = 0.0

        for price in prices[1:]:
            if price > peak:
                peak = price
            dd = (peak - price) / peak * 100
            if dd > max_dd:
                max_dd = dd

        return float(max_dd)

    def margin_call_distance(self, current_price: float, max_drawdown: float) -> float:
        """How far can the stock fall before hitting margin call?

        With 3x leverage (33% margin), margin call typically at ~25% equity.
        Stock can fall ~18-20% before margin call.
        """
        if max_drawdown <= 0:
            return 0.0

        # With 3x leverage, margin call when equity < 25% of position
        # Initial equity = 33.3%, so stock can fall ~18-20%
        # But using max drawdown as reference:
        # If max drawdown was 35%, current distance to that level
        margin_call_threshold = self.settings.mtf_margin_call_threshold * 100
        distance = max(0, margin_call_threshold - (max_drawdown - margin_call_threshold))
        return round(distance, 1)

    def break_even_days(self, current_price: float) -> int:
        """Estimated days to break even given daily interest cost.

        With 0.04% daily interest on borrowed 67%:
        - Daily cost = 0.04% * 0.67 = 0.0268% of position
        - Stock must rise 0.027% per day to break even
        - If expected daily move is 1%, break even in ~3 days
        """
        daily_interest = self.settings.mtf_interest_rate_annual / 365
        leverage = self.settings.mtf_leverage_multiplier
        borrowed_pct = (leverage - 1) / leverage
        daily_cost_pct = daily_interest * borrowed_pct * 100

        # Assume stock moves ~1% per day on average
        avg_daily_move = 1.0
        days = int(daily_cost_pct / avg_daily_move * 100) + 1
        return max(1, min(days, 30))

    def is_liquid(self, symbol: str) -> bool:
        """Check if stock has sufficient daily volume."""
        volume = AVERAGE_VOLUME_CR.get(symbol, 0)
        return volume >= 50.0  # Minimum 50 crore daily volume

    def risk_report(self, symbol: str) -> dict[str, Any]:
        """Generate full MTF risk report for a stock."""
        tier = self.get_tier(symbol)
        max_dd = self.get_max_drawdown(symbol)
        liquid = self.is_liquid(symbol)

        return {
            "symbol": symbol,
            "mtf_safety_tier": tier.value,
            "tier_name": tier.name,
            "is_mtf_safe": tier.is_mtf_safe,
            "max_drawdown_5y_pct": round(max_dd, 1),
            "is_liquid": liquid,
            "margin_call_distance_pct": round(self.margin_call_distance(0, max_dd), 1),
            "estimated_break_even_days": self.break_even_days(0),
            "warning": (
                "AVOID for MTF" if tier == MTFSafetyTier.TIER_4_RISKY
                else "Moderate risk" if tier == MTFSafetyTier.TIER_3_MODERATE
                else "Safe for MTF"
            ),
        }

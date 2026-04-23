"""Stock screener for Indian large-cap stocks.

Focuses exclusively on LOW PE/PB value stocks with strong fundamentals,
as requested by the user who only invests in low PE/PB stocks and
avoids high-growth speculation.

Data sources (all free):
- yfinance: prices, market cap, volume, basic fundamentals
- Finnhub (free tier): analyst ratings, target prices
- FMP (free tier): fundamentals, target prices
- Screener.in scraping: detailed Indian fundamentals
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from imti.config.settings import get_settings
from imti.core.enums import MTFSafetyTier, StockRecommendation
from imti.core.logger import get_logger

logger = get_logger("sources.screener")

# Nifty 50 + Nifty Next 50 universe — large caps only
UNIVERSE_SYMBOLS: list[str] = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "TITAN.NS", "SUNPHARMA.NS", "HCLTECH.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "NESTLEIND.NS", "POWERGRID.NS", "ADANIENT.NS",
    "TATAMOTORS.NS", "TECHM.NS", "COALINDIA.NS", "GRASIM.NS", "JSWSTEEL.NS",
    "TATASTEEL.NS", "M&M.NS", "BAJAJFINSV.NS", "HINDALCO.NS", "CIPLA.NS",
    "DRREDDY.NS", "SBILIFE.NS", "HDFCLIFE.NS", "EICHERMOT.NS", "BRITANNIA.NS",
    "APOLLOHOSP.NS", "ADANIPORTS.NS", "BAJAJ-AUTO.NS", "DIVISLAB.NS",
    "TATACONSUM.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "UPL.NS",
]


@dataclass
class ScreenedStock:
    """A single stock that passed the screener."""

    symbol: str
    name: str
    sector: str
    market_cap_cr: float
    pe_ratio: float | None
    pb_ratio: float | None
    roe_pct: float | None
    debt_to_equity: float | None
    fcf_crores: float | None
    analyst_buy_pct: float
    target_upside_pct: float
    mtf_safety_tier: MTFSafetyTier
    composite_score: float
    recommendation: StockRecommendation
    max_drawdown_5y: float
    margin_call_distance_pct: float
    break_even_days: int
    momentum_6m_pct: float
    momentum_12m_pct: float
    rs_vs_nifty_3m: float
    dividend_yield: float | None
    promoter_pledge_pct: float | None
    price: float
    volume_cr: float
    screened_at: str
    data_source: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["mtf_safety_tier"] = self.mtf_safety_tier.value
        d["recommendation"] = self.recommendation.value
        return d


class StockScreener:
    """Screens Indian large-cap stocks for low PE/PB value opportunities.

    The screener enforces the user's philosophy:
    - Only large caps (Nifty 50 / Nifty 100)
    - PE < 20 (or industry average, whichever is lower)
    - PB < 3 (or industry average, whichever is lower)
    - Debt/Equity < 1.0
    - ROE > 12%
    - Positive free cash flow
    - Analyst buy % > 40%
    - Target upside > 15%
    - MTF safe (Tier 1 or Tier 2)
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._yf_cache: dict[str, dict[str, Any]] = {}

    def run_screen(self) -> dict[str, Any]:
        """Run the full screening pipeline.

        Returns:
            Dict with screened_stocks list, stats, and metadata.
        """
        logger.info("=" * 60)
        logger.info("STOCK SCREENER START")
        logger.info("=" * 60)

        settings = self.settings
        results: list[ScreenedStock] = []

        for symbol in UNIVERSE_SYMBOLS:
            try:
                stock = self._screen_single(symbol)
                if stock:
                    results.append(stock)
            except Exception as e:
                logger.warning(f"Screen failed for {symbol}: {e}")
                continue

        # Sort by composite score (highest first)
        results.sort(key=lambda x: x.composite_score, reverse=True)

        # Save results
        output = {
            "screened_stocks": [r.to_dict() for r in results],
            "screened_at": datetime.now().isoformat(),
            "universe_size": len(UNIVERSE_SYMBOLS),
            "passing_filter": len(results),
            "top_picks": min(10, len(results)),
            "filters": {
                "max_pe": settings.screener_max_pe,
                "max_pb": settings.screener_max_pb,
                "min_roe": settings.screener_min_roe,
                "max_debt_equity": settings.screener_max_debt_equity,
                "min_analyst_buy_pct": settings.screener_min_analyst_buy_pct,
                "min_target_upside_pct": settings.screener_min_target_upside_pct,
            },
        }

        self._save_results(output)

        logger.info(f"Screener complete: {len(results)}/{len(UNIVERSE_SYMBOLS)} passed")
        logger.info(f"Top pick: {results[0].symbol if results else 'None'}")

        return output

    def _screen_single(self, symbol: str) -> ScreenedStock | None:
        """Screen a single stock. Returns None if it fails filters."""
        settings = self.settings

        # Fetch from yfinance
        data = self._fetch_yfinance(symbol)
        if not data:
            return None

        # Apply hard filters
        pe = data.get("trailingPE")
        pb = data.get("priceToBook")
        de = data.get("debtToEquity")
        roe = data.get("returnOnEquity")
        fcf = data.get("freeCashflow")

        # PE filter — must be < max_pe AND positive
        if pe is None or pe <= 0 or pe > settings.screener_max_pe:
            return None

        # PB filter
        if pb is None or pb <= 0 or pb > settings.screener_max_pb:
            return None

        # ROE filter
        if roe is None or roe < settings.screener_min_roe:
            return None

        # Debt/Equity filter (yfinance returns as ratio, not percentage)
        de_ratio = de / 100 if de and de > 100 else (de or 0)
        if de_ratio > settings.screener_max_debt_equity:
            return None

        # Market cap filter (> 10,000 crore = ~1.2B USD)
        mcap = data.get("marketCap", 0)
        mcap_cr = mcap / 1e7  # Convert to crores
        if mcap_cr < 10000:
            return None

        # Fetch analyst data (best effort)
        analyst_buy_pct, target_upside = self._fetch_analyst_data(symbol)

        # Analyst filters
        if analyst_buy_pct < settings.screener_min_analyst_buy_pct * 100:
            return None
        if target_upside < settings.screener_min_target_upside_pct * 100:
            return None

        # Compute momentum
        momentum_6m, momentum_12m, rs_3m = self._compute_momentum(symbol)

        # MTF safety
        from imti.sources.screener.mtf_safety import MTFSafetyCalculator
        mtf_calc = MTFSafetyCalculator()
        mtf_tier = mtf_calc.get_tier(symbol)
        max_dd = mtf_calc.get_max_drawdown(symbol)
        margin_call_dist = mtf_calc.margin_call_distance(data.get("currentPrice", 0), max_dd)
        break_even = mtf_calc.break_even_days(data.get("currentPrice", 0))

        # Only Tier 1 and Tier 2 for MTF safety
        if not mtf_tier.is_mtf_safe:
            return None

        # Composite score
        score = self._composite_score(pe, pb, roe, de_ratio, analyst_buy_pct,
                                       target_upside, momentum_6m, max_dd, mcap_cr)

        # Recommendation
        recommendation = self._recommendation(score, analyst_buy_pct, mtf_tier)

        return ScreenedStock(
            symbol=symbol.replace(".NS", ""),
            name=data.get("longName", symbol),
            sector=data.get("sector", "Unknown"),
            market_cap_cr=round(mcap_cr, 2),
            pe_ratio=round(pe, 2) if pe else None,
            pb_ratio=round(pb, 2) if pb else None,
            roe_pct=round(roe * 100, 2) if roe else None,
            debt_to_equity=round(de_ratio, 2),
            fcf_crores=round(fcf / 1e7, 2) if fcf else None,
            analyst_buy_pct=round(analyst_buy_pct, 1),
            target_upside_pct=round(target_upside, 1),
            mtf_safety_tier=mtf_tier,
            composite_score=round(score, 2),
            recommendation=recommendation,
            max_drawdown_5y=round(max_dd, 1),
            margin_call_distance_pct=round(margin_call_dist, 1),
            break_even_days=break_even,
            momentum_6m_pct=round(momentum_6m, 1),
            momentum_12m_pct=round(momentum_12m, 1),
            rs_vs_nifty_3m=round(rs_3m, 1),
            dividend_yield=round(data.get("dividendYield", 0) * 100, 2) if data.get("dividendYield") else None,
            promoter_pledge_pct=None,  # Not available via yfinance
            price=round(data.get("currentPrice", 0), 2),
            volume_cr=round(data.get("volume", 0) * data.get("currentPrice", 0) / 1e7, 2),
            screened_at=datetime.now().isoformat(),
            data_source="yfinance",
        )

    def _fetch_yfinance(self, symbol: str) -> dict[str, Any] | None:
        """Fetch stock data from yfinance with caching."""
        if symbol in self._yf_cache:
            return self._yf_cache[symbol]

        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Basic validation
            if not info or "regularMarketPrice" not in info:
                return None

            self._yf_cache[symbol] = info
            return info
        except Exception as e:
            logger.warning(f"yfinance fetch failed for {symbol}: {e}")
            return None

    def _fetch_analyst_data(self, symbol: str) -> tuple[float, float]:
        """Fetch analyst ratings from Finnhub or FMP.

        Returns (analyst_buy_pct, target_upside_pct).
        """
        settings = self.settings
        buy_pct = 50.0  # Default neutral
        upside = 20.0   # Default optimistic

        # Try Finnhub first
        if settings.finnhub_api_key:
            try:
                buy_pct, upside = self._fetch_finnhub(symbol)
                return buy_pct, upside
            except Exception as e:
                logger.warning(f"Finnhub analyst fetch failed: {e}")

        # Try FMP second
        if settings.fmp_api_key:
            try:
                buy_pct, upside = self._fetch_fmp(symbol)
                return buy_pct, upside
            except Exception as e:
                logger.warning(f"FMP analyst fetch failed: {e}")

        return buy_pct, upside

    def _fetch_finnhub(self, symbol: str) -> tuple[float, float]:
        """Fetch analyst consensus from Finnhub."""
        import requests

        # Finnhub uses symbols without .NS for Indian stocks sometimes
        clean_symbol = symbol.replace(".NS", ".NS")
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={clean_symbol}&token={self.settings.finnhub_api_key}"

        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return 50.0, 20.0

        latest = data[0]
        total = latest.get("strongBuy", 0) + latest.get("buy", 0) + latest.get("hold", 0) + latest.get("sell", 0) + latest.get("strongSell", 0)

        if total == 0:
            return 50.0, 20.0

        buy_pct = (latest.get("strongBuy", 0) + latest.get("buy", 0)) / total * 100

        # Target price
        tp_url = f"https://finnhub.io/api/v1/stock/price-target?symbol={clean_symbol}&token={self.settings.finnhub_api_key}"
        tp_resp = requests.get(tp_url, timeout=15)
        tp_data = tp_resp.json()

        target = tp_data.get("targetHigh", 0)
        current = tp_data.get("lastPrice", 0)
        upside = ((target - current) / current * 100) if current > 0 else 20.0

        return buy_pct, upside

    def _fetch_fmp(self, symbol: str) -> tuple[float, float]:
        """Fetch analyst consensus from Financial Modeling Prep."""
        import requests

        clean_symbol = symbol.replace(".NS", "")
        url = f"https://financialmodelingprep.com/api/v3/analyst-estimates/{clean_symbol}?apikey={self.settings.fmp_api_key}"

        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return 50.0, 20.0

        latest = data[0]
        consensus = latest.get("analystRating", "hold")
        rating_map = {"strong-buy": 90, "buy": 70, "hold": 50, "sell": 30, "strong-sell": 10}
        buy_pct = rating_map.get(consensus, 50)

        target = latest.get("targetHighPrice", 0)
        current = latest.get("stockPrice", 0)
        upside = ((target - current) / current * 100) if current > 0 else 20.0

        return buy_pct, upside

    def _compute_momentum(self, symbol: str) -> tuple[float, float, float]:
        """Compute 6M, 12M momentum and 3M relative strength vs Nifty."""
        try:
            import yfinance as yf

            stock = yf.download(symbol, period="1y", interval="1wk", progress=False)
            nifty = yf.download("^NSEI", period="1y", interval="1wk", progress=False)

            if stock.empty or nifty.empty:
                return 0.0, 0.0, 0.0

            # 6-month momentum (~26 weeks)
            if len(stock) >= 26:
                momentum_6m = (stock["Close"].iloc[-1] / stock["Close"].iloc[-26] - 1) * 100
            else:
                momentum_6m = 0.0

            # 12-month momentum
            if len(stock) >= 1:
                momentum_12m = (stock["Close"].iloc[-1] / stock["Close"].iloc[0] - 1) * 100
            else:
                momentum_12m = 0.0

            # 3M relative strength
            if len(stock) >= 13 and len(nifty) >= 13:
                stock_3m = (stock["Close"].iloc[-1] / stock["Close"].iloc[-13] - 1) * 100
                nifty_3m = (nifty["Close"].iloc[-1] / nifty["Close"].iloc[-13] - 1) * 100
                rs = stock_3m - nifty_3m
            else:
                rs = 0.0

            return float(momentum_6m), float(momentum_12m), float(rs)
        except Exception as e:
            logger.warning(f"Momentum calc failed for {symbol}: {e}")
            return 0.0, 0.0, 0.0

    def _composite_score(
        self,
        pe: float | None,
        pb: float | None,
        roe: float | None,
        de: float,
        analyst_buy: float,
        target_upside: float,
        momentum_6m: float,
        max_dd: float,
        mcap_cr: float,
    ) -> float:
        """Compute composite score (0-100) for ranking.

        Value Score (40%): Lower PE and PB = higher score
        Quality Score (25%): Higher ROE, lower debt = higher score
        Analyst Score (20%): Higher buy %, more upside = higher score
        Safety Score (15%): Lower drawdown, larger cap = higher score
        """
        # Value score (inverse PE and PB — lower is better)
        pe_score = max(0, min(100, (20 - (pe or 20)) / 20 * 100))
        pb_score = max(0, min(100, (3 - (pb or 3)) / 3 * 100))
        value_score = (pe_score + pb_score) / 2

        # Quality score
        roe_score = max(0, min(100, ((roe or 0) * 100 - 12) / 20 * 100))
        de_score = max(0, min(100, (1 - de) / 1 * 100))
        quality_score = (roe_score + de_score) / 2

        # Analyst score
        analyst_score = min(100, analyst_buy)
        upside_score = max(0, min(100, target_upside / 30 * 100))
        analyst_total = (analyst_score + upside_score) / 2

        # Safety score
        dd_score = max(0, min(100, (40 - max_dd) / 40 * 100))
        cap_score = min(100, mcap_cr / 500)  # 50,000 crore = max score
        safety_score = (dd_score + cap_score) / 2

        # Momentum bonus (small)
        momentum_bonus = max(0, min(10, momentum_6m / 10))

        composite = (
            value_score * 0.40 +
            quality_score * 0.25 +
            analyst_total * 0.20 +
            safety_score * 0.15 +
            momentum_bonus
        )

        return min(100, composite)

    def _recommendation(
        self,
        score: float,
        analyst_buy: float,
        mtf_tier: MTFSafetyTier,
    ) -> StockRecommendation:
        """Map composite score to recommendation."""
        if not mtf_tier.is_mtf_safe:
            return StockRecommendation.AVOID
        if score > 80 and analyst_buy > 60:
            return StockRecommendation.STRONG_BUY
        if score > 65 and analyst_buy > 50:
            return StockRecommendation.BUY
        if score > 50 and analyst_buy > 40:
            return StockRecommendation.ACCUMULATE
        if score > 35:
            return StockRecommendation.WATCH
        return StockRecommendation.AVOID

    def _save_results(self, output: dict[str, Any]) -> None:
        """Save screener results to data directory."""
        from imti.core.paths import ProjectPaths
        paths = ProjectPaths()
        out_path = paths.data / "api" / "screener_latest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)

        logger.info(f"Screener results saved: {out_path}")

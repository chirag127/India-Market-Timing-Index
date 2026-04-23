"""Snapshot fetcher — collects all indicator data from all sources.

This is the main entry point for data collection. It:
1. Registers all source connectors in the registry
2. Fetches all indicators with fallback resolution
3. Collects news headlines from RSS + search APIs
4. Runs LLM analysis on collected headlines (if enabled)
5. Produces a complete Snapshot object
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from imti.config.holidays import is_market_holiday, is_weekend
from imti.core.enums import IndicatorCategory, MarketStatus, RunType, SourceStatus
from imti.core.logger import get_logger
from imti.core.types import IndicatorValue, Snapshot, SourceHealth
from imti.core.validation import validate_indicator_value
from imti.sources.registry import SourceRegistry

logger = get_logger("ingestion.fetch")


def _determine_run_type() -> tuple[RunType, MarketStatus, bool]:
    """Determine the current run type and market status."""
    today = date.today()
    is_holiday = is_market_holiday(today)
    is_wkend = is_weekend(today)

    if is_holiday:
        return RunType.HOLIDAY, MarketStatus.HOLIDAY, True
    if is_wkend:
        return RunType.WEEKEND, MarketStatus.CLOSED, False

    # Check if market is currently open (IST 9:15 - 15:30)
    now = datetime.now()
    hour, minute = now.hour, now.minute
    if 9 <= hour < 15 or (hour == 9 and minute >= 15) or (hour == 15 and minute <= 30):
        return RunType.MARKET_HOURS, MarketStatus.OPEN, False
    return RunType.AFTER_HOURS, MarketStatus.CLOSED, False


def _register_all_sources(registry: SourceRegistry) -> None:
    """Register all available source connectors."""
    # Import and register each source
    # These are lazy imports to avoid circular dependencies and slow startup
    from imti.sources.tickertape.mmi import TickertapeMMISource
    from imti.sources.nse.market import NSEMarketSource
    from imti.sources.nse.options import NSEOptionsSource
    from imti.sources.yahoo.market import YahooFinanceSource
    from imti.sources.moneycontrol.headlines import MoneycontrolHeadlinesSource
    from imti.sources.nsdl.flows import NSDLFlowsSource
    from imti.sources.investing.econ import InvestingEconSource
    from imti.sources.bse.market import BSEMarketSource
    from imti.sources.rbi.rates import RBIRatesSource
    from imti.sources.amfi.sip import AMFISIPSource
    from imti.sources.tradingview.indicators import TradingViewSource
    from imti.sources.search.multi import MultiSearchSource
    from imti.sources.rss.feeds import RSSFeedsSource

    sources = [
        TickertapeMMISource(),
        NSEMarketSource(),
        NSEOptionsSource(),
        YahooFinanceSource(),
        MoneycontrolHeadlinesSource(),
        NSDLFlowsSource(),
        InvestingEconSource(),
        BSEMarketSource(),
        RBIRatesSource(),
        AMFISIPSource(),
        TradingViewSource(),
        MultiSearchSource(),
        RSSFeedsSource(),
    ]

    for source in sources:
        registry.register(source)

    logger.info(f"Registered {len(sources)} sources covering {registry.source_count} connectors")


def fetch_full_snapshot() -> Snapshot:
    """Fetch a complete snapshot of all available market data.

    This is the primary data collection function, called every hour
    by the pipeline.
    """
    run_type, market_status, is_holiday = _determine_run_type()
    timestamp = datetime.now()

    logger.info(f"Fetching snapshot: run_type={run_type}, market={market_status}")

    # Initialize registry and register all sources
    registry = SourceRegistry()
    _register_all_sources(registry)

    # Fetch all numeric indicators
    values, health_records = registry.fetch_all()

    # Build IndicatorValue objects with metadata
    indicators: dict[str, IndicatorValue] = {}
    for name, value in values.items():
        is_valid, clamped = validate_indicator_value(name, value)
        # Determine category based on indicator name prefix
        category = _infer_category(name)

        indicators[name] = IndicatorValue(
            name=name,
            category=category,
            value=clamped if clamped is not None else value,
            source_name="multi",  # Simplified — could track actual source
            fetch_timestamp=timestamp,
            validation_passed=is_valid,
        )

    # Collect all headlines (RSS + search + Moneycontrol)
    all_headlines: list[str] = []

    # RSS headlines — use fetch_list_indicator for non-scalar types
    rss_val, rss_health = registry.fetch_list_indicator("rss_headlines")
    if rss_val is not None:
        all_headlines.extend(rss_val)
    health_records.append(rss_health)

    # Search headlines
    search_val, search_health = registry.fetch_list_indicator("search_headlines")
    if search_val is not None:
        all_headlines.extend(search_val)
    health_records.append(search_health)

    # Moneycontrol headlines
    mc_val, mc_health = registry.fetch_list_indicator("moneycontrol_headlines")
    if mc_val is not None:
        all_headlines.extend(mc_val)
    health_records.append(mc_health)

    # Deduplicate headlines
    seen: set[str] = set()
    unique_headlines: list[str] = []
    for h in all_headlines:
        h_lower = h.lower().strip()
        if h_lower not in seen and len(h) > 15:
            seen.add(h_lower)
            unique_headlines.append(h)

    # Run LLM analysis if enabled and headlines are available
    llm_analysis: dict[str, Any] | None = None
    from imti.config.settings import get_settings
    settings = get_settings()

    if settings.enable_llm and unique_headlines:
        try:
            from imti.llm.analyzer import analyze_headlines
            llm_result = analyze_headlines(unique_headlines[:30])
            if llm_result:
                llm_analysis = llm_result.model_dump()
                # Add LLM-derived indicators
                indicators["llm_danger_score"] = IndicatorValue(
                    name="llm_danger_score",
                    category=IndicatorCategory.NEWS,
                    value=llm_result.danger_score,
                    source_name="llm",
                    fetch_timestamp=timestamp,
                )
                indicators["llm_panic_score"] = IndicatorValue(
                    name="llm_panic_score",
                    category=IndicatorCategory.NEWS,
                    value=llm_result.panic_score,
                    source_name="llm",
                    fetch_timestamp=timestamp,
                )
                indicators["llm_euphoria_score"] = IndicatorValue(
                    name="llm_euphoria_score",
                    category=IndicatorCategory.NEWS,
                    value=llm_result.euphoria_score,
                    source_name="llm",
                    fetch_timestamp=timestamp,
                )
                indicators["llm_opportunity_score"] = IndicatorValue(
                    name="llm_opportunity_score",
                    category=IndicatorCategory.NEWS,
                    value=llm_result.opportunity_score,
                    source_name="llm",
                    fetch_timestamp=timestamp,
                )
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")

    # Build snapshot
    snapshot = Snapshot(
        timestamp=timestamp,
        run_type=run_type,
        market_status=market_status,
        is_holiday=is_holiday,
        indicators=indicators,
        source_health=health_records,
        news_summary=" | ".join(unique_headlines[:10]),
        llm_analysis=llm_analysis,
        notes=f"Headlines collected: {len(unique_headlines)}, Indicators: {len(indicators)}",
    )

    logger.info(
        f"Snapshot complete: {len(indicators)} indicators, "
        f"{len(unique_headlines)} headlines, "
        f"{len([h for h in health_records if h.source_status == SourceStatus.SUCCESS])} sources OK"
    )

    return snapshot


def _infer_category(name: str) -> IndicatorCategory:
    """Infer indicator category from name."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["mmi", "fear_greed", "sentiment", "panic", "euphoria", "opportunity"]):
        return IndicatorCategory.SENTIMENT
    if any(kw in name_lower for kw in ["fii", "dii", "flow", "sip", "aum"]):
        return IndicatorCategory.FLOW
    if any(kw in name_lower for kw in ["advance", "decline", "breadth", "pct_above", "52w", "trin", "mcclellan"]):
        return IndicatorCategory.BREADTH
    if any(kw in name_lower for kw in ["rsi", "macd", "stochastic", "bollinger", "adx", "cci", "supertrend", "ema", "roc", "atr", "obv"]):
        return IndicatorCategory.TECHNICAL
    if any(kw in name_lower for kw in ["vix", "volatility", "pcr", "put_call", "skew"]):
        return IndicatorCategory.VOLATILITY
    if any(kw in name_lower for kw in ["yield", "repo", "crr", "cpi", "gdp", "usd_inr", "dxy", "brent", "gold", "crude", "rbi"]):
        return IndicatorCategory.MACRO
    if any(kw in name_lower for kw in ["pe", "pb", "earnings", "dividend", "mcap", "valuation"]):
        return IndicatorCategory.VALUATION
    if any(kw in name_lower for kw in ["llm", "news", "headline"]):
        return IndicatorCategory.NEWS
    return IndicatorCategory.TECHNICAL

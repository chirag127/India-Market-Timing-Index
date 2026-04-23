"""Tests for the stock screener module."""

from __future__ import annotations

import pytest

from imti.core.enums import MTFSafetyTier, StockRecommendation
from imti.sources.screener.mtf_safety import MTFSafetyCalculator
from imti.sources.screener.stock_screener import StockScreener


class TestMTFSafetyCalculator:
    """Tests for MTF safety calculations."""

    def test_get_tier_tier1(self) -> None:
        calc = MTFSafetyCalculator()
        tier = calc.get_tier("NESTLEIND.NS")
        assert tier == MTFSafetyTier.TIER_1_SAFEST
        assert tier.is_mtf_safe is True

    def test_get_tier_tier2(self) -> None:
        calc = MTFSafetyCalculator()
        # Use a stock with hardcoded drawdown in 30-40% range
        tier = calc.get_tier("MARUTI.NS")
        assert tier == MTFSafetyTier.TIER_2_SAFE
        assert tier.is_mtf_safe is True

    def test_get_tier_tier4(self) -> None:
        calc = MTFSafetyCalculator()
        tier = calc.get_tier("ADANIENT.NS")
        assert tier == MTFSafetyTier.TIER_4_RISKY
        assert tier.is_mtf_safe is False

    def test_break_even_days_positive(self) -> None:
        calc = MTFSafetyCalculator()
        days = calc.break_even_days(100.0)
        assert isinstance(days, int)
        assert 1 <= days <= 30

    def test_margin_call_distance(self) -> None:
        calc = MTFSafetyCalculator()
        dist = calc.margin_call_distance(100.0, 35.0)
        assert isinstance(dist, float)
        assert dist >= 0

    def test_is_liquid(self) -> None:
        calc = MTFSafetyCalculator()
        assert calc.is_liquid("RELIANCE.NS") is True
        assert calc.is_liquid("UNKNOWN.NS") is False

    def test_risk_report_structure(self) -> None:
        calc = MTFSafetyCalculator()
        report = calc.risk_report("TCS.NS")
        assert "symbol" in report
        assert "mtf_safety_tier" in report
        assert "is_mtf_safe" in report
        assert "warning" in report


class TestStockScreener:
    """Tests for the stock screener."""

    def test_composite_score_pe_only(self) -> None:
        screener = StockScreener()
        score = screener._composite_score(
            pe=10.0, pb=1.5, roe=0.20, de=0.1,
            analyst_buy=80.0, target_upside=30.0,
            momentum_6m=10.0, max_dd=25.0, mcap_cr=100000.0,
        )
        assert 0 <= score <= 100
        assert score > 60  # Good fundamentals should score high

    def test_composite_score_bad_stock(self) -> None:
        screener = StockScreener()
        score = screener._composite_score(
            pe=25.0, pb=4.0, roe=0.05, de=1.5,
            analyst_buy=20.0, target_upside=5.0,
            momentum_6m=-10.0, max_dd=55.0, mcap_cr=5000.0,
        )
        assert 0 <= score <= 100
        assert score < 40  # Bad fundamentals should score low

    def test_recommendation_strong_buy(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(85.0, 65.0, MTFSafetyTier.TIER_1_SAFEST)
        assert rec == StockRecommendation.STRONG_BUY

    def test_recommendation_avoid_mtf_unsafe(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(85.0, 65.0, MTFSafetyTier.TIER_4_RISKY)
        assert rec == StockRecommendation.AVOID

    def test_recommendation_buy(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(70.0, 55.0, MTFSafetyTier.TIER_2_SAFE)
        assert rec == StockRecommendation.BUY

    def test_recommendation_accumulate(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(55.0, 45.0, MTFSafetyTier.TIER_1_SAFEST)
        assert rec == StockRecommendation.ACCUMULATE

    def test_recommendation_watch(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(40.0, 35.0, MTFSafetyTier.TIER_2_SAFE)
        assert rec == StockRecommendation.WATCH

    def test_recommendation_avoid_low_score(self) -> None:
        screener = StockScreener()
        rec = screener._recommendation(20.0, 30.0, MTFSafetyTier.TIER_2_SAFE)
        assert rec == StockRecommendation.AVOID

    def test_screened_stock_to_dict(self) -> None:
        from datetime import datetime
        from imti.sources.screener.stock_screener import ScreenedStock
        stock = ScreenedStock(
            symbol="TCS",
            name="TCS Ltd",
            sector="IT",
            market_cap_cr=120000.0,
            pe_ratio=18.0,
            pb_ratio=2.8,
            roe_pct=25.0,
            debt_to_equity=0.0,
            fcf_crores=15000.0,
            analyst_buy_pct=70.0,
            target_upside_pct=18.0,
            mtf_safety_tier=MTFSafetyTier.TIER_1_SAFEST,
            composite_score=75.0,
            recommendation=StockRecommendation.BUY,
            max_drawdown_5y=28.0,
            margin_call_distance_pct=18.0,
            break_even_days=5,
            momentum_6m_pct=12.0,
            momentum_12m_pct=18.0,
            rs_vs_nifty_3m=3.0,
            dividend_yield=1.5,
            promoter_pledge_pct=0.0,
            price=3500.0,
            volume_cr=500.0,
            screened_at=datetime.now().isoformat(),
            data_source="yfinance",
        )
        d = stock.to_dict()
        assert d["symbol"] == "TCS"
        assert d["mtf_safety_tier"] == 1
        assert d["recommendation"] == "BUY"

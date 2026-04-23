"""Tests for core Pydantic types."""

from datetime import datetime

from imti.core.enums import IndexName, ScoreZone, SignalAction
from imti.core.types import IndexScore


def test_index_score_from_raw():
    """IndexScore.from_raw_score should create a proper score object."""
    score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=25.0,
        confidence=0.8,
        top_drivers=["tickertape_mmi", "india_vix"],
    )
    assert score.score == 25.0
    assert score.score_zone == ScoreZone.STRONG_BUY
    assert score.signal_action == SignalAction.BUY
    assert score.exposure_suggestion == 0.75
    assert len(score.top_drivers) == 2


def test_index_score_inverted_low():
    """Low score (e.g., 10) should map to EXTREME_BUY in inverted system."""
    score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=10.0,
        confidence=0.9,
    )
    assert score.score_zone == ScoreZone.EXTREME_BUY
    assert score.signal_action == SignalAction.STRONG_BUY
    assert score.exposure_suggestion == 1.0  # 100% equity


def test_index_score_inverted_high():
    """High score (e.g., 90) should map to EXTREME_SELL in inverted system."""
    score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=90.0,
        confidence=0.7,
    )
    assert score.score_zone == ScoreZone.EXTREME_SELL
    assert score.signal_action == SignalAction.STRONG_SELL
    assert score.exposure_suggestion == 0.0  # 0% equity — go flat


def test_index_score_neutral():
    """Score 50 should map to NEUTRAL."""
    score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=50.0,
        confidence=0.5,
    )
    assert score.score_zone == ScoreZone.NEUTRAL
    assert score.signal_action == SignalAction.NEUTRAL
    assert score.exposure_suggestion == 0.25


def test_index_score_boundary():
    """Score exactly at boundary should map to the lower zone."""
    score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=30.0,
        confidence=0.5,
    )
    assert score.score_zone == ScoreZone.STRONG_BUY  # 30 is in 16-30 range

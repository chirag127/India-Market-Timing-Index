"""Tests for core enums — especially the INVERTED score system."""

from imti.core.enums import ScoreZone, SignalAction


def test_score_zone_extreme_buy():
    """Score 0–15 should be EXTREME_BUY (inverted system)."""
    assert ScoreZone.from_score(0) == ScoreZone.EXTREME_BUY
    assert ScoreZone.from_score(15) == ScoreZone.EXTREME_BUY


def test_score_zone_strong_buy():
    """Score 16–30 should be STRONG_BUY."""
    assert ScoreZone.from_score(16) == ScoreZone.STRONG_BUY
    assert ScoreZone.from_score(30) == ScoreZone.STRONG_BUY


def test_score_zone_buy_lean():
    """Score 31–45 should be BUY_LEAN."""
    assert ScoreZone.from_score(31) == ScoreZone.BUY_LEAN
    assert ScoreZone.from_score(45) == ScoreZone.BUY_LEAN


def test_score_zone_neutral():
    """Score 46–55 should be NEUTRAL."""
    assert ScoreZone.from_score(46) == ScoreZone.NEUTRAL
    assert ScoreZone.from_score(55) == ScoreZone.NEUTRAL


def test_score_zone_sell_lean():
    """Score 56–69 should be SELL_LEAN."""
    assert ScoreZone.from_score(56) == ScoreZone.SELL_LEAN
    assert ScoreZone.from_score(69) == ScoreZone.SELL_LEAN


def test_score_zone_strong_sell():
    """Score 70–84 should be STRONG_SELL."""
    assert ScoreZone.from_score(70) == ScoreZone.STRONG_SELL
    assert ScoreZone.from_score(84) == ScoreZone.STRONG_SELL


def test_score_zone_extreme_sell():
    """Score 85–100 should be EXTREME_SELL."""
    assert ScoreZone.from_score(85) == ScoreZone.EXTREME_SELL
    assert ScoreZone.from_score(100) == ScoreZone.EXTREME_SELL


def test_score_zone_invalid():
    """Score outside 0–100 should raise ValueError."""
    import pytest
    with pytest.raises(ValueError):
        ScoreZone.from_score(-1)
    with pytest.raises(ValueError):
        ScoreZone.from_score(101)


def test_inverted_system_low_is_buy():
    """LOW scores = BUY zones (inverted system)."""
    assert ScoreZone.from_score(5).is_buy_zone
    assert ScoreZone.from_score(25).is_buy_zone
    assert not ScoreZone.from_score(5).is_sell_zone


def test_inverted_system_high_is_sell():
    """HIGH scores = SELL zones (inverted system)."""
    assert ScoreZone.from_score(80).is_sell_zone
    assert ScoreZone.from_score(95).is_sell_zone
    assert not ScoreZone.from_score(80).is_buy_zone


def test_signal_action_exposure():
    """SignalAction exposure should match inverted scoring."""
    # STRONG_BUY should have 100% exposure
    assert SignalAction.STRONG_BUY.exposure_pct == 1.0
    # SELL should have 0% exposure
    assert SignalAction.SELL.exposure_pct == 0.0
    # STRONG_SELL should also have 0%
    assert SignalAction.STRONG_SELL.exposure_pct == 0.0


def test_signal_action_from_score():
    """SignalAction.from_score should map correctly."""
    assert SignalAction.from_score(10) == SignalAction.STRONG_BUY
    assert SignalAction.from_score(50) == SignalAction.NEUTRAL
    assert SignalAction.from_score(90) == SignalAction.STRONG_SELL


def test_score_zone_colors():
    """ScoreZone should have hex color values."""
    assert ScoreZone.EXTREME_BUY.color.startswith("#")
    assert ScoreZone.STRONG_SELL.color.startswith("#")


def test_score_zone_emojis():
    """ScoreZone should have emoji representations."""
    assert "🟢" in ScoreZone.EXTREME_BUY.emoji
    assert "🔴" in ScoreZone.STRONG_SELL.emoji

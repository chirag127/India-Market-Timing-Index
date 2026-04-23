"""Tests for data validation utilities."""

from imti.core.validation import validate_indicator_value, clamp_value, safe_float


def test_validate_indicator_in_range():
    """Valid indicator values should pass validation."""
    is_valid, clamped = validate_indicator_value("tickertape_mmi", 50.0)
    assert is_valid is True
    assert clamped == 50.0


def test_validate_indicator_out_of_range():
    """Out-of-range values should be flagged."""
    is_valid, clamped = validate_indicator_value("tickertape_mmi", 150.0)
    assert is_valid is False
    assert clamped is None


def test_validate_indicator_at_boundaries():
    """Boundary values should be valid."""
    is_valid, clamped = validate_indicator_value("tickertape_mmi", 0.0)
    assert is_valid is True
    assert clamped == 0.0

    is_valid, clamped = validate_indicator_value("tickertape_mmi", 100.0)
    assert is_valid is True
    assert clamped == 100.0


def test_validate_unknown_indicator():
    """Unknown indicators should pass with a warning."""
    is_valid, clamped = validate_indicator_value("unknown_indicator_xyz", 42.0)
    assert is_valid is True
    assert clamped == 42.0


def test_clamp_value():
    """Clamping should restrict value to range."""
    assert clamp_value(150.0, 0, 100) == 100.0
    assert clamp_value(-10.0, 0, 100) == 0.0
    assert clamp_value(50.0, 0, 100) == 50.0


def test_safe_float_from_string():
    """safe_float should parse string numbers."""
    assert safe_float("42.5") == 42.5
    assert safe_float("1,000.5") == 0.0  # comma not handled — returns default


def test_safe_float_from_none():
    """safe_float should return default for None."""
    assert safe_float(None, default=99.0) == 99.0


def test_safe_float_from_invalid():
    """safe_float should return default for invalid strings."""
    assert safe_float("abc", default=0.0) == 0.0

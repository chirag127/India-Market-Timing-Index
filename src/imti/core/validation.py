"""Data validation utilities for indicator values."""

from imti.config.thresholds import INDICATOR_RANGES
from imti.core.logger import get_logger

logger = get_logger("validation")


def validate_indicator_value(name: str, value: float) -> tuple[bool, float | None]:
    """Validate an indicator value against its expected range.

    Returns:
        (is_valid, clamped_value) — if out of range, value is clamped or None.
    """
    if name not in INDICATOR_RANGES:
        # Unknown indicator — allow but warn
        logger.warning(f"Unknown indicator '{name}' — no validation range defined")
        return True, value

    low, high = INDICATOR_RANGES[name]

    if low <= value <= high:
        return True, value

    # Value is out of expected range
    logger.warning(
        f"Indicator '{name}' value {value} outside range [{low}, {high}] — flagging as invalid"
    )
    return False, None


def clamp_value(value: float, low: float, high: float) -> float:
    """Clamp a value to the given range."""
    return max(low, min(high, value))


def safe_float(raw: str | float | int | None, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    if raw is None:
        return default
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default

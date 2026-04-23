"""Base class for indicator computation modules.

Indicators transform raw data into normalized 0–100 values
suitable for the ML model. Each indicator category has its own
computation module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from imti.core.enums import IndicatorCategory
from imti.core.logger import get_logger
from imti.core.types import IndicatorValue


class BaseIndicatorModule(ABC):
    """Abstract base class for an indicator computation module.

    Subclasses compute and normalize indicators for a specific category.
    """

    category: IndicatorCategory = IndicatorCategory.TECHNICAL

    def __init__(self) -> None:
        self.logger = get_logger(f"indicator.{self.category.value}")

    @abstractmethod
    def compute(self, snapshot_data: dict[str, Any]) -> dict[str, IndicatorValue]:
        """Compute and normalize indicators from snapshot data.

        Args:
            snapshot_data: Dict of {indicator_name: raw_value}

        Returns:
            Dict of {indicator_name: IndicatorValue} with normalized values.
        """
        ...

    @staticmethod
    def normalize_percentile(value: float, historical_values: list[float]) -> float:
        """Normalize a value using percentile rank (0–100).

        Higher value = higher percentile = higher danger score.
        """
        if not historical_values:
            return 50.0  # Default to neutral
        count_below = sum(1 for v in historical_values if v < value)
        return (count_below / len(historical_values)) * 100.0

    @staticmethod
    def normalize_zscore(value: float, mean: float, std: float) -> float:
        """Normalize using z-score, then map to 0–100.

        Higher value = higher z-score = higher danger score.
        """
        if std == 0:
            return 50.0
        z = (value - mean) / std
        # Map z-score (-3 to +3) to 0–100
        return max(0.0, min(100.0, (z + 3) / 6 * 100))

    @staticmethod
    def normalize_minmax(value: float, min_val: float, max_val: float) -> float:
        """Normalize using min-max scaling to 0–100."""
        if max_val == min_val:
            return 50.0
        return max(0.0, min(100.0, (value - min_val) / (max_val - min_val) * 100))

    @staticmethod
    def invert_for_contrarian(normalized_value: float) -> float:
        """Invert a normalized value for contrarian interpretation.

        In our INVERTED system:
        - High MMI (greed) → high danger → HIGH score (sell)
        - Low MMI (fear) → low danger → LOW score (buy)
        So sentiment indicators map DIRECTLY (not inverted).

        But for some indicators like RSI:
        - Low RSI (oversold) → buy opportunity → LOW score
        - High RSI (overbought) → sell danger → HIGH score
        RSI also maps directly.

        This inversion is for indicators where the natural direction
        is opposite — e.g., PCR where high PCR = put-heavy = fear = buy.
        """
        return 100.0 - normalized_value

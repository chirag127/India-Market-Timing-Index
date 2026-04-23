"""Core type definitions for the IMTI system."""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from pydantic import BaseModel, Field

from imti.core.enums import (
    IndexName,
    IndicatorCategory,
    MarketStatus,
    RunType,
    ScoreZone,
    SignalAction,
    SourceStatus,
)


class SourceHealth(BaseModel):
    """Health/status record for a single data source fetch."""

    source_name: str
    fetch_timestamp: datetime
    source_status: SourceStatus
    latency_ms: float | None = None
    freshness_age_minutes: float | None = None
    validation_passed: bool = True
    fallback_triggered: bool = False
    fallback_source: str | None = None
    error_message: str | None = None


class IndicatorValue(BaseModel):
    """A single indicator reading with metadata."""

    name: str
    category: IndicatorCategory
    value: float | None = None
    normalized_value: float | None = None  # 0–100 scale
    source_name: str
    fetch_timestamp: datetime
    is_stale: bool = False
    freshness_minutes: float = 0.0
    validation_passed: bool = True

    @property
    def is_available(self) -> bool:
        """Whether this indicator has a valid value."""
        return self.value is not None and self.validation_passed and not self.is_stale


class IndexScore(BaseModel):
    """IMTI score for a single index."""

    index_name: IndexName
    score: float = Field(ge=0, le=100, description="0=strong buy, 100=strong sell (INVERTED)")
    confidence: float = Field(ge=0, le=1, description="Model confidence level")
    score_zone: ScoreZone
    signal_action: SignalAction
    exposure_suggestion: float = Field(ge=0, le=1, description="Suggested equity exposure 0–1")
    top_drivers: list[str] = Field(default_factory=list, description="Top 3 indicators driving score")
    timestamp: datetime

    @classmethod
    def from_raw_score(cls, index_name: IndexName, score: float, confidence: float,
                       top_drivers: list[str] | None = None,
                       timestamp: datetime | None = None) -> "IndexScore":
        """Create an IndexScore from a raw 0–100 score."""
        zone = ScoreZone.from_score(score)
        action = SignalAction.from_score(score)
        return cls(
            index_name=index_name,
            score=score,
            confidence=confidence,
            score_zone=zone,
            signal_action=action,
            exposure_suggestion=action.exposure_pct,
            top_drivers=top_drivers or [],
            timestamp=timestamp or datetime.now(),
        )


class Snapshot(BaseModel):
    """Complete snapshot of all data at a point in time."""

    timestamp: datetime
    run_type: RunType
    market_status: MarketStatus
    is_holiday: bool = False
    indices: dict[str, IndexScore] = Field(default_factory=dict)
    indicators: dict[str, IndicatorValue] = Field(default_factory=dict)
    source_health: list[SourceHealth] = Field(default_factory=list)
    news_summary: str | None = None
    llm_analysis: dict[str, Any] | None = None
    notes: str = ""

    @property
    def nifty_score(self) -> IndexScore | None:
        """Get Nifty 50 score if available."""
        return self.indices.get(IndexName.NIFTY_50.value)

    @property
    def stale_indicators(self) -> list[str]:
        """Names of indicators using stale data."""
        return [k for k, v in self.indicators.items() if v.is_stale]

    @property
    def failed_sources(self) -> list[str]:
        """Names of sources that failed."""
        return [
            h.source_name for h in self.source_health
            if h.source_status == SourceStatus.FAILED
        ]


class DailyBlogData(BaseModel):
    """Data structure for a daily blog page."""

    date: date
    opening_score: float | None = None
    closing_score: float | None = None
    score_range: tuple[float, float] | None = None
    hourly_scores: list[tuple[str, float]] = Field(default_factory=list)  # (time, score)
    key_events: list[str] = Field(default_factory=list)
    top_headlines: list[str] = Field(default_factory=list)
    llm_summary: str | None = None
    fii_dii_summary: dict[str, float] = Field(default_factory=dict)
    global_context: dict[str, float] = Field(default_factory=dict)
    breadth_snapshot: dict[str, float] = Field(default_factory=dict)
    derivatives_snapshot: dict[str, float] = Field(default_factory=dict)
    source_audit_summary: dict[str, Any] = Field(default_factory=dict)
    what_changed: str | None = None

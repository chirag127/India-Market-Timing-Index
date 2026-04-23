"""Pydantic schemas for LLM analysis outputs.

These schemas define the structured data that the LLM produces,
ensuring type safety and validation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NewsAnalysis(BaseModel):
    """Structured output from the LLM news analysis pipeline.

    IMPORTANT: The scoring system is INVERTED —
    panic/fear = buy opportunity → low danger_score
    euphoria/complacency = sell danger → high danger_score
    """

    raw_sentiment_score: float = Field(ge=0, le=100, description="0=extreme bearish, 100=extreme bullish")
    panic_score: float = Field(ge=0, le=100, description="Level of panic in news — contrarian buy signal")
    euphoria_score: float = Field(ge=0, le=100, description="Level of euphoria — contrarian sell signal")
    opportunity_score: float = Field(ge=0, le=100, description="Contrarian buy opportunity level")
    danger_score: float = Field(ge=0, le=100, description="Overall danger/sell risk — HIGH = should sell")
    time_horizon: str = Field(description="intraday | swing | macro")
    sector_impacts: dict[str, float] = Field(
        default_factory=dict,
        description="Sector → impact score (-1 to 1). E.g. banking: -0.5, it: 0.2",
    )
    key_events: list[str] = Field(default_factory=list, description="Key market-moving events detected")
    rationale: str = Field(default="", description="2-3 sentence explanation of the analysis")
    contrarian_note: str = Field(default="none", description="Specific contrarian opportunity if any")

    @classmethod
    def from_llm_response(cls, data: dict[str, Any]) -> "NewsAnalysis":
        """Create a NewsAnalysis from the LLM's JSON response, with defaults for missing fields."""
        return cls(
            raw_sentiment_score=float(data.get("raw_sentiment_score", 50)),
            panic_score=float(data.get("panic_score", 0)),
            euphoria_score=float(data.get("euphoria_score", 0)),
            opportunity_score=float(data.get("opportunity_score", 50)),
            danger_score=float(data.get("danger_score", 50)),
            time_horizon=str(data.get("time_horizon", "swing")),
            sector_impacts=data.get("sector_impacts", {}),
            key_events=data.get("key_events", []),
            rationale=str(data.get("rationale", "")),
            contrarian_note=str(data.get("contrarian_note", "none")),
        )

    @property
    def is_contrarian_buy(self) -> bool:
        """True if this analysis suggests a contrarian buy opportunity."""
        return self.panic_score > 60 or self.opportunity_score > 70

    @property
    def is_contrarian_sell(self) -> bool:
        """True if this analysis suggests euphoria/danger."""
        return self.euphoria_score > 60 or self.danger_score > 70


class SectorAnalysis(BaseModel):
    """Sector-specific risk analysis from the LLM."""

    sector: str
    risk_level: float = Field(ge=-1, le=1, description="-1=very bearish, 0=neutral, 1=very bullish")
    key_concern: str = ""
    opportunity: str = ""


class PolicyEvent(BaseModel):
    """Policy/regulatory event detected by the LLM."""

    event_type: str  # "rbi_policy", "budget", "sebi_action", "govt_reform", etc.
    description: str
    impact_assessment: str  # "bullish", "bearish", "neutral"
    affected_sectors: list[str] = Field(default_factory=list)
    severity: float = Field(ge=0, le=100, description="How significant this event is")


class GeopoliticalAssessment(BaseModel):
    """Geopolitical risk assessment from the LLM."""

    risk_score: float = Field(ge=0, le=100, description="0=no risk, 100=severe geopolitical risk")
    active_threats: list[str] = Field(default_factory=list, description="Active geopolitical concerns")
    market_impact: str = Field(default="minimal", description="minimal | moderate | severe")
    affected_markets: list[str] = Field(default_factory=list, description="Which markets are affected")

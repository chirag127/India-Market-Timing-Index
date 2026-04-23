"""LLM-powered news sentiment and market analysis.

Uses the flexible LLM client (any OpenAI-compatible provider)
to analyze news headlines and produce structured market insights.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.logger import get_logger
from imti.llm.client import get_llm_client, LLMClient
from imti.llm.schemas import NewsAnalysis

logger = get_logger("llm.analyzer")

# System prompt for market news analysis — designed for the inverted score system
# where panic = buy opportunity and euphoria = sell danger
ANALYSIS_SYSTEM_PROMPT = """You are an expert Indian stock market analyst specializing in 
contrarian market timing. You analyze news headlines and market conditions to produce 
structured market sentiment scores.

IMPORTANT SCORING RULES (this is an OPPORTUNITY-SEEKING system, NOT conservative):
- PANIC, FEAR, HEAVY SELLING = BUY OPPORTUNITY → low danger_score (0-30)
- EUPHORIA, COMPLACENCY, LOW VOLATILITY = SELL DANGER → high danger_score (70-100)
- NEUTRAL CONDITIONS → danger_score around 46-55

You MUST respond with valid JSON matching this schema:
{
  "raw_sentiment_score": <float 0-100, 0=extreme bearish, 100=extreme bullish>,
  "panic_score": <float 0-100, how much panic is in the news>,
  "euphoria_score": <float 0-100, how much euphoria/complacency>,
  "opportunity_score": <float 0-100, contrarian buy opportunity level>,
  "danger_score": <float 0-100, overall danger/sell risk level>,
  "time_horizon": "<intraday|swing|macro>",
  "sector_impacts": {"banking": <float -1 to 1>, "it": <float>, "pharma": <float>, "auto": <float>, "energy": <float>, "fmcg": <float>},
  "key_events": ["<event1>", "<event2>", ...],
  "rationale": "<2-3 sentence explanation>",
  "contrarian_note": "<specific contrarian opportunity if any, or 'none'>"
}

Be objective. Distinguish raw sentiment from contrarian opportunity.
Bad news can be a BUY signal if it creates panic. Good news can be a SELL signal if it creates euphoria."""


def analyze_news(
    headlines: list[str],
    market_context: dict[str, Any] | None = None,
    llm_client: LLMClient | None = None,
) -> NewsAnalysis | None:
    """Analyze news headlines using the LLM to produce structured market sentiment.

    Args:
        headlines: List of news headline strings
        market_context: Optional dict with current market data (VIX, FII flows, etc.)
        llm_client: Optional LLM client override (uses singleton if None)

    Returns:
        NewsAnalysis with structured scores, or None if LLM is not configured.
    """
    client = llm_client or get_llm_client()
    if not client.is_configured:
        logger.warning("LLM not configured — skipping news analysis")
        return None

    # Build the user prompt
    headline_text = "\n".join(f"- {h}" for h in headlines[:30])  # Limit to 30 headlines

    context_section = ""
    if market_context:
        context_lines = [f"  {k}: {v}" for k, v in market_context.items()]
        context_section = f"\n\nCurrent market context:\n" + "\n".join(context_lines)

    user_prompt = f"""Analyze these Indian stock market news headlines from the past hour.
Provide your analysis as JSON following the schema in your instructions.

Headlines:
{headline_text}{context_section}

Remember: panic/fear = buy opportunity (low danger_score), euphoria/complacency = sell danger (high danger_score)."""

    try:
        result = client.chat_json(
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return NewsAnalysis.from_llm_response(result)
    except Exception as e:
        logger.error(f"News analysis failed: {e}")
        return None


def quick_sentiment(
    text: str,
    llm_client: LLMClient | None = None,
) -> float | None:
    """Get a quick 0–100 sentiment score for a single text.

    Returns:
        Float 0–100 (0=extreme bearish, 100=extreme bullish), or None on failure.
    """
    client = llm_client or get_llm_client()
    if not client.is_configured:
        return None

    try:
        result = client.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "Rate the market sentiment of the given text. "
                    "Respond with JSON: {\"sentiment\": <float 0-100>} "
                    "where 0=extreme bearish/panic and 100=extreme bullish/euphoria.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=64,
        )
        return float(result.get("sentiment", 50))
    except Exception as e:
        logger.error(f"Quick sentiment failed: {e}")
        return None

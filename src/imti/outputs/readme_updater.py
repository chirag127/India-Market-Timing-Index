"""README updater — generates a living README with current IMTI score.

Updates README.md every pipeline run with the current score,
score chart, zone indicator, and last update timestamp.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from imti.core.enums import IndexName, ScoreZone
from imti.core.logger import get_logger
from imti.core.paths import get_project_root
from imti.core.types import IndexScore, Snapshot

logger = get_logger("outputs.readme")


def update_readme(score: IndexScore, snapshot: Snapshot) -> None:
    """Update the README.md with the current IMTI score and status."""
    root = get_project_root()
    readme_path = root / "README.md"

    # Build the new README content
    zone = score.score_zone
    timestamp_str = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S IST")

    content = f"""# India Market Timing Index (IMTI)

> AI-powered market timing signal for Indian equity markets

## Current Signal

| | |
|---|---|
| **Score** | **{score.score:.1f}** / 100 |
| **Zone** | {zone.emoji} {zone.value.replace('_', ' ').title()} |
| **Action** | {score.signal_action.value} |
| **Exposure** | {score.exposure_suggestion:.0%} equity |
| **Confidence** | {score.confidence:.0%} |
| **Last Updated** | {timestamp_str} |

### Score Interpretation (INVERTED — opportunity-seeking system)

| Range | Zone | Meaning |
|-------|------|---------|
| 0–15 | 🟢🟢 Extreme Buy | Maximum buy opportunity — fear/panic in market |
| 16–30 | 🟢 Strong Buy | Strong buy signal |
| 31–45 | 🟡🟢 Buy Lean | Leaning toward buying |
| 46–55 | 🟡 Neutral | No strong conviction |
| 56–69 | 🟡🔴 Sell Lean | Leaning toward selling |
| 70–84 | 🔴 Strong Sell | Strong sell / danger signal |
| 85–100 | 🔴🔴 Extreme Sell | Maximum danger — euphoria/complacency |

> **Note:** This system is NOT conservative. Low scores (0–30) indicate BUY opportunities
> (fear/panic in the market). High scores (70–100) indicate SELL/EXIT danger
> (euphoria/complacency). The system aggressively seeks opportunities.

## Architecture

- **50+ indicators** across 7 categories (Sentiment, Flow, Breadth, Technical, Volatility, Macro, Valuation)
- **45+ data sources** with fallback chains for redundancy
- **XGBoost model** with daily retraining and hourly inference
- **LLM-powered news analysis** for qualitative market assessment
- **Tickertape MMI** as the highest-weight sentiment indicator

## Data Sources

| Source | Provides | Priority |
|--------|----------|----------|
| NSE India | VIX, A/D, FII/DII, market data | Highest |
| Tickertape | Market Mood Index (MMI) | Highest |
| Yahoo Finance | Global indices, commodities, forex | High |
| NSDL | FII/DII cash flows (official) | High |
| BSE India | Sensex, breadth (fallback) | Medium |
| Moneycontrol | News headlines | Medium |
| Investing.com | India 10Y yield, P/E, P/B | Medium |
| RBI | Repo rate, monetary policy | Medium |
| AMFI | SIP flows, mutual fund data | Medium |
| RSS Feeds | News aggregation (free, reliable) | Medium |
| Search APIs | Google, Tavily, Brave, NewsAPI | Low |
| TradingView (computed) | 20+ technical indicators | Computed |

## Pipeline

- **Hourly** (GitHub Actions cron): Fetch → Indicators → Score → Save → Email → Commit
- **Daily** (GitHub Actions cron): Retrain model → Feature selection → Blog → Deploy

## Setup

```bash
# Install with uv
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the hourly pipeline
imti run

# Check current status
imti status
```

## License

MIT
"""

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"README updated with score {score.score:.1f} ({zone.value})")

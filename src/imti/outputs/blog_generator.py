"""Enhanced blog generator for hourly IMTI updates.

Generates markdown blog posts with:
- IMTI score and zone
- Top 10 low PE/PB stock picks from screener
- Changelog (what changed since last run)
- Sector analysis
- Macro outlook
- MTF risk alerts
- LLM news analysis

Posts are saved to data/blog/ and website/src/content/blog/
for static site generation.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from imti.config.settings import get_settings
from imti.core.enums import ScoreZone, SignalAction
from imti.core.logger import get_logger
from imti.core.paths import ProjectPaths, get_project_root

logger = get_logger("outputs.blog")


def generate_hourly_blog(
    score: float,
    confidence: float,
    snapshot: Any,
    screener_results: dict[str, Any] | None = None,
    previous_snapshot: Any | None = None,
) -> dict[str, Any]:
    """Generate an hourly blog post with changelog and stock picks.

    Args:
        score: Current IMTI score (0-100)
        confidence: Model confidence (0-1)
        snapshot: Current market snapshot
        screener_results: Output from StockScreener.run_screen()
        previous_snapshot: Previous snapshot for changelog computation

    Returns:
        Dict with paths to generated files.
    """
    settings = get_settings()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M")

    # Compute changelog
    changelog = _compute_changelog(snapshot, previous_snapshot)

    # Build markdown content
    md_content = _build_blog_markdown(
        now, score, confidence, snapshot, screener_results, changelog
    )

    # Save to data/blog/YYYY-MM-DD/
    blog_dir = Path("data/blog") / date_str
    blog_dir.mkdir(parents=True, exist_ok=True)
    md_path = blog_dir / f"{time_str}.md"
    md_path.write_text(md_content, encoding="utf-8")

    # Save to website/src/content/blog/ for Astro
    web_blog_dir = get_project_root() / "website" / "src" / "content" / "blog" / date_str
    web_blog_dir.mkdir(parents=True, exist_ok=True)
    web_md_path = web_blog_dir / f"{time_str}.md"
    web_md_path.write_text(md_content, encoding="utf-8")

    # Also save JSON for API consumption
    json_data = {
        "timestamp": now.isoformat(),
        "score": score,
        "zone": ScoreZone.from_score(score).value,
        "action": SignalAction.from_score(score).value,
        "confidence": confidence,
        "changelog": changelog,
        "screener_results": screener_results,
    }
    json_path = blog_dir / f"{time_str}.json"
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding="utf-8")

    logger.info(f"Hourly blog generated: {md_path}")
    return {"md_path": str(md_path), "json_path": str(json_path), "web_path": str(web_md_path)}


def _compute_changelog(
    current: Any | None,
    previous: Any | None,
) -> list[dict[str, Any]]:
    """Compute what changed between two snapshots."""
    changes: list[dict[str, Any]] = []

    if not current or not previous:
        return [{"type": "info", "message": "First run — no previous data for comparison."}]

    curr_ind = current.indicators if hasattr(current, "indicators") else {}
    prev_ind = previous.indicators if hasattr(previous, "indicators") else {}

    key_indicators = [
        ("tickertape_mmi", "Tickertape MMI", "{:.1f}"),
        ("india_vix", "India VIX", "{:.2f}"),
        ("nifty_pe", "Nifty PE", "{:.2f}"),
        ("nifty_pb", "Nifty PB", "{:.2f}"),
        ("fii_cash_net", "FII Net Flow", "{:.0f} Cr"),
        ("dii_cash_net", "DII Net Flow", "{:.0f} Cr"),
        ("put_call_ratio", "Put/Call Ratio", "{:.2f}"),
        ("usd_inr", "USD/INR", "{:.2f}"),
        ("us_10y_yield", "US 10Y Yield", "{:.2f}%"),
        ("brent_crude", "Brent Crude", "${:.2f}"),
    ]

    for key, label, fmt in key_indicators:
        if key in curr_ind and key in prev_ind:
            curr_val = curr_ind[key].value if hasattr(curr_ind[key], "value") else curr_ind[key]
            prev_val = prev_ind[key].value if hasattr(prev_ind[key], "value") else prev_ind[key]

            if curr_val is None or prev_val is None:
                continue

            diff = curr_val - prev_val
            if abs(diff) > 0.01:
                direction = "📈" if diff > 0 else "📉"
                changes.append({
                    "type": "indicator_change",
                    "label": label,
                    "old": fmt.format(prev_val),
                    "new": fmt.format(curr_val),
                    "diff": f"{diff:+.2f}",
                    "direction": direction,
                })

    # Score change
    if hasattr(current, "indices") and hasattr(previous, "indices"):
        curr_score = current.indices.get("nifty_50", {}).get("score", 50)
        prev_score = previous.indices.get("nifty_50", {}).get("score", 50)
        if abs(curr_score - prev_score) > 1:
            changes.insert(0, {
                "type": "score_change",
                "label": "IMTI Score",
                "old": f"{prev_score:.1f}",
                "new": f"{curr_score:.1f}",
                "diff": f"{curr_score - prev_score:+.1f}",
            })

    if not changes:
        changes.append({"type": "info", "message": "No significant changes since last update."})

    return changes


def _build_blog_markdown(
    timestamp: datetime,
    score: float,
    confidence: float,
    snapshot: Any,
    screener_results: dict[str, Any] | None,
    changelog: list[dict[str, Any]],
) -> str:
    """Build full markdown blog content."""
    zone = ScoreZone.from_score(score)
    action = SignalAction.from_score(score)
    date_str = timestamp.strftime("%B %d, %Y")
    time_str = timestamp.strftime("%H:%M IST")

    # Extract news/LLM data
    llm_score = 50.0
    llm_summary = "No LLM analysis available."
    key_events: list[str] = []

    if hasattr(snapshot, "news") and snapshot.news:
        llm_score = getattr(snapshot.news, "llm_score", 50.0)
        llm_summary = getattr(snapshot.news, "summary", llm_summary)
        key_events = getattr(snapshot.news, "key_events", [])

    # Build stock picks section
    stock_section = _build_stock_section(screener_results)

    # Build changelog section
    changelog_section = _build_changelog_section(changelog)

    # Build indicator table
    indicator_table = _build_indicator_table(snapshot)

    return f"""---
title: "IMTI Market Update — {date_str} {time_str}"
description: "India Market Timing Index hourly update. Score: {score:.1f} ({zone.value}). Action: {action.value}."
date: {timestamp.isoformat()}
zone: {zone.value}
score: {score:.1f}
confidence: {confidence:.2f}
action: {action.value}
---

# 📊 IMTI Market Update — {date_str} {time_str}

<div class="score-badge" style="background:{zone.color};color:#fff;padding:12px 24px;border-radius:8px;font-size:24px;font-weight:bold;text-align:center;margin:16px 0;">
  IMTI Score: {score:.1f} | {zone.value.upper().replace("_", " ")} {zone.emoji}
</div>

**Recommended Action:** `{action.value}` | **Equity Exposure:** {action.exposure_pct * 100:.0f}%

**Model Confidence:** {confidence * 100:.1f}%

---

## 🔄 Changelog (Since Last Update)

{changelog_section}

---

## 🏆 Top Low PE/PB Stock Picks

*These stocks passed our fundamental screener: PE < 20, PB < 3, ROE > 12%, Debt/Equity < 1, positive FCF, analyst buy > 40%, and MTF-safe.*

{stock_section}

---

## 📰 LLM News Analysis

**Bullish/Bearish Score:** {llm_score:.1f}/100

{llm_summary}

### 🔑 Key Events
{chr(10).join(f"- {e}" for e in key_events[:10]) if key_events else "- No major events detected."}

---

## 📈 Key Indicators

{indicator_table}

---

## ⚠️ MTF Risk Reminder

With **3x leverage** (MTF/Pay-Later):
- A **10%** stock fall = **30%** capital loss
- A **20%** stock fall = **60%** capital loss (margin call likely)
- A **33%** stock fall = **100%** capital loss (total wipeout)

**Only buy stocks in Tier 1 or Tier 2 MTF safety.**

---

## 📋 Methodology

The India Market Timing Index (IMTI) is a **fundamental-only, contrarian system**:
- **Low score (0-30)** = Market fear, cheap valuations = **BUY opportunity**
- **High score (70-100)** = Market euphoria, expensive valuations = **SELL/AVOID**
- We **only invest in large-cap, low PE/PB, debt-free** stocks
- Technical indicators are collected for display but have **zero weight** in scoring

---

*Generated automatically by IMTI pipeline at {timestamp.isoformat()}*
*This is NOT investment advice. For educational purposes only. SEBI disclaimer applies.*
"""


def _build_stock_section(screener_results: dict[str, Any] | None) -> str:
    """Build markdown table of top stock picks."""
    if not screener_results or not screener_results.get("screened_stocks"):
        return "_No stocks passed the fundamental filters today. Market may be overvalued._"

    stocks = screener_results["screened_stocks"][:10]
    lines = [
        "| # | Stock | Sector | PE | PB | ROE | Analyst Buy | Upside | MTF Tier | Score |",
        "|---|-------|--------|----|----|-----|-------------|--------|----------|-------|",
    ]

    for i, s in enumerate(stocks, 1):
        tier_emoji = "🟢" if s["mtf_safety_tier"] <= 2 else "🟡" if s["mtf_safety_tier"] == 3 else "🔴"
        lines.append(
            f"| {i} | **{s['symbol']}** | {s['sector']} | "
            f"{s['pe_ratio'] or '-'} | {s['pb_ratio'] or '-'} | "
            f"{s['roe_pct'] or '-'}% | {s['analyst_buy_pct']:.0f}% | "
            f"{s['target_upside_pct']:.0f}% | {tier_emoji} T{s['mtf_safety_tier']} | "
            f"{s['composite_score']:.1f} |"
        )

    # Add detail cards for top 3
    lines.append("\n### 🥇 Top 3 Details\n")
    for s in stocks[:3]:
        rec = s["recommendation"]
        lines.append(
            f"**{s['symbol']}** — {rec} (Score: {s['composite_score']:.1f})\n"
            f"- PE: {s['pe_ratio']}, PB: {s['pb_ratio']}, ROE: {s['roe_pct']}%\n"
            f"- Debt/Equity: {s['debt_to_equity']}, FCF: ₹{s['fcf_crores'] or 'N/A'} Cr\n"
            f"- Analyst Buy: {s['analyst_buy_pct']:.0f}%, Target Upside: {s['target_upside_pct']:.0f}%\n"
            f"- MTF Safety: Tier {s['mtf_safety_tier']}, Max Drawdown: {s['max_drawdown_5y']}%\n"
            f"- 6M Momentum: {s['momentum_6m_pct']:+.1f}%, RS vs Nifty: {s['rs_vs_nifty_3m']:+.1f}%\n"
            f"- Break-even (MTF): ~{s['break_even_days']} days of interest\n"
        )

    return "\n".join(lines)


def _build_changelog_section(changelog: list[dict[str, Any]]) -> str:
    """Build markdown list of changes."""
    if not changelog:
        return "_No changes detected._"

    lines = []
    for change in changelog:
        if change["type"] == "score_change":
            lines.append(
                f"- 🎯 **{change['label']}:** {change['old']} → **{change['new']}** ({change['diff']})"
            )
        elif change["type"] == "indicator_change":
            lines.append(
                f"- {change['direction']} **{change['label']}:** {change['old']} → **{change['new']}** ({change['diff']})"
            )
        else:
            lines.append(f"- ℹ️ {change['message']}")

    return "\n".join(lines)


def _build_indicator_table(snapshot: Any) -> str:
    """Build markdown table of key indicators."""
    if not hasattr(snapshot, "indicators"):
        return "_No indicator data available._"

    indicators = snapshot.indicators
    key_items = [
        ("tickertape_mmi", "Tickertape MMI", "{:.1f}"),
        ("india_vix", "India VIX", "{:.2f}"),
        ("nifty_pe", "Nifty 50 PE", "{:.2f}"),
        ("nifty_pb", "Nifty 50 PB", "{:.2f}"),
        ("earnings_yield", "Earnings Yield", "{:.2f}%"),
        ("dividend_yield", "Dividend Yield", "{:.2f}%"),
        ("fii_cash_net", "FII Net Flow", "₹{:.0f} Cr"),
        ("dii_cash_net", "DII Net Flow", "₹{:.0f} Cr"),
        ("put_call_ratio", "Put/Call Ratio", "{:.2f}"),
        ("usd_inr", "USD/INR", "{:.2f}"),
        ("us_10y_yield", "US 10Y Yield", "{:.2f}%"),
        ("brent_crude", "Brent Crude", "${:.2f}"),
        ("rbi_repo_rate", "RBI Repo Rate", "{:.2f}%"),
        ("cpi_inflation", "CPI Inflation", "{:.2f}%"),
    ]

    lines = ["| Indicator | Value |", "|-----------|-------|"]
    for key, label, fmt in key_items:
        if key in indicators:
            val = indicators[key].value if hasattr(indicators[key], "value") else indicators[key]
            if val is not None:
                lines.append(f"| {label} | {fmt.format(val)} |")

    return "\n".join(lines)


def generate_blog_index() -> str:
    """Generate a blog index page listing all blog posts."""
    blog_root = get_project_root() / "website" / "src" / "content" / "blog"
    if not blog_root.exists():
        return ""

    posts: list[tuple[datetime, str, str]] = []
    for date_dir in sorted(blog_root.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for md_file in sorted(date_dir.glob("*.md"), reverse=True):
            # Extract frontmatter date
            content = md_file.read_text(encoding="utf-8")
            date_line = [l for l in content.split("\n") if l.startswith("date:")]
            if date_line:
                post_date = datetime.fromisoformat(date_line[0].replace("date: ", "").strip())
                posts.append((post_date, str(md_file.relative_to(blog_root)), content[:200]))

    lines = ["# 📰 IMTI Blog Archive\n"]
    for dt, path, _ in posts[:100]:
        lines.append(f"- [{dt.strftime('%Y-%m-%d %H:%M')}] ({path})")

    index_path = blog_root / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return str(index_path)

# India Market Timing Index — Specification Document

> **Last Updated:** 2025-07-15
> **Status:** Draft
> **Repository:** Public GitHub repository

---

## 1. Project Overview

The **India Market Timing Index (IMTI)** is an AI-powered system that generates a continuous 0–100 score indicating whether one should be **long** (buy/hold equity exposure) or **flat** (sell/exit to cash) in the Indian stock market. The system combines **30+ quantitative indicators** with **LLM-powered news analysis** to produce a holistic market timing signal.

### Core Principles
- **Most of the time the signal will be SELL/flat** — the system is conservative, favoring capital preservation.
- **Sentiment & mood indicators (especially Tickertape MMI) carry the highest weight.**
- **Every data point is stored** in the repository for historical comparison, backtesting, and model improvement.
- **The ML model is regenerated daily** from all accumulated data; hourly runs perform inference only.
- **The system runs every hour**, even on non-trading days, because GIFT Nifty, global markets, and news events affect the next session.

---

## 2. Target Indices & Signal Interpretation

### Tracked Indices
| Index | Exchange | Purpose |
|-------|----------|---------|
| **Nifty 50** | NSE | Primary benchmark — main signal applies here |
| **Sensex (BSE 30)** | BSE | Secondary confirmation |
| **Nifty Bank** | NSE | Banking sector momentum signal |

### Signal Output
- **Format:** Continuous score **0–100** (no discrete BUY/SELL label)
- **Interpretation:**
  - **0–30:** Strong SELL — exit positions, go flat
  - **31–45:** SELL leaning — reduce exposure
  - **46–55:** NEUTRAL — no strong conviction either way
  - **56–70:** BUY leaning — gradually build positions
  - **71–100:** Strong BUY — full long exposure
- **Action mapping:** BUY = go long on index (futures/ETF), SELL = exit to cash (flat)
- **Signal is produced per index** — Nifty 50, Sensex, and Nifty Bank each get their own score

### Model Confidence
- Alongside the 0–100 score, the system reports **model confidence** (how certain the model is about its prediction)
- Low-confidence signals are flagged in the email for the user's discretion

---

## 3. Indicator Framework (30 Parameters)

Indicators are organized into **6 tiers** by category and weight. The Tickertape Market Mood Index (MMI) and custom Fear & Greed composite receive the **highest individual weight** in the model.

### Tier 1 — Sentiment & Mood (Weight: ~35%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 1 | **Tickertape Market Mood Index (MMI)** | Very High | 0–100 sentiment score for Indian markets. Updates every 3 min during market hours. Primary signal driver. | tickertape.in/market-mood-index | Web scrape (requests + BeautifulSoup) |
| 2 | **India VIX** | Very High | NSE volatility index. VIX >20 = panic/buy zone; <12 = complacency/sell zone. | NSE India | Scrape NSE or nsepy library |
| 3 | **CNN Fear & Greed Index** | Very High | Global sentiment proxy (0–100). Extreme fear (<20) → contrarian buy; extreme greed (>80) → sell. Highly correlated with FII behavior. | CNN Business website | Web scrape |
| 4 | **Custom India Fear & Greed Index** | Very High | Built from: PCR, VIX, 52-week highs/lows, market breadth, RSI, moving averages. India-specific composite. | Calculated from NSE data | Custom calculation from scraped components |
| 5 | **Put/Call Ratio (PCR)** | High | PCR >1.2 = bullish contrarian; <0.7 = bearish contrarian. Options market sentiment is very accurate. | NSE options chain | Scrape NSE derivatives data |

### Tier 2 — Institutional Flow (Weight: ~25%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 6 | **FII/DII Net Flows** | Very High | Foreign institutional buying/selling is the single biggest market driver. Sustained FII selling = strong sell signal. | NSE / SEBI daily data | Scrape NSE reports page |
| 7 | **FII F&O Positions** | High | FII net long/short in index futures — leading indicator, often moves 1–2 days ahead of cash market. | NSE participant-wise OI | Scrape NSE participant data |
| 8 | **Mutual Fund SIP Flows** | Medium | Monthly SIP inflows act as a floor for the market. Rising SIP data = demand support on dips. | AMFI monthly report | Scrape AMFI website |

### Tier 3 — Technical & Market Breadth (Weight: ~20%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 9 | **Nifty vs 200 DMA** | High | Price vs 200-day MA — most reliable long-term trend signal. Below = bear market; above = bull market. | Yahoo Finance / yfinance | yfinance API |
| 10 | **Advance-Decline Ratio** | Medium | Breadth indicator. Nifty rises but A/D falls = weak rally, likely to reverse. | NSE market breadth | Scrape NSE market stats |
| 11 | **Nifty RSI (14-day)** | Medium | RSI >75 = overbought sell zone; <30 = oversold buy zone. Best used with other signals. | Calculated from OHLC | Custom calculation from yfinance data |
| 12 | **52-Week Highs vs Lows** | Medium | More stocks hitting new lows than highs = bear market breadth confirmation. | NSE market stats page | Scrape NSE |
| 13 | **Nifty MACD** | Medium | Trend strength and momentum confirmation. | Calculated from OHLC | Custom calculation |
| 14 | **Bollinger Band Position** | Low | Where Nifty sits relative to Bollinger Bands — squeeze/expansion signals. | Calculated from OHLC | Custom calculation |

### Tier 4 — Macro & Global (Weight: ~15%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 15 | **USD/INR & DXY** | High | Rising dollar = FII outflows. DXY >105 historically negative for emerging markets. | Yahoo Finance | yfinance API |
| 16 | **US 10-Year Bond Yield** | High | Rising yields = FIIs move capital to US bonds. Biggest macro risk for Indian equities. | FRED API / Yahoo Finance | FRED API or yfinance |
| 17 | **Crude Oil Price (Brent)** | Medium | India imports 80%+ of oil. Crude >$90 = inflationary pressure, RBI tightening risk. | Yahoo Finance | yfinance API |
| 18 | **S&P 500 Trend** | Medium | Global risk-on/off. S&P corrects >5%, India typically follows within days. | Yahoo Finance | yfinance API |
| 19 | **RBI Repo Rate / Stance** | Medium | Rate hike cycle = bearish; rate cut cycle = bullish. Monitor MPC outcomes. | RBI website | Scrape RBI press releases |
| 20 | **India CPI Inflation** | Low | CPI >6% = RBI forced to hike, negative for markets. Monthly data — low frequency. | MOSPI / RBI | Scrape MOSPI releases |

### Tier 5 — Valuation (Weight: ~5%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 21 | **Nifty 50 P/E Ratio** | High | Historical avg ~20x. Above 24x = expensive/sell; below 16x = cheap/buy. Most reliable long-term valuation gauge. | NSE website | Scrape NSE |
| 22 | **Nifty P/B Ratio** | Medium | Price-to-book. Above 4x = overvalued; below 2.5x = undervalued. | NSE website | Scrape NSE |
| 23 | **Market Cap to GDP (Buffett Indicator)** | Low | Above 100% = market expensive. Very slow-moving, for regime detection only. | NSE total mcap / GDP data | Scrape + manual GDP input |

### Tier 6 — LLM News Analysis (Weight: ~10%)

| # | Indicator | Weight | Description | Data Source | Scrape/API Method |
|---|-----------|--------|-------------|-------------|-------------------|
| 24 | **LLM Bullish/Bearish News Score** | High | LLM analyzes aggregated news headlines and returns a 0–100 bullish/bearish score with reasoning. | Search APIs → LLM API | Search API + LLM API (keys in GitHub Secrets) |
| 25 | **News Sentiment Aggregate** | Medium | Aggregated sentiment from multiple news sources, stored as structured data. | Multiple search APIs | Search API responses stored as JSON |
| 26 | **GIFT Nifty Movement** | Medium | Overnight GIFT Nifty (SGX Nifty) movement indicates opening direction. | GIFT Nifty / SGX data | Scrape or API |
| 27 | **Global Market Overnight Changes** | Medium | US market close, Asian markets open — captures overnight risk. | Yahoo Finance | yfinance API |
| 28 | **Sector-Specific News Flags** | Low | LLM identifies sector-specific risks (banking, IT, pharma, auto). | Search APIs → LLM API | Search API + LLM API |
| 29 | **Policy/Regulatory Event Detection** | Low | LLM flags major policy changes, budget announcements, SEBI actions. | Search APIs → LLM API | Search API + LLM API |
| 30 | **Geopolitical Risk Score** | Low | LLM assesses geopolitical tensions affecting markets (wars, sanctions, trade disputes). | Search APIs → LLM API | Search API + LLM API |

---

## 4. Architecture

### 4.1 High-Level System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS (Hourly)                │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  SCRAPERS │  │ LLM NEWS  │  │  COMPUTE │             │
│  │ (30 ind.) │→ │ ANALYSIS  │→ │ INDICATORS│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                      │                   │
│                              ┌──────▼──────┐            │
│                              │  ML MODEL   │            │
│                              │ (Inference) │            │
│                              └──────┬──────┘            │
│                                     │                    │
│              ┌──────────────┬───────┴────────┐          │
│              ▼              ▼                ▼          │
│        ┌──────────┐  ┌──────────┐  ┌──────────────┐     │
│        │ CSV DATA  │  │ JSON API  │  │ EMAIL ALERT  │     │
│        │ (commit)  │  │ (commit)  │  │ (SMTP/API)   │     │
│        └──────────┘  └──────────┘  └──────────────┘     │
│              │              │                            │
│              ▼              ▼                            │
│     ┌─────────────────────────────┐                      │
│     │  ASTRO WEBSITE (Build)      │                      │
│     │  → Deploy to Cloudflare     │                      │
│     │     Pages                    │                      │
│     └─────────────────────────────┘                      │
└─────────────────────────────────────────────────────────┘

Daily (2:00 AM IST):
  ┌──────────────────┐
  │  FULL MODEL       │
  │  RETRAIN          │
  │  + BACKTEST       │
  │  VALIDATION       │
  └──────────────────┘
```

### 4.2 Project Directory Structure

```
india-market-timing-index/
├── .github/
│   └── workflows/
│       ├── hourly-signal.yml        # Hourly scraping + inference + email
│       ├── daily-retrain.yml        # Daily full retrain + backtest
│       └── deploy-website.yml       # Build & deploy Astro site to Cloudflare Pages
├── src/
│   ├── scrapers/
│   │   ├── tickertape_mmi.py        # Tickertape MMI scraper
│   │   ├── nse_data.py              # NSE: prices, VIX, PCR, OI, FII/DII, breadth
│   │   ├── nse_options.py           # NSE options chain for PCR
│   │   ├── yahoo_finance.py         # Global markets, commodities, forex
│   │   ├── cnn_fear_greed.py        # CNN Fear & Greed Index scraper
│   │   ├── rbi_data.py              # RBI repo rate scraper
│   │   ├── amfi_data.py             # AMFI SIP flow data
│   │   ├── mospi_data.py            # CPI inflation data
│   │   ├── gift_nifty.py            # GIFT Nifty / SGX data
│   │   └── search_news.py           # Search API news aggregator
│   ├── indicators/
│   │   ├── technical.py             # RSI, MACD, Bollinger, A/D, 52wk H/L
│   │   ├── sentiment.py             # Custom India F&G composite calculator
│   │   ├── institutional.py         # FII/DII flow processing
│   │   ├── macro.py                 # Macro indicator normalizers
│   │   └── valuation.py             # P/E, P/B, MCap/GDP processing
│   ├── llm/
│   │   ├── news_analyzer.py         # LLM-powered news sentiment analysis
│   │   ├── sector_analyzer.py       # Sector-specific risk detection
│   │   ├── policy_detector.py       # Policy/regulatory event detection
│   │   └── geopolitical_scorer.py   # Geopolitical risk assessment
│   ├── model/
│   │   ├── trainer.py               # Model training (daily full retrain)
│   │   ├── predictor.py             # Hourly inference
│   │   ├── feature_engineer.py      # Feature construction from 30 indicators
│   │   └── labeler.py               # Training label generation (future returns)
│   ├── backtest/
│   │   ├── engine.py                # Backtesting engine
│   │   ├── metrics.py               # Performance metrics (Sharpe, drawdown, etc.)
│   │   └── reports.py               # Backtest report generation
│   ├── notifications/
│   │   ├── email_sender.py          # Email composition and sending
│   │   └── templates/
│   │       ├── hourly_digest.html   # Hourly email template
│   │       └── signal_alert.html    # Signal change alert template
│   ├── storage/
│   │   ├── csv_writer.py            # CSV data storage
│   │   ├── json_api.py              # JSON API endpoint data generation
│   │   └── git_committer.py         # Automated git commit/push from Actions
│   └── config/
│       ├── settings.py              # Central configuration
│       ├── indicators_config.yaml   # Indicator definitions, weights, thresholds
│       └── holidays.py              # Indian market holiday calendar
├── data/
│   ├── signals/
│   │   ├── nifty_50.csv             # Daily signal history for Nifty 50
│   │   ├── sensex.csv               # Daily signal history for Sensex
│   │   └── nifty_bank.csv           # Daily signal history for Nifty Bank
│   ├── indicators/
│   │   └── hourly/                  # Hourly indicator snapshots
│   │       ├── YYYY-MM-DD.csv       # One file per day with hourly rows
│   │       └── ...
│   ├── news/
│   │   ├── YYYY-MM-DD.json          # Daily news scrape results + LLM analysis
│   │   └── ...
│   ├── api/
│   │   ├── latest.json              # Current signal + all indicator values
│   │   ├── history.json             # Last 30 days of signals
│   │   └── backtest.json            # Latest backtest results
│   └── backtest/
│       └── report.json              # Latest backtest performance metrics
├── website/                         # Astro framework project
│   ├── astro.config.mjs
│   ├── package.json
│   ├── src/
│   │   ├── layouts/
│   │   │   └── Layout.astro
│   │   ├── pages/
│   │   │   ├── index.astro          # Main dashboard
│   │   │   ├── history.astro        # Historical signals & charts
│   │   │   ├── news.astro           # News archive & analysis
│   │   │   ├── backtest.astro       # Backtest results
│   │   │   └── api/
│   │   │       ├── latest.json.ts   # JSON API endpoint
│   │   │       └── history.json.ts  # JSON API endpoint
│   │   ├── components/
│   │   │   ├── SignalGauge.astro    # 0-100 gauge visualization
│   │   │   ├── IndicatorTable.astro # All 30 indicators table
│   │   │   ├── SignalChart.astro    # Signal vs Nifty overlay chart
│   │   │   ├── NewsTimeline.astro   # News events timeline
│   │   │   └── BacktestReport.astro # Backtest performance display
│   │   └── styles/
│   │       └── global.css
│   └── public/
│       └── favicon.svg
├── tests/
│   ├── test_scrapers.py
│   ├── test_indicators.py
│   ├── test_model.py
│   └── test_backtest.py
├── .env.example                     # Template for all required env vars/secrets
├── .gitignore
├── pyproject.toml                   # Python project config (uv)
├── uv.lock                          # Lock file for reproducibility
├── README.md                        # Living dashboard — updated every run
└── india-market-timing-index-spec.md  # This spec file
```

---

## 5. GitHub Actions Workflows

### 5.1 Hourly Signal Workflow (`hourly-signal.yml`)

- **Schedule:** Every hour, 24/7 (including non-trading days — global news and GIFT Nifty matter)
- **Cron:** `0 * * * *` (UTC, every hour)
- **Steps:**
  1. Checkout repository
  2. Setup Python (via uv)
  3. Install dependencies
  4. Run all scrapers (30 indicators)
  5. Run search API news fetching
  6. Run LLM news analysis
  7. Compute all indicator values
  8. Run model inference (load latest model from artifact or retrain-quickly)
  9. Store data point in CSV + JSON API files
  10. Store news scrape results in `data/news/`
  11. Generate signal
  12. Send email (hourly digest or signal-change alert)
  13. Update README.md with latest charts
  14. Commit and push data + README changes
  15. Trigger Astro website build (if data changed)

### 5.2 Daily Retrain Workflow (`daily-retrain.yml`)

- **Schedule:** 2:00 AM IST daily (`30 20 * * *` UTC — previous day 20:30)
- **Steps:**
  1. Checkout repository
  2. Setup Python (via uv)
  3. Install dependencies
  4. Load ALL historical data from CSVs
  5. Generate training labels (future returns-based)
  6. Feature engineering on all 30 indicators
  7. Full model retrain
  8. Run backtest on historical data
  9. Generate backtest report
  10. Store model metadata (not the model binary — regenerated each time)
  11. Store backtest results in `data/backtest/`
  12. Commit and push

### 5.3 Deploy Website Workflow (`deploy-website.yml`)

- **Trigger:** After hourly-signal completes (workflow_run) or manual
- **Steps:**
  1. Checkout repository
  2. Setup Node.js
  3. Build Astro website
  4. Deploy to Cloudflare Pages

### GitHub Actions Compute Budget Considerations
- ~720 hourly runs/month × ~5 min each ≈ 3,600 min/month
- ~30 daily retrain runs × ~15 min each ≈ 450 min/month
- ~30 website deploys × ~3 min each ≈ 90 min/month
- **Total: ~4,140 min/month** — exceeds free tier (2,000 min). User may need GitHub Pro or to optimize.

---

## 6. Machine Learning Model

### 6.1 Model Selection

**Primary model: XGBoost (Gradient Boosted Decision Trees)**
- Best suited for tabular data with 30 features
- Handles mixed feature scales well
- Interpretable — can show feature importance (which indicators drove the signal)
- Fast training and inference — fits GitHub Actions time/compute constraints
- Robust to missing values (some indicators may be unavailable on certain runs)

**Fallback/ensemble addition: Random Forest** for variance reduction

### 6.2 Training Labels (Future Returns-Based)

The model learns from historical data what the "correct" signal would have been:

- **Label computation:** For each historical data point, look ahead N days and compute the Nifty 50 return
- **Binary classification approach:**
  - If Nifty rose >1.5% in next 5 trading days → label = 1 (should have been long)
  - If Nifty fell >1.5% in next 5 trading days → label = 0 (should have been flat)
  - If change was between -1.5% and +1.5% → label = previous state (momentum continuation)
- **Regression alternative:** Predict the actual future return value, then map to 0–100 scale
- **Avoid look-ahead bias:** In production, model only sees current indicator values, never future data

### 6.3 Feature Engineering

- **Normalization:** Each indicator normalized to 0–100 scale using historical min/max or percentile ranks
- **Missing value handling:** XGBoost handles natively; for other models, use forward-fill or median
- **Time features:** Day of week, month, days since last holiday, pre/post-expiry week
- **Lagged features:** Include 1-day, 3-day, 5-day, and 10-day lagged values of key indicators
- **Interaction features:** FII flow × VIX, PCR × MMI, P/E × bond yield (key combinations)

### 6.4 Model Output

- **Raw prediction:** Probability of positive future returns (0.0 – 1.0)
- **Scaled output:** Map to 0–100 continuous score
- **Confidence:** Model's prediction probability distance from 0.5 (closer to 0 or 1 = higher confidence)
- **Top drivers:** SHAP values or feature importance to identify which indicators drove the signal

### 6.5 Daily Retraining Strategy

- **Full retrain** every day at 2:00 AM IST using ALL accumulated historical data
- **Hourly runs** only perform inference (no retraining) — fast and lightweight
- **Model artifact:** NOT pushed to repository (regenerated each time from data)
- **Model metadata IS stored:** version, hyperparameters, feature importance, training metrics

---

## 7. Data Storage

### 7.1 CSV Format (Daily Signal History)

**File:** `data/signals/nifty_50.csv`

| Column | Type | Description |
|--------|------|-------------|
| date | date | Trading date |
| open_time_score | float | Score at market open (9:15 AM) |
| close_time_score | float | Score at market close (3:30 PM) |
| final_daily_score | float | End-of-day consolidated score |
| confidence | float | Model confidence (0–1) |
| signal_action | string | "STRONG_SELL" / "SELL" / "NEUTRAL" / "BUY" / "STRONG_BUY" |
| nifty_close | float | Nifty 50 closing price |
| mmi | float | Tickertape MMI value |
| india_vix | float | India VIX value |
| cnn_fg | float | CNN Fear & Greed value |
| custom_fg | float | Custom India F&G value |
| pcr | float | Put-Call Ratio |
| fii_net | float | FII net flow (crores) |
| dii_net | float | DII net flow (crores) |
| fii_fo_position | float | FII F&O net position |
| sip_flow | float | Monthly SIP flow (crores) |
| nifty_vs_200dma | float | % distance from 200 DMA |
| adv_decline_ratio | float | Advance-Decline ratio |
| rsi_14 | float | RSI(14) value |
| highs_vs_lows | float | 52-week highs vs lows ratio |
| macd | float | MACD value |
| bollinger_position | float | Position within Bollinger Bands (0–1) |
| usd_inr | float | USD/INR exchange rate |
| dxy | float | Dollar Index value |
| us_10yr_yield | float | US 10-year bond yield (%) |
| brent_crude | float | Brent crude oil price |
| sp500_change | float | S&P 500 daily change (%) |
| rbi_repo_rate | float | RBI repo rate (%) |
| cpi_inflation | float | India CPI inflation (%) |
| nifty_pe | float | Nifty 50 P/E ratio |
| nifty_pb | float | Nifty P/B ratio |
| mcap_to_gdp | float | Market cap to GDP ratio |
| llm_news_score | float | LLM bullish/bearish news score (0–100) |
| news_sentiment | float | Aggregated news sentiment |
| gift_nifty_change | float | GIFT Nifty overnight change (%) |
| global_overnight | float | Global market overnight change (%) |
| sector_risk_flags | string | JSON: sector risk flags from LLM |
| policy_event | string | LLM-detected policy event (or "none") |
| geopolitical_score | float | Geopolitical risk score (0–100) |
| top_driver_1 | string | #1 indicator driving the signal |
| top_driver_2 | string | #2 indicator driving the signal |
| top_driver_3 | string | #3 indicator driving the signal |
| is_holiday | bool | Whether market was closed this day |
| model_version | string | Model version identifier |
| notes | string | Any special notes (budget day, expiry, etc.) |

### 7.2 CSV Format (Hourly Indicator Snapshots)

**File:** `data/indicators/hourly/YYYY-MM-DD.csv`

Same columns as above but with additional:
- `timestamp` (ISO 8601)
- `run_type` ("market_hours" / "after_hours" / "holiday")

### 7.3 JSON API Files

**`data/api/latest.json`** — Current state:
```json
{
  "timestamp": "2025-07-15T14:30:00+05:30",
  "indices": {
    "nifty_50": { "score": 42.3, "confidence": 0.71, "action": "SELL" },
    "sensex": { "score": 45.1, "confidence": 0.68, "action": "NEUTRAL" },
    "nifty_bank": { "score": 38.7, "confidence": 0.74, "action": "SELL" }
  },
  "indicators": { "...": "all 30 indicator current values" },
  "top_drivers": ["mmi", "fii_net", "india_vix"],
  "llm_analysis": {
    "news_score": 35.2,
    "summary": "FII selling continues, global uncertainty rising...",
    "sector_flags": { "banking": "negative", "it": "neutral" },
    "policy_events": "none",
    "geopolitical_risk": 45
  },
  "market_status": "open"
}
```

**`data/api/history.json`** — Last 30 days of daily scores

**`data/api/backtest.json`** — Latest backtest results

### 7.4 News Data Storage

**`data/news/YYYY-MM-DD.json`** — Daily news archive:
```json
{
  "date": "2025-07-15",
  "search_results": [
    { "source": "search_api_1", "query": "India stock market today", "results": [...] },
    { "source": "search_api_2", "query": "FII flows India", "results": [...] }
  ],
  "llm_analysis": {
    "overall_sentiment": "bearish",
    "score": 35,
    "key_events": ["RBI policy meeting tomorrow", "FII net sellers 5th day"],
    "sector_impact": { "banking": "negative", "pharma": "positive" },
    "reasoning": "..."
  }
}
```

---

## 8. LLM News Analysis Pipeline

### 8.1 Search API Integration

- **Multiple search APIs** for comprehensive coverage:
  - Primary: Google Custom Search API, or Tavily Search API, or Brave Search API
  - Fallback: NewsAPI.org, or Bing News Search API
- **Search queries** (run every hour):
  - "India stock market today"
  - "Nifty 50 outlook"
  - "FII flows India"
  - "RBI policy announcement"
  - "India economy news"
  - "GIFT Nifty live"
  - "Asian markets today"
  - "US market close"
  - "crude oil price India"
  - "geopolitical risk emerging markets"
- **API keys stored in GitHub Secrets** (user will configure)

### 8.2 LLM Analysis

- **LLM API:** OpenAI GPT / Anthropic Claude / other (user provides API key via GitHub Secrets)
- **Input:** Aggregated search results + headlines
- **Output:**
  - Overall bullish/bearish score (0–100)
  - Key events summary
  - Sector-specific risk flags
  - Policy/regulatory event detection
  - Geopolitical risk assessment
  - Brief reasoning (2–3 sentences)
- **Prompt engineering:** Carefully designed to be objective, data-driven, not sensationalist
- **Rate limiting:** LLM called once per hourly run (not per search query) — batch all news into one analysis

### 8.3 News Storage

- All raw search results stored in `data/news/YYYY-MM-DD.json`
- All LLM analysis outputs stored alongside search results
- This creates a **news archive** that can be:
  - Displayed on the website
  - Used for future model training (news sentiment as a feature)
  - Audited for accuracy

---

## 9. Email Notification System

### 9.1 Email Provider

- **Recommended:** SendGrid (free tier: 100 emails/day, reliable, professional)
- **Fallback:** Gmail SMTP with App Password
- **Credentials:** Stored in GitHub Secrets (`SENDGRID_API_KEY` or `EMAIL_ADDRESS` + `EMAIL_PASSWORD`)

### 9.2 Email Types

#### Hourly Digest (sent every hour)
- **Subject:** `IMTI Update: Nifty 50 Score XX | [ACTION] | [Confidence XX%]`
- **Contents:**
  - Current 0–100 score for each index (Nifty 50, Sensex, Nifty Bank)
  - Confidence level
  - Top 3 drivers of the signal
  - Key indicator values (MMI, VIX, FII/DII, PCR, P/E, custom F&G)
  - LLM news summary (2–3 sentences + key events)
  - GIFT Nifty movement (if after hours)
  - Market status (open/closed/holiday)
  - Comparison with previous hour's score (change arrow ↑↓→)

#### Signal Change Alert (sent immediately when score crosses threshold)
- **Triggers:** Score moves from one zone to another (e.g., NEUTRAL → SELL)
- **Subject:** `⚠️ IMTI SIGNAL CHANGE: [FROM] → [TO] | Nifty Score: XX`
- **Contents:**
  - Previous and current score
  - What changed (which indicators shifted)
  - LLM analysis of what's driving the change
  - Recommended action

### 9.3 Email Design

- HTML formatted, mobile-responsive
- Color-coded: Red for sell zones, green for buy zones, yellow for neutral
- Compact layout — scannable in 10 seconds
- Include mini sparkline charts for key indicators (embedded as base64 images)

---

## 10. Website (Astro on Cloudflare Pages)

### 10.1 Framework

- **Astro** (latest stable version) — static site generator with island architecture
- **React** for interactive components (charts, gauges)
- **Charting:** Chart.js or Plotly.js for interactive visualizations
- **Styling:** Tailwind CSS
- **Deployment:** Cloudflare Pages (connected to GitHub repo, auto-deploys on push)

### 10.2 Pages

#### Dashboard (Home — `/`)
- **Signal Gauge:** Large semi-circular gauge showing current 0–100 score
- **Signal for each index:** Nifty 50, Sensex, Nifty Bank with scores and actions
- **Key indicators at a glance:** MMI, VIX, FII/DII, PCR, P/E (as cards with trend arrows)
- **LLM News Summary:** Latest AI-generated market analysis
- **Last updated:** Timestamp of most recent run

#### Historical Signals (`/history`)
- **Interactive chart:** Signal score (0–100) overlaid on Nifty 50 price
- **Date range selector:** 1 week / 1 month / 3 months / 1 year / All time
- **Signal zone coloring:** Red/green bands on the chart
- **Indicator correlation view:** Compare any indicator vs signal over time

#### News Archive (`/news`)
- **Timeline of news:** Each day's search results and LLM analysis
- **Date picker** to browse historical news
- **Sentiment trend chart:** LLM news score over time
- **Key events highlighted:** Major market-moving events tagged

#### Backtest Results (`/backtest`)
- **Performance metrics:** Sharpe ratio, max drawdown, win rate, CAGR
- **Equity curve:** Simulated portfolio growth following IMTI signals
- **Buy & Hold comparison:** IMTI strategy vs simple buy-and-hold
- **Signal distribution:** Histogram of historical scores

#### JSON API Endpoints
- `/api/latest.json` — Current signal + all indicators
- `/api/history.json` — Historical daily data
- `/api/backtest.json` — Backtest results

### 10.3 README as Living Dashboard

The `README.md` is updated every hourly run with:
- **Current signal badge** (GitHub-flavored markdown badge with color)
- **Latest score** with timestamp
- **Embedded charts** (as SVG or base64 PNG from matplotlib/plotly)
- **Mini indicator table** (top 10 indicators)
- **Last 7-day signal chart**
- **Link to full website**

---

## 11. Backtesting System

### 11.1 Backtesting Engine

- **Essential feature** — included from the start
- **Method:** Walk-forward backtest on accumulated historical data
- **Simulation:** Starting with ₹1,000,000, follow the IMTI signal:
  - Score >55: Invest 100% in Nifty 50 (simulated via Nifty total return index)
  - Score 46–55: Invest 50% in Nifty, 50% in cash (liquid fund returns ~5% annualized)
  - Score <46: 100% cash (liquid fund)
- **Transaction costs:** 0.1% per entry/exit (brokerage + impact)
- **Slippage:** Assumed 0.05% per trade

### 11.2 Performance Metrics

- **Sharpe Ratio** (annualized, risk-free = 6% India RBI bond yield)
- **Sortino Ratio** (downside deviation only)
- **Maximum Drawdown** (% from peak to trough)
- **CAGR** (Compound Annual Growth Rate)
- **Win Rate** (% of trades that were profitable)
- **Average trade return**
- **Comparison vs Buy & Hold Nifty 50**
- **Calmar Ratio** (CAGR / Max Drawdown)

### 11.3 Reporting

- Backtest results stored in `data/backtest/report.json`
- Updated daily after model retrain
- Displayed on website `/backtest` page
- Included in weekly email summary

---

## 12. Environment & Secrets Configuration

### 12.1 `.env.example` (committed to repository)

```env
# === Search APIs ===
SEARCH_API_1_KEY=your_google_custom_search_api_key
SEARCH_API_1_CX=your_google_custom_search_cx
SEARCH_API_2_KEY=your_tavily_api_key
SEARCH_API_3_KEY=your_brave_search_api_key

# === LLM API ===
LLM_API_KEY=your_openai_or_anthropic_api_key
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# === Email ===
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_FROM=imti@example.com
EMAIL_TO=your_email@example.com

# === Cloudflare Pages ===
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id

# === Optional Data APIs ===
FRED_API_KEY=your_fred_api_key
YAHOO_FINANCE_API_KEY=  # Usually not needed, yfinance is free

# === GitHub ===
GITHUB_TOKEN=  # Auto-provided by GitHub Actions
```

### 12.2 GitHub Secrets (configured in repo Settings)

All values from `.env.example` should be configured as GitHub Secrets. The hourly workflow references them as environment variables:

```yaml
env:
  SEARCH_API_1_KEY: ${{ secrets.SEARCH_API_1_KEY }}
  LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
  SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
  # ... etc
```

### 12.3 Public Repository Considerations

- **Never commit API keys, tokens, or credentials** — only `.env.example` template
- **Data stored in repository** is all derived/analyzed data (scores, indicators, news) — no raw credentials
- **Model binary NOT stored** — regenerated each time
- **Scraper source code IS public** — websites may block if they see the code, so use appropriate User-Agent headers

---

## 13. Holiday & Non-Trading Day Handling

- **Indian market holidays** (NSE/BSE): ~15–20 per year (Republic Day, Holi, Diwali, etc.)
- **Holiday calendar:** Stored in `src/config/holidays.py`, updated annually
- **On holidays:**
  - GitHub Actions still runs (global news and GIFT Nifty matter)
  - Market data uses **previous trading day's closing values**
  - CSV row flagged `is_holiday = true`
  - Email notes "MARKET CLOSED — signal based on previous close + global factors"
  - LLM news analysis still runs (overnight global events affect next session)
- **Half-day sessions:** Flagged separately (e.g., Muhurat Trading on Diwali)

---

## 14. Error Handling & Resilience

### 14.1 Scraper Failures

- If a specific scraper fails (site blocks, timeout, CAPTCHA):
  - Log the failure with timestamp and error details
  - Use **last known value** for that indicator (forward-fill)
  - Flag in CSV/email: "⚠️ [INDICATOR] using stale data (last updated: [TIME])"
  - Continue with all other indicators — don't fail the entire run

### 14.2 Rate Limiting

- **Respectful scraping:** Add delays between requests, use appropriate User-Agent
- **API rate limits:** Track usage, implement backoff/retry logic
- **NSE anti-scraping:** NSE blocks automated requests — may need to:
  - Rotate User-Agent headers
  - Use session cookies (NSE requires initial cookie fetch)
  - Fallback to nsepy library if direct scraping fails

### 14.3 GitHub Actions Failures

- If a workflow run fails:
  - Don't send a failure email (avoid noise)
  - Log the error in a `data/errors/` directory
  - Next successful run will pick up where it left off
  - Add `workflow_dispatch` trigger for manual re-runs

### 14.4 Data Validation

- **Sanity checks on scraped data:**
  - VIX should be between 5 and 80
  - MMI should be between 0 and 100
  - PCR should be between 0.1 and 5.0
  - FII flows should be between -10,000 and +10,000 crores
  - P/E should be between 5 and 50
- If a value is outside expected range, flag it and use last known good value

---

## 15. Python Tech Stack

### 15.1 Core Dependencies

| Package | Purpose |
|---------|---------|
| `uv` | Package manager (as specified by user) |
| `pandas` | Data manipulation and storage |
| `numpy` | Numerical operations |
| `requests` | HTTP requests for scraping |
| `beautifulsoup4` | HTML parsing for scraping |
| `yfinance` | Yahoo Finance data (free) |
| `nsepy` / `nsetools` | NSE India data |
| `xgboost` | ML model (gradient boosted trees) |
| `scikit-learn` | Feature engineering, metrics, preprocessing |
| `shap` | Feature importance / explainability |
| `matplotlib` | Chart generation for README |
| `plotly` | Interactive chart generation for website |
| `jinja2` | HTML email template rendering |
| `pyyaml` | Configuration file parsing |
| `python-dotenv` | Environment variable loading |
| `sendgrid` | Email sending (or `smtplib` for Gmail) |
| `openai` / `anthropic` | LLM API client |
| `lxml` | Fast XML/HTML processing |

### 15.2 Development Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `pytest-cov` | Test coverage |
| `ruff` | Linting + formatting |
| `mypy` | Type checking |

---

## 16. Website Tech Stack

| Technology | Purpose |
|------------|---------|
| **Astro** (latest) | Static site framework |
| **React** | Interactive components (islands) |
| **Tailwind CSS** | Styling |
| **Chart.js** or **Plotly.js** | Interactive charts |
| **Cloudflare Pages** | Hosting & deployment |

---

## 17. Implementation Phases

### Phase 1 — Foundation (Week 1–2)
- [ ] Project setup (uv, pyproject.toml, .env.example, directory structure)
- [ ] Core scraper infrastructure with error handling
- [ ] Top 5 scrapers: Tickertape MMI, NSE (prices, VIX), Yahoo Finance, FII/DII
- [ ] Custom India F&G Index calculator
- [ ] CSV data storage + git auto-commit
- [ ] Basic XGBoost model with initial training labels
- [ ] GitHub Actions hourly workflow

### Phase 2 — Full Indicators + Model (Week 3–4)
- [ ] All remaining scrapers (CNN F&G, PCR, RBI, AMFI, MOSPI, GIFT Nifty)
- [ ] All technical indicator calculators (RSI, MACD, Bollinger, A/D)
- [ ] All macro/valuation indicator processing
- [ ] Full 30-parameter feature engineering pipeline
- [ ] Daily retrain workflow
- [ ] Email notification system (hourly digest + signal alerts)

### Phase 3 — LLM News Analysis (Week 5–6)
- [ ] Search API integration (multiple providers)
- [ ] LLM news analysis pipeline
- [ ] News data storage
- [ ] Sector risk + policy event + geopolitical detection
- [ ] LLM score integration into model features

### Phase 4 — Backtesting + Validation (Week 7–8)
- [ ] Backtesting engine
- [ ] Performance metrics calculation
- [ ] Walk-forward validation
- [ ] Backtest reporting

### Phase 5 — Website + Dashboard (Week 9–12)
- [ ] Astro project setup with Cloudflare Pages
- [ ] Signal gauge + dashboard page
- [ ] Historical charts page
- [ ] News archive page
- [ ] Backtest results page
- [ ] JSON API endpoints
- [ ] README living dashboard (charts, badges)
- [ ] Mobile-responsive design
- [ ] Professional frontend design (use frontend-design skill)

### Phase 6 — Polish & Production (Week 13+)
- [ ] Comprehensive error handling and resilience testing
- [ ] Data validation and anomaly detection
- [ ] Performance optimization (scraper caching, incremental CSV writes)
- [ ] Documentation (README, contributing guide, AGENTS.md)
- [ ] Unit and integration tests
- [ ] Monitoring and alerting for workflow failures

---

## 18. Key Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Signal format | Continuous 0–100 score | Nuanced, no hard thresholds, user interprets |
| Target indices | Nifty 50 + Sensex + Nifty Bank | Comprehensive coverage of Indian markets |
| Action type | Long/Flat | Conservative — sell means exit to cash, not short |
| ML model | XGBoost | Best for tabular data, interpretable, fast |
| Training labels | Future returns-based | Objective, avoids subjective labeling |
| Retrain frequency | Daily full + hourly inference | Balanced compute/accuracy tradeoff |
| Data storage | CSV (daily) + JSON API | Git-friendly, human-readable, queryable |
| Highest weight indicator | Tickertape MMI | User's explicit preference — mood drives Indian markets |
| LLM integration | Search API → LLM analysis | Captures qualitative factors that numbers miss |
| Runs on holidays | Yes | GIFT Nifty + global news affect next session |
| Email approach | Hourly digest + signal change alerts | Comprehensive but not overwhelming |
| Email provider | SendGrid (recommended) | Free tier sufficient, reliable, professional |
| Package manager | uv | User preference — modern, fast |
| Website framework | Astro + React + Cloudflare Pages | Fast, modern, free hosting |
| Repository visibility | Public | Keep secrets in GitHub Secrets only |

---

## 19. Open Questions / Future Considerations

1. **GitHub Actions compute budget:** ~4,140 min/month exceeds free tier (2,000 min). User may need GitHub Pro or optimization (e.g., skip after-hours runs on some days).
2. **Scraper reliability:** NSE actively blocks scrapers. May need to maintain multiple fallback strategies.
3. **Model cold start:** With no historical data initially, the model needs bootstrapping. Consider pre-populating with 2–3 years of historical data.
4. **LLM cost:** GPT-4o-mini is cheap (~$0.15/1M input tokens) but 24 calls/day × 30 days = ~720 LLM calls/month. Monitor costs.
5. **Signal latency:** Scraping + LLM + inference may take 5–10 minutes. Signal is not truly "real-time."
6. **Regulatory considerations:** This is a personal tool, not investment advice. Add appropriate disclaimers.
7. **Data volume growth:** CSV files will grow over years. Consider yearly archiving or switching to Parquet for large datasets.

---

Continue making Repository And project and ensure that we have a common Ai and point for the open ai Alan MAPI, we can change the base URL and API key and Whenever we want to change the model and everything, we can change the model by api key And the base URL in the environment variables
Gather all the relevant context and then spawn @thinker-gpt Think about how to implement the following:

Look at the Spec and create a plan, proper plan, with the everything proper plan And all Please ensure that everything is done correctly Search the Web for paper everything Search the web for more research paper on how to detect the Market moving How to which papers which research paper are there for the Stock market product Predictions
*End of specification document. This spec should be reviewed and updated as the project evolves.*

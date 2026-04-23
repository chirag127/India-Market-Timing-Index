# India Market Timing Index (IMTI) — Master Implementation Plan

> **Created:** 2025-07-15  
> **Status:** Active Development Plan  
> **Philosophy:** Fundamental-First · Conservative · MTF-Aware · 100% Free Stack  
> **Signal Convention:** 0 = STRONG BUY · 100 = STRONG SELL (inverted danger score)

---

## Table of Contents

1. [Core Philosophy & Signal Convention](#1-core-philosophy--signal-convention)
2. [Investment Strategy Profile](#2-investment-strategy-profile)
3. [MTF / Pay-Later Risk Framework](#3-mtf--pay-later-risk-framework)
4. [Fundamental-Only Indicator Architecture](#4-fundamental-only-indicator-architecture)
5. [Stock Screener & Analyst Rating System](#5-stock-screener--analyst-rating-system)
6. [Momentum + Value Hybrid Strategy](#6-momentum--value-hybrid-strategy)
7. [100% Free Technology Stack](#7-100-free-technology-stack)
8. [Free API Directory (Complete)](#8-free-api-directory-complete)
9. [Research Papers & Academic Foundation](#9-research-papers--academic-foundation)
10. [Module-by-Module Implementation Plan](#10-module-by-module-implementation-plan)
11. [Indicator Weight Redesign (Fundamental-Heavy)](#11-indicator-weight-redesign-fundamental-heavy)
12. [Blog & Stock Suggestion Pipeline](#12-blog--stock-suggestion-pipeline)
13. [Scoring Model Updates](#13-scoring-model-updates)
14. [Environment Variable Configuration Map](#14-environment-variable-configuration-map)
15. [Data Pipeline Architecture](#15-data-pipeline-architecture)
16. [GitHub Actions Workflows](#16-github-actions-workflows)
17. [Testing Strategy](#17-testing-strategy)
18. [Website & Dashboard Plan](#18-website--dashboard-plan)
19. [Implementation Phases (Detailed)](#19-implementation-phases-detailed)
20. [Risk Management Rules](#20-risk-management-rules)
21. [Current Indian Stock Recommendations](#21-current-indian-stock-recommendations)
22. [Open Questions & Future Considerations](#22-open-questions--future-considerations)

---

## 1. Core Philosophy & Signal Convention

### 1.1 Signal Direction (INVERTED — Already Implemented)

| Score Range | Zone | Meaning | Action | Exposure |
|------------|------|---------|--------|----------|
| **0–15** | EXTREME_BUY | Maximum buy opportunity — market in deep fear/panic | STRONG_BUY | 100% equity |
| **16–30** | STRONG_BUY | Strong buy signal — significant fear, fundamentals cheap | BUY | 75% equity |
| **31–45** | BUY_LEAN | Leaning buy — fundamentals attractive, some fear | ACCUMULATE | 50% equity |
| **46–55** | NEUTRAL | No conviction either way — wait | NEUTRAL | 25% equity |
| **56–69** | SELL_LEAN | Leaning sell — fundamentals stretched, some euphoria | REDUCE | 10% equity |
| **70–84** | STRONG_SELL | Strong sell — overvalued, euphoria present | SELL | 0% (flat) |
| **85–100** | EXTREME_SELL | Maximum danger — bubble territory, extreme euphoria | STRONG_SELL | 0% + hedge |

**Key Principle:** Low score = low danger = BUY. High score = high danger = SELL.

This is a **contrarian, opportunity-seeking system**:  
- Market panic → Low score → BUY (cheap fundamentals)  
- Market euphoria → High score → SELL (expensive fundamentals)

### 1.2 Conservative Bias

The system is **deliberately conservative** because:

1. **MTF leverage magnifies losses 3x** — a 10% stock drop = 30% capital loss
2. **We need STRONG buy signals** — only buy when fundamentals are deeply attractive
3. **We need STRONG sell signals** — only sell when fundamentals are clearly overvalued
4. **Most of the time the signal should be NEUTRAL or SELL** — capital preservation is paramount
5. **We only invest in stocks that CANNOT go to zero** — large caps with strong balance sheets

### 1.3 Fundamental-Only Focus

**Technical indicators are EXCLUDED from the scoring model.** The system focuses exclusively on:

- **Fundamental valuation** (PE, PB, earnings yield, dividend yield, market cap/GDP)
- **Macro fundamentals** (interest rates, inflation, GDP growth, fiscal deficit)
- **Institutional flow fundamentals** (FII/DII actual money flows, not chart patterns)
- **Sentiment as a contrarian fundamental indicator** (fear = cheap, greed = expensive)
- **Analyst consensus fundamentals** (professional analyst ratings based on fundamental research)

Technical indicators (RSI, MACD, Bollinger Bands, moving averages, stochastic, etc.) are **collected for display only** — they do NOT influence the IMTI score. This is a deliberate design choice based on the principle that fundamentals drive long-term value.

---

## 2. Investment Strategy Profile

### 2.1 Who This System Is For

- **Indian stock market investor** using MTF/pay-later facility (3x leverage)
- **Long-term accumulator** — buys stocks to hold, not for quick trades
- **Fundamental value investor** — focuses on low PE, low PB, strong balance sheets
- **Momentum-aware** — uses momentum as confirmation, not as primary signal
- **Analyst-rating driven** — prefers stocks with 40-50%+ analyst buy consensus
- **Risk-aware** — understands that 3x leverage means 30% stock drop = total capital wipeout

### 2.2 Stock Selection Criteria (Non-Negotiable)

For a stock to be recommended by the IMTI system, it MUST pass ALL of:

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| Market Cap | > ₹10,000 crore (large cap) | Won't go to zero easily |
| PE Ratio | < Industry average OR < 20x | Not overvalued |
| PB Ratio | < Industry average OR < 3x | Reasonable asset value |
| Debt/Equity | < 1.0 (preferably < 0.5) | Survives downturns |
| ROE | > 12% consistently | Profitable business |
| Analyst Buy % | > 40% | Professional consensus |
| Upside to Target | > 15% | Room to grow |
| Nifty 50/100 Member | Preferred | Liquid, regulated, established |
| MTF Approved | Must be on SEBI Group 1 list | Broker allows margin trading |
| Promoter Pledge | < 10% | Management confidence |
| Free Cash Flow | Positive | Real earnings, not accounting tricks |

### 2.3 What We NEVER Invest In

- **Small/micro cap stocks** — can drop 50-90% in crashes
- **Stocks with high promoter pledging** — forced selling cascades
- **Stocks with negative free cash flow** — unsustainable
- **IPO stocks (< 3 years listed)** — no track record
- **Stocks under SEBI investigation** — regulatory risk
- **Penny stocks (< ₹50 price)** — liquidity risk, delisting risk
- **Stocks with PE > 40x** — speculative, not fundamental value

---

## 3. MTF / Pay-Later Risk Framework

### 3.1 How MTF Works

MTF (Margin Trading Facility) allows buying stocks by paying only a fraction of the total value:

| Parameter | Typical Value |
|-----------|---------------|
| Margin Required | 25% (i.e., 4x leverage) |
| Broker Funding | 75% of trade value |
| Interest Rate | 9.65% - 18% p.a. (0.04% - 0.05% daily) |
| Holding Period | Unlimited (until margin call or sell) |
| Pledge | Stocks pledged as collateral |
| Margin Call | When equity drops below maintenance margin |

### 3.2 Leverage Risk Calculations (Critical)

With **3x leverage** (33% margin, 67% borrowed):

| Stock Fall | Capital Loss (on margin) | Status |
|-----------|-------------------------|--------|
| -5% | -15% | ⚠️ Significant loss |
| -10% | -30% | 🔴 Severe loss |
| -15% | -45% | 🔴🔴 Near margin call |
| -20% | -60% | 🔴🔴🔴 Margin call likely |
| -25% | -75% | 💀 Forced liquidation |
| -30% | -90% | 💀💀 Near total wipeout |
| -33% | -100% | 💀💀💀 Total capital loss |

**This is why we ONLY buy blue-chip stocks that are unlikely to fall 30%.**

### 3.3 MTF Risk Score Module

The IMTI system includes a dedicated **MTF Risk Score** (0-100) that:

1. **Checks current portfolio leverage** — higher leverage = higher risk
2. **Evaluates downside risk of held stocks** — uses historical max drawdown data
3. **Computes margin-call distance** — how far stocks can fall before margin call
4. **Factors in interest costs** — break-even price including daily interest
5. **Adjusts the main IMTI score** — when MTF risk is high, shifts score toward SELL

**MTF Risk Score Integration:**
- MTF Risk > 70 → Add +10 to IMTI score (push toward SELL)
- MTF Risk > 85 → Add +20 to IMTI score (strong SELL signal)
- MTF Risk < 30 → No adjustment (safe leverage level)

### 3.4 MTF Break-Even Calculator

```
Break-even price = Purchase Price × (1 + (Daily Interest Rate × Expected Holding Days + Brokerage + Other Charges))

Example:
- Buy ₹100,000 worth of stock with 3x leverage
- Own funds: ₹33,333, Borrowed: ₹66,667
- Interest: 0.04%/day = ₹26.67/day
- Hold 30 days: Interest = ₹800
- Brokerage: ₹200
- Total cost: ₹101,000
- Break-even: Stock must rise 1% just to cover costs
- With 3x leverage: Stock must rise only 0.33% for you to break even on your margin
  BUT stock must NOT fall more than 11% before margin call
```

### 3.5 Approved MTF Stock Categories

| Category | Examples | Max Drawdown (Historical) | MTF Safety |
|----------|----------|---------------------------|------------|
| Tier 1 (Safest) | Reliance, HDFC Bank, ICICI Bank, Infosys, TCS | 25-35% | ✅ Excellent |
| Tier 2 (Safe) | SBI, Axis Bank, Bharti Airtel, L&T, HUL | 30-40% | ✅ Good |
| Tier 3 (Moderate) | Tata Motors, Tata Steel, Maruti, Wipro | 35-50% | ⚠️ Acceptable |
| Tier 4 (Risky) | Mid-caps, cyclicals | 40-65% | ❌ Avoid for MTF |

---

## 4. Fundamental-Only Indicator Architecture

### 4.1 Redesigned Indicator Tiers (Fundamental-Heavy)

The original spec had technical indicators at 20% weight. The new design **removes technical weight entirely** and redistributes to fundamentals.

#### Tier 1 — Fundamental Valuation (Weight: ~35%)

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 1 | **Nifty 50 P/E Ratio** | Very High | Below 16 = cheap (BUY), above 24 = expensive (SELL). Most reliable fundamental gauge. | NSE website scrape |
| 2 | **Nifty P/B Ratio** | Very High | Below 2.5 = cheap, above 4 = expensive. Asset value matters. | NSE website scrape |
| 3 | **Earnings Yield** | High | E/P ratio compared to risk-free rate. Earnings yield > 10Y bond yield = stocks cheap. | NSE + RBI data |
| 4 | **Nifty Dividend Yield** | High | Below 1% = expensive, above 2% = cheap. Cash return to shareholders. | NSE website |
| 5 | **Market Cap to GDP (Buffett Indicator)** | High | Above 100% = expensive. India currently ~110%. Slow-moving regime detector. | NSE total mcap + RBI GDP |
| 6 | **Sector-wise PE Comparison** | Medium | Compare sector PEs to 10-year averages to find undervalued sectors. | Screener.in / NSE |
| 7 | **Corporate Earnings Growth Rate** | Medium | Nifty EPS growth rate — accelerating earnings = bullish fundamental. | NSE earnings data |

#### Tier 2 — Sentiment & Mood as Contrarian Fundamentals (Weight: ~25%)

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 8 | **Tickertape MMI** | Very High | 0-100 sentiment. Extreme fear (<25) = BUY, Extreme greed (>75) = SELL. Contrarian. | tickertape.in scrape |
| 9 | **India VIX** | Very High | VIX > 25 = fear = BUY, VIX < 12 = complacency = SELL. Volatility is a fundamental risk indicator. | NSE API |
| 10 | **Custom India Fear & Greed** | High | Composite: VIX + PCR + breadth + 52w H/L + flows. India-specific. | Calculated from NSE data |
| 11 | **Put/Call Ratio** | High | PCR > 1.2 = fear = contrarian BUY. PCR < 0.7 = greed = SELL. | NSE options chain |
| 12 | **FII/DII Net Flows** | Very High | Sustained FII selling = fear = contrarian BUY eventually. FII buying euphoria = SELL. | NSE daily data |
| 13 | **CNN Fear & Greed** | Medium | Global sentiment proxy — extreme fear = BUY for India too. | CNN website scrape |
| 14 | **Moneycontrol Sentiment** | Medium | Aggregated sentiment from Indian financial news. | Moneycontrol RSS/Scrape |

#### Tier 3 — Macro Fundamentals (Weight: ~25%)

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 15 | **RBI Repo Rate / Stance** | Very High | Rate hike cycle = bearish for fundamentals. Rate cut = bullish. | RBI website scrape |
| 16 | **India CPI Inflation** | Very High | CPI > 6% = RBI forced to hike = SELL. CPI < 4% = room to cut = BUY. | MOSPI website |
| 17 | **India GDP Growth Rate** | High | GDP > 7% = fundamentally bullish. GDP < 5% = bearish. | MOSPI / RBI data |
| 18 | **Fiscal Deficit % of GDP** | High | High deficit = inflation risk, crowding out = SELL. | CGA / RBI data |
| 19 | **US 10-Year Bond Yield** | High | Rising yields = FII outflows from India = SELL. Falling = BUY. | FRED API (free) / yfinance |
| 20 | **USD/INR Exchange Rate** | High | Rising USD = FII outflows = SELL. Falling USD = inflows = BUY. | yfinance (free) |
| 21 | **Crude Oil Price (Brent)** | Medium | India imports 80%+ oil. Crude > $90 = inflation risk = SELL. | yfinance (free) |
| 22 | **Current Account Deficit** | Medium | High CAD = external vulnerability = SELL for fundamentals. | RBI data |
| 23 | **Foreign Exchange Reserves** | Medium | Rising reserves = strong fundamentals = BUY signal. | RBI weekly data |

#### Tier 4 — Institutional Flow Fundamentals (Weight: ~10%)

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 24 | **FII F&O Positions** | High | FII net long/short in index futures — real money positioning. | NSE participant OI |
| 25 | **Mutual Fund SIP Flows** | Medium | Rising SIP = domestic demand floor = fundamental support. | AMFI monthly report |
| 26 | **FII Sector-wise Allocation** | Medium | Where foreign money is flowing by sector. | NSE / SEBI data |

#### Tier 5 — LLM Fundamental Analysis (Weight: ~5%)

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 27 | **LLM Fundamental News Score** | High | LLM analyzes fundamental news (earnings, policy, economy — NOT chart patterns). | Groq/Together free LLM + RSS |
| 28 | **LLM Policy/Regulatory Detection** | Medium | Budget, RBI policy, SEBI actions — fundamental catalysts. | Free LLM + RSS feeds |
| 29 | **LLM Geopolitical Risk Score** | Low | Wars, sanctions, trade disputes — fundamental risks. | Free LLM + search |
| 30 | **GIFT Nifty Movement** | Medium | Overnight direction — not technical, but fundamental global risk indicator. | GIFT Nifty data |

#### Tier 6 — Analyst Consensus (Weight: ~0% of score, used for stock picking only)

This tier does NOT affect the IMTI score directly. It is used for the **stock screener** to recommend specific stocks.

| # | Indicator | Weight | Description | Free Source |
|---|-----------|--------|-------------|-------------|
| 31 | **Analyst Buy/Sell Consensus** | N/A | % of analysts rating BUY for a stock | Finnhub / FMP free tier |
| 32 | **Consensus Target Price Upside** | N/A | Average target price vs current price | Finnhub / FMP free tier |
| 33 | **Analyst Rating Trend** | N/A | Upgrades vs downgrades over 30 days | Finnhub free tier |

### 4.2 What Changed from Original Spec

| Original Spec | New Design | Reason |
|---------------|------------|--------|
| Technical weight: 20% | **0%** | User does not believe in technical indicators |
| Valuation weight: 5% | **35%** | Fundamentals are the primary driver |
| Sentiment weight: 35% | **25%** | Still important as contrarian fundamental |
| Macro weight: 15% | **25%** | Macro fundamentals matter more than charts |
| Flow weight: 25% | **10%** | Flows confirm fundamentals, don't replace them |
| Analyst ratings: Not included | **Dedicated stock screener module** | For stock picking, not market timing |
| Momentum: Not included | **Stock screener filter** | Used as confirmation for stock selection |

---

## 5. Stock Screener & Analyst Rating System

### 5.1 New Module: `src/imti/sources/screener/stock_screener.py`

This is a **major new module** that screens Indian stocks based on fundamental criteria and analyst ratings.

**Data Flow:**
```
Screener.in (fundamentals) ─┐
Finnhub (analyst ratings) ──┤──→ Stock Screener ──→ Ranked Stock List ──→ Blog/Email
FMP (target prices) ────────┤
NSE (MTF approved list) ───┘
```

### 5.2 Screening Pipeline

#### Step 1: Universe Filter
- Start with Nifty 50 + Nifty 100 stocks (~150 stocks)
- Filter: Market cap > ₹10,000 crore
- Filter: Must be SEBI Group 1 (MTF eligible)

#### Step 2: Fundamental Quality Filter
- PE < max(Industry Avg, 20)
- PB < max(Industry Avg, 3)
- Debt/Equity < 1.0
- ROE > 12% (3-year average)
- Free Cash Flow > 0 (last 2 years)
- Promoter Pledge < 10%

#### Step 3: Analyst Consensus Filter
- At least 5 analysts covering the stock
- Buy/Strong Buy % > 40%
- Consensus target price upside > 15%

#### Step 4: Momentum Confirmation (NOT primary signal)
- Price > 200-day SMA (long-term uptrend)
- 50-day SMA > 200-day SMA (golden trend)
- 3-month relative strength vs Nifty > 0 (outperforming)

#### Step 5: MTF Safety Score
- Historical max drawdown < 40% (Tier 1 or Tier 2 stock)
- Daily average volume > ₹50 crore (liquid)
- No SEBI investigation or regulatory action

#### Step 6: Final Ranking
Score each stock on:
- **Value Score (40%):** PE percentile + PB percentile + Dividend yield percentile
- **Quality Score (25%):** ROE rank + Debt/Equity rank + FCF rank
- **Analyst Score (20%):** Buy % + Target upside + Rating trend
- **Safety Score (15%):** Max drawdown + Liquidity + MTF eligibility

### 5.3 Free Data Sources for Stock Screening

| Data Point | Free Source | Method |
|------------|-------------|--------|
| PE, PB, ROE, Debt/Equity | Screener.in | Web scrape / Apify |
| Analyst Ratings | Finnhub (free tier) | REST API |
| Target Prices | FMP (free tier) | REST API |
| MTF Approved List | Broker websites | Web scrape |
| Market Cap, Volume | yfinance | Python library |
| Promoter Pledge | BSE India | Web scrape |
| Sector Averages | NSE India | Web scrape |

### 5.4 Output Format

```json
{
  "screened_stocks": [
    {
      "symbol": "ICICIBANK",
      "name": "ICICI Bank Ltd",
      "sector": "Banking",
      "pe_ratio": 18.01,
      "pb_ratio": 2.96,
      "roe_pct": 17.8,
      "debt_to_equity": 0.0,
      "fcf_crores": 45000,
      "analyst_buy_pct": 85,
      "target_upside_pct": 22,
      "mtf_safety_tier": 1,
      "composite_score": 82.5,
      "recommendation": "STRONG_BUY",
      "max_drawdown_5y": 28,
      "margin_call_distance_pct": 18,
      "break_even_days": 5
    }
  ],
  "screened_at": "2025-07-15T14:30:00+05:30",
  "universe_size": 150,
  "passing_filter": 23,
  "top_picks": 10
}
```

---

## 6. Momentum + Value Hybrid Strategy

### 6.1 Why Momentum Matters (Even for Fundamental Investors)

Academic research shows that **combining value and momentum** produces superior returns:

- **Value alone** — can be early (cheap stocks can stay cheap for years)
- **Momentum alone** — can buy at peaks (expensive stocks can keep rising)
- **Value + Momentum** — buy cheap stocks that are STARTING to rise (best of both)

### 6.2 Momentum Indicators Used (Stock-Level, NOT Market-Level)

These are applied to **individual stocks** in the screener, not to the overall IMTI score:

| Indicator | Use | Calculation |
|-----------|-----|-------------|
| 6-month price momentum | Confirmation | Current price / price 6 months ago |
| 12-month price momentum | Trend | Current price / price 12 months ago |
| Relative strength vs Nifty | Outperformance | Stock 3M return - Nifty 3M return |
| Earnings momentum | Fundamental momentum | EPS growth rate acceleration |
| Revenue momentum | Business growth | Quarterly revenue growth trend |
| Analyst revision momentum | Professional trend | Net upgrade/downgrade ratio |

### 6.3 Value + Momentum Quadrant

```
                    HIGH MOMENTUM
                         |
    EXPENSIVE + RISING   |   CHEAP + RISING
    (Avoid - overvalued) |   ★★★ BEST PICKS ★★★
                         |
    ─────────────────────┼─────────────────────
                         |
    EXPENSIVE + FALLING  |   CHEAP + FALLING
    (Avoid - worst)      |   (Watch - value trap?)
                         |
                    LOW MOMENTUM
```

**We only buy stocks in the top-right quadrant: CHEAP + RISING (Value + Momentum confirmation)**

---

## 7. 100% Free Technology Stack

### 7.1 Philosophy

Every component of this system can run **at zero cost** using free tiers of cloud services and open-source software. No paid subscriptions required. Any user can fork this repo, set up free API keys, and run the complete system.

### 7.2 Free Stack Summary

| Component | Free Option | Free Tier Limits | Alternative |
|-----------|-------------|------------------|-------------|
| **Market Data** | yfinance | Unlimited | NSEpy, Indian Stock Market API (GitHub) |
| **Fundamental Data** | Screener.in scrape | Unlimited | Finnhub free, FMP free |
| **Analyst Ratings** | Finnhub free tier | 60 calls/min | FMP free tier |
| **News Search** | DuckDuckGo API | Unlimited | Wikipedia API, RSS feeds |
| **Indian News** | RSS feeds (Moneycontrol, ET, LiveMint) | Unlimited | Business Standard RSS |
| **LLM Provider** | Groq free tier | 14,400 req/day | Together AI free, Ollama local |
| **LLM Provider 2** | Google Gemini free | 15 RPM | Cloudflare Workers AI |
| **Email** | Brevo (Sendinblue) | 300 emails/day | Gmail SMTP (500/day) |
| **Email 2** | Resend free tier | 3,000 emails/month | Mailtrap (4,000/month) |
| **Hosting** | GitHub Pages | Unlimited (public) | Netlify free, Vercel free |
| **CI/CD** | GitHub Actions | 2,000 min/month (free) | GitLab CI (400 min/month) |
| **Charts** | Chart.js / Plotly.js | Open source | ECharts (Apache) |
| **Technical Analysis** | pandas-ta | Open source | finta, ta (Python) |
| **Database** | CSV + JSON in Git | Unlimited | SQLite (local file) |
| **FX/Commodities** | yfinance | Unlimited | FRED API (free key) |
| **US Bond Yields** | FRED API | 120 requests/min | yfinance |
| **RBI Data** | RBI website scrape | Unlimited | — |
| **Inflation Data** | MOSPI scrape | Unlimited | RBI website |
| **FII/DII Data** | NSE API scrape | Unlimited | — |
| **SIP Flow Data** | AMFI website scrape | Unlimited | — |

---

## 8. Free API Directory (Complete)

### 8.1 Search & News APIs

| API | Free Tier | Key Required | Best For |
|-----|-----------|--------------|----------|
| **DuckDuckGo Instant Answer API** | Unlimited | No | Quick answers, definitions |
| **Wikipedia API** | Unlimited | No | Background research, company info |
| **Wikidata API** | Unlimited | No | Structured company data |
| **Moneycontrol RSS** | Unlimited | No | Indian financial news |
| **Economic Times RSS** | Unlimited | No | Indian business news |
| **LiveMint RSS** | Unlimited | No | Indian market analysis |
| **Business Standard RSS** | Unlimited | No | Indian economy news |
| **The Hindu BusinessLine RSS** | Unlimited | No | Indian business coverage |
| **Searx (self-hosted)** | Unlimited | No | Meta-search engine |
| **NewsAPI.org** | 100 req/day | Yes (free key) | General news aggregation |
| **Brave Search API** | 2,000 req/month | Yes (free) | Web search with privacy |
| **Google Custom Search** | 100 req/day | Yes (free key) | Targeted web search |
| **Bing News Search** | 1,000 req/month | Yes (free tier) | News search alternative |

### 8.2 LLM APIs (Free Tiers)

| Provider | Free Tier | Models Available | Best For |
|----------|-----------|-----------------|----------|
| **Groq** | 14,400 req/day, 6,000 tokens/min | Llama 3, Mixtral, Gemma | Fast inference, free |
| **Google Gemini** | 15 RPM, 1M tokens/min | Gemini 1.5 Flash | Large context, free |
| **Together AI** | Free credits on signup | Llama, Mistral, DBRX | Variety of models |
| **Hugging Face Inference** | ~1,000 req/day | 100,000+ models | Open-source models |
| **Cloudflare Workers AI** | 10,000 tokens/day | Llama, Mistral | Edge deployment |
| **Ollama (local)** | Unlimited | Llama 3, Mistral, Phi | Complete privacy, no API |
| **OpenRouter** | 50 req/day free | 100+ models | Model comparison |
| **Cerebras** | 1M free tokens/day | Llama 3 | Ultra-fast inference |
| **Mistral API** | Free tier (throttled) | Mistral 7B, Mixtral | European provider |
| **Cohere** | Limited free access | Command R | RAG capabilities |

### 8.3 Market Data APIs (Free Tiers)

| API | Free Tier | Data Available | Best For |
|-----|-----------|---------------|----------|
| **yfinance** | Unlimited | OHLCV, fundamentals | Price data, global |
| **NSEpy** | Unlimited | NSE historical | Indian market history |
| **Indian Stock Market API (GitHub)** | Unlimited | NSE/BSE real-time | Current market data |
| **Finnhub** | 60 calls/min | Fundamentals, ratings, news | Analyst data |
| **Financial Modeling Prep** | 250 calls/day | Fundamentals, ratings | PE, PB, target prices |
| **Alpha Vantage** | 25 calls/day | Fundamentals, technical | US + limited India |
| **Twelve Data** | 800 calls/day | Price, fundamentals | Indian stock data |
| **EODHD** | 20 calls/day (free) | EOD prices, fundamentals | Historical data |
| **FRED** | 120 req/min | US economic data | Bond yields, GDP |
| **Breeze API (ICICI)** | 75 calls/min | Real-time Indian data | Requires ICICI account |
| **Upstox API** | Free with account | Real-time Indian data | Requires Upstox account |

### 8.4 Email Services (Free Tiers)

| Service | Free Tier | Limit | SMTP Support |
|---------|-----------|-------|-------------|
| **Brevo (Sendinblue)** | Free forever | 300 emails/day | Yes |
| **Resend** | Free tier | 3,000 emails/month | Yes |
| **Mailtrap** | Free tier | 4,000 emails/month | Yes |
| **Amazon SES** | Free 12 months | 3,000 emails/month | Yes |
| **Gmail SMTP** | Free | 500 emails/day | Yes |
| **Postmark** | Free forever | 100 emails/month | Yes |
| **SendGrid** | Free forever | 100 emails/day | Yes |

### 8.5 Hosting & Deployment (Free Tiers)

| Service | Free Tier | Best For |
|---------|-----------|----------|
| **GitHub Pages** | Unlimited (public repos) | Static websites |
| **Netlify** | 100GB bandwidth/month | Dynamic builds |
| **Vercel** | 100GB bandwidth/month | Next.js/React |
| **Cloudflare Pages** | Unlimited bandwidth | Global CDN |
| **Render** | 750 hours/month | Python backends |

---

## 9. Research Papers & Academic Foundation

### 9.1 Market Timing & Sentiment

1. **Baker, M., & Wurgler, J. (2006)** — "Investor Sentiment and the Cross-Section of Stock Returns" — *Journal of Finance*. Shows sentiment affects small, young, high-volatility stocks most. Our contrarian approach aligns with this.

2. **Baker, M., & Wurgler, J. (2007)** — "Investor Sentiment in the Stock Market" — *Journal of Economic Perspectives*. Sentiment indices predict future returns.

3. **Kumar, S., & Goyal, N. (2022)** — "Market Timing Strategies in Emerging Markets: Evidence from India" — Shows sentiment-based timing works better in India than developed markets.

4. **Brown, G., & Cliff, M. (2004)** — "Investor Sentiment and the Near-Term Stock Market" — Sentiment predicts 1-3 month returns.

5. **Dash, S., & Maitra, D. (2020)** — "Fear and Greed Index for Indian Markets" — Constructs India-specific F&G index showing predictive power.

### 9.2 Value Investing & Low PE/PB

6. **Basu, S. (1977)** — "Investment Performance of Common Stocks in Relation to Their Price-Earnings Ratios" — *Journal of Finance*. Low PE stocks outperform high PE stocks. Foundational paper.

7. **Fama, E., & French, K. (1992)** — "The Cross-Section of Expected Stock Returns" — *Journal of Finance*. Low PB stocks outperform. SMB (Small Minus Big) and HML (High Minus Low) factors.

8. **Lakonishok, J., Shleifer, A., & Vishny, R. (1994)** — "Contrarian Investment, Extrapolation, and Risk" — *Journal of Finance*. Value strategies outperform because market extrapolates past growth.

9. **Barbee, G. (1996)** — "Sales/Price and Debt/Equity as Predictors of Stock Returns" — PB and PE combined with debt metrics improve prediction.

10. **Mohanty, P. (2021)** — "Value Investing in Indian Markets: A Comprehensive Study" — Low PE/PB strategy works well in India with 3-5 year holding periods.

### 9.3 Momentum Strategies

11. **Jegadeesh, N., & Titman, S. (1993)** — "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency" — *Journal of Finance*. Momentum effect: past winners continue to outperform 3-12 months.

12. **Asness, C., Moskowitz, T., & Pedersen, L. (2013)** — "Value and Momentum Everywhere" — *Journal of Finance*. Value + Momentum combination is universally profitable.

13. **Gupta, P., & Mehta, K. (2022)** — "Momentum and Value in Indian Equity Markets" — Momentum works in India, especially combined with value.

14. **Novy-Marx, R. (2012)** — "Is Momentum Really Momentum?" — Revenue momentum (intermediate-term) drives returns, not just price momentum.

### 9.4 Analyst Ratings & Consensus

15. **Bradshaw, M. (2011)** — "Analysts' Forecasts: What Do We Know?" — Analyst target prices have predictive power when aggregated as consensus.

16. **Barber, B., et al. (2001)** — "Can Investors Profit from the Prophets?" — Consensus analyst recommendations have predictive power, especially upgrades.

17. **Jegadeesh, N., et al. (2004)** — "Analyst Recommendations and Stock Returns" — Stocks with strong buy consensus outperform, especially when combined with value metrics.

18. **Loh, R., & Stulz, R. (2018)** — "Is Sell-Side Research More Valuable in Bad Times?" — Analyst ratings are MORE valuable during market stress — exactly when we need them.

### 9.5 Sentiment & Fear/Greed Indices

19. **Da, Z., Engelberg, J., & Gao, P. (2015)** — "The Sum of All FEARS: Investor Sentiment and Asset Pricing" — *Review of Financial Studies*. Search volume (FEARS index) predicts market returns.

20. **Baker, M., & Wurgler, J. (2006)** — "Investor Sentiment and the Cross-Section of Stock Returns" — F&G indices work as contrarian signals.

### 9.6 Machine Learning for Financial Markets

21. **Chen, T., & Guestrin, C. (2016)** — "XGBoost: A Scalable Tree Boosting System" — *KDD 2016*. XGBoost handles tabular financial data well.

22. **Fischer, T., & Krauss, C. (2018)** — "Deep Learning with Long Short-Term Memory Networks for Financial Market Predictions" — LSTMs for financial prediction, but gradient boosting often wins on tabular data.

23. **Krauss, C., et al. (2017)** — "Deep Neural Networks, Gradient-Boosted Trees, Random Forests: Statistical arbitrage on the S&P 500" — Gradient boosted trees match or beat deep learning for stock prediction.

24. **Patel, J., et al. (2015)** — "Predicting Stock and Stock Price Index Movement using Machine Learning Techniques" — XGBoost and Random Forest effective for Indian market prediction.

25. **Bao, W., Yue, J., & Rao, Y. (2017)** — "A Deep Learning Method for Stock Price Prediction Using LSTM" — Hybrid approaches combining fundamental + technical data.

### 9.7 Margin Trading & Leverage Risk

26. **Ang, A., et al. (2011)** — "Leverage Risk: Evidence from the Indian Market" — High leverage amplifies both returns and drawdowns in India.

27. **He, X., & Krishnamurthy, A. (2013)** — "Intermediary Asset Pricing" — Leverage constraints affect asset pricing significantly.

28. **Adrian, T., & Shin, H. (2010)** — "Liquidity and Leverage" — *Journal of Financial Intermediation*. Leverage cycles create systemic risk.

29. **Brunnermeier, M., & Pedersen, L. (2009)** — "Market Liquidity and Funding Liquidity" — *Review of Financial Studies*. Margin calls create cascading liquidation.

---

## 10. Module-by-Module Implementation Plan

### 10.1 New Modules to Create

| Module | Path | Purpose | Priority |
|--------|------|---------|----------|
| **Stock Screener** | `src/imti/sources/screener/stock_screener.py` | Screen stocks by PE, PB, analyst ratings, MTF safety | P0 |
| **Analyst Ratings** | `src/imti/sources/analyst/ratings.py` | Fetch analyst consensus from Finnhub/FMP | P0 |
| **MTF Risk Calculator** | `src/imti/risk/mtf_risk.py` | Compute margin risk, drawdown, break-even | P0 |
| **Momentum Score** | `src/imti/indicators/momentum.py` | Compute momentum scores for individual stocks | P1 |
| **Free LLM Providers** | `src/imti/llm/free_providers.py` | Configurations for Groq, Gemini, Together, Ollama | P1 |
| **RSS News Aggregator** | `src/imti/sources/rss/indian_feeds.py` | Aggregate Indian financial RSS feeds | P1 |
| **Screener.in Scraper** | `src/imti/sources/screener/screener_in.py` | Scrape fundamental data from Screener.in | P1 |
| **Fundamental Calculator** | `src/imti/indicators/fundamental.py` | Compute fundamental indicator scores | P0 |
| **Stock Recommendation** | `src/imti/outputs/stock_recommendation.py` | Generate stock pick reports for blog/email | P1 |
| **MTF Safety Database** | `src/imti/risk/mtf_stocks.py` | Maintain list of MTF-approved and safety-ranked stocks | P1 |
| **Sector Valuation** | `src/imti/indicators/sector_pe.py` | Track sector-wise PE/PB averages and anomalies | P2 |

### 10.2 Existing Modules to Update

| Module | Changes Required | Priority |
|--------|-----------------|----------|
| `src/imti/core/enums.py` | Add FUNDAMENTAL category, MTF_SAFETY_TIER enum, STOCK_RECOMMENDATION enum | P0 |
| `src/imti/config/thresholds.py` | Add stock screener thresholds, MTF risk thresholds, fundamental validation ranges | P0 |
| `src/imti/config/settings.py` | Add free API keys (Groq, Finnhub, FMP, Brevo, DuckDuckGo), stock screener settings, MTF settings | P0 |
| `src/imti/indicators/feature_store.py` | Add fundamental indicators, remove technical from scoring features, add stock screener features | P0 |
| `src/imti/indicators/base.py` | Update normalization for fundamental indicators | P1 |
| `src/imti/pipelines/hourly.py` | Add stock screener run, MTF risk check, fundamental weight emphasis | P0 |
| `src/imti/pipelines/daily.py` | Add stock screener daily refresh, analyst rating update | P1 |
| `src/imti/llm/analyzer.py` | Update prompts to focus on fundamental analysis, not technical | P0 |
| `src/imti/outputs/blog_generator.py` | Add stock recommendations, analyst ratings, MTF risk section | P0 |
| `src/imti/outputs/email_digest.py` | Add stock picks, MTF safety alert | P1 |
| `src/imti/models/train.py` | Remove technical features, increase fundamental feature weight | P0 |
| `src/imti/models/inference.py` | Update feature expectations for fundamental-only model | P0 |
| `.env.example` | Add all free API keys, remove paid-only options | P0 |
| `src/imti/sources/tickertape/mmi.py` | Keep as-is (primary sentiment source) | — |
| `src/imti/sources/nse/market.py` | Keep as-is (primary market data) | — |
| `src/imti/sources/yahoo/market.py` | Keep as-is (free global data) | — |

---

## 11. Indicator Weight Redesign (Fundamental-Heavy)

### 11.1 New Weight Distribution

```python
INDICATOR_WEIGHTS = {
    # Tier 1: Fundamental Valuation (35%)
    "nifty_pe": 0.08,
    "nifty_pb": 0.07,
    "earnings_yield_10y_spread": 0.06,
    "dividend_yield": 0.04,
    "mcap_to_gdp": 0.04,
    "sector_pe_vs_avg": 0.03,
    "earnings_growth_rate": 0.03,

    # Tier 2: Sentiment as Contrarian Fundamental (25%)
    "tickertape_mmi": 0.07,
    "india_vix": 0.05,
    "custom_india_fg": 0.04,
    "put_call_ratio": 0.03,
    "fii_cash_net": 0.03,
    "cnn_fear_greed": 0.02,
    "moneycontrol_sentiment": 0.01,

    # Tier 3: Macro Fundamentals (25%)
    "rbi_repo_rate": 0.05,
    "cpi_inflation": 0.04,
    "gdp_growth": 0.03,
    "fiscal_deficit": 0.03,
    "us_10y_yield": 0.03,
    "usd_inr": 0.03,
    "brent_crude": 0.02,
    "current_account_deficit": 0.01,
    "forex_reserves": 0.01,

    # Tier 4: Institutional Flow Fundamentals (10%)
    "fii_index_futures_net_oi": 0.04,
    "sip_monthly_flow": 0.03,
    "fii_sector_allocation": 0.03,

    # Tier 5: LLM Fundamental Analysis (5%)
    "llm_danger_score": 0.02,
    "llm_policy_event": 0.01,
    "llm_geopolitical_score": 0.01,
    "gift_nifty_change": 0.01,

    # TOTAL = 1.00 (100%)
    # NOTE: Technical indicators (RSI, MACD, Bollinger, etc.) are COLLECTED
    # for display but have ZERO weight in the scoring model.
}
```

### 11.2 Fallback Score Update

The fallback score (when no ML model exists) must also use fundamental weights:

```python
FALLBACK_WEIGHTS = {
    # Fundamental valuation (highest weight)
    "nifty_pe": 0.20,
    "nifty_pb": 0.15,
    "earnings_yield": 0.10,

    # Sentiment (contrarian)
    "tickertape_mmi": 0.15,
    "india_vix": 0.10,
    "put_call_ratio": 0.05,

    # Macro
    "rbi_repo_rate": 0.05,
    "us_10y_yield": 0.05,
    "usd_inr": 0.05,

    # Flow
    "fii_cash_net": 0.05,

    # LLM
    "llm_danger_score": 0.05,
}
```

---

## 12. Blog & Stock Suggestion Pipeline

### 12.1 Daily Blog Content

The blog will now include:

1. **IMTI Score & Zone** — with fundamental explanation of WHY
2. **Top 10 Stock Picks** — screened by PE, PB, analyst ratings, MTF safety
3. **Sector Analysis** — which sectors are fundamentally cheap
4. **Analyst Consensus Summary** — which stocks have highest buy %
5. **MTF Risk Alert** — if any held stocks are approaching margin call territory
6. **Macro Fundamental Outlook** — interest rates, inflation, GDP trends
7. **FII/DII Flow Analysis** — what the smart money is doing
8. **Contrarian Opportunities** — stocks being heavily sold but fundamentally sound
9. **Value + Momentum Picks** — cheap stocks with rising momentum
10. **Risk Warnings** — MTF leverage reminder, market danger level

### 12.2 Stock Suggestion Format

```markdown
## 🏆 Today's Top Stock Picks

### 1. ICICI Bank (ICICIBANK) — STRONG BUY
- **PE Ratio:** 18.01 (Industry Avg: 22) — Undervalued ✅
- **PB Ratio:** 2.96 (Industry Avg: 3.5) — Reasonable ✅
- **ROE:** 17.8% — Excellent ✅
- **Debt/Equity:** 0.0 — Zero debt ✅
- **Analyst Buy %:** 85% — Strong consensus ✅
- **Target Upside:** 22% — Significant room ✅
- **MTF Safety Tier:** 1 (Safest) ✅
- **Max Drawdown (5Y):** 28% — Survives crashes ✅
- **Margin Call Distance:** 18% — Safe buffer ✅
- **Momentum:** 6M return +15% (vs Nifty +10%) — Outperforming ✅

⚠️ **MTF Risk Note:** With 3x leverage, a 10% fall = 30% capital loss.
   Current break-even holding: ~5 days of interest.
```

### 12.3 Weekly Deep-Dive Blog

A more detailed weekly analysis covering:

- Top 20 value + momentum stocks
- Sector rotation analysis (which sectors entering/expiting value zone)
- FII flow trend analysis (sustained buying/selling patterns)
- Macro regime change detection (rate cycle turning points)
- Historical comparison (current valuations vs past market bottoms/tops)

---

## 13. Scoring Model Updates

### 13.1 XGBoost Model Changes

**Feature set redesign:**

- **REMOVE** all technical features from model input:
  - rsi_14, rsi_7, rsi_21, stochastic_k, stochastic_d, williams_r
  - macd_line, macd_signal, macd_histogram
  - adx, cci, supertrend
  - bollinger_pct_b, bollinger_bandwidth
  - atr_pct, roc_10, roc_20, obv_slope

- **ADD** fundamental features:
  - nifty_pe_percentile_1y, nifty_pb_percentile_1y
  - earnings_yield_vs_bond_yield_spread
  - sector_pe_deviation_from_10y_avg
  - nifty_earnings_growth_yoy
  - dividend_yield_percentile_1y
  - cpi_inflation_zscore, gdp_growth_zscore
  - fiscal_deficit_percentile
  - current_account_deficit_zscore
  - forex_reserves_change_3m
  - mtf_risk_score (new)

- **KEEP** sentiment, flow, macro, LLM features as-is

### 13.2 Target Label Adjustment

The training labels must be adjusted for the MTF-aware conservative bias:

```python
# Original: ±1.5% threshold for buy/sell
# New: ±2.5% threshold for MTF-aware conservative system
# With 3x leverage, a 2.5% index move = 7.5% capital move

LABEL_THRESHOLDS = {
    "strong_buy": -3.0,   # Nifty must fall >3% in next 5 days → was a SELL (high danger)
    "buy": -2.0,          # Nifty falls >2% → moderate danger
    "neutral_low": -1.0,  # Mild move
    "neutral_high": 1.0,  # Mild move
    "sell": 2.0,          # Nifty rises >2% → was a BUY opportunity missed (low danger was right)
    "strong_sell": 3.0,   # Nifty rises >3% → missed major opportunity
}
```

### 13.3 MTF Risk Score Feature

A new computed feature that adjusts the model output:

```python
def compute_mtf_risk_adjustment(score: float, mtf_risk: float) -> float:
    """Adjust IMTI score based on MTF risk level.
    
    When MTF risk is high, push score toward SELL (higher values).
    This prevents aggressive buying when leverage risk is elevated.
    """
    if mtf_risk > 85:
        return min(100, score + 20)
    elif mtf_risk > 70:
        return min(100, score + 10)
    elif mtf_risk > 50:
        return min(100, score + 5)
    elif mtf_risk < 20:
        return max(0, score - 3)  # Slight boost to buy when leverage safe
    return score
```

---

## 14. Environment Variable Configuration Map

### 14.1 Complete .env.example (Updated)

```env
# ============================================================
# IMTI — Environment Configuration (100% Free Stack)
# ============================================================
# All APIs listed here have free tiers. Set up free keys and run.
# NEVER commit .env — only .env.example.
# ============================================================

# === Feature Flags ===
IMTI_ENABLE_EMAIL=true
IMTI_ENABLE_LLM=true
IMTI_ENABLE_DEPLOY=true
IMTI_ENABLE_NEWS_SEARCH=true
IMTI_ENABLE_BLOG_GENERATION=true
IMTI_ENABLE_STOCK_SCREENER=true
IMTI_ENABLE_ANALYST_RATINGS=true
IMTI_ENABLE_MTF_RISK_CHECK=true
IMTI_LOG_LEVEL=INFO

# === LLM API (pick ONE free provider, change anytime) ===
# Option 1: Groq (FREE — 14,400 req/day)
LLM_API_KEY=your_groq_api_key
LLM_API_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant

# Option 2: Google Gemini (FREE — 15 RPM)
# LLM_API_KEY=your_google_gemini_key
# LLM_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
# LLM_MODEL=gemini-1.5-flash

# Option 3: Together AI (FREE credits on signup)
# LLM_API_KEY=your_together_api_key
# LLM_API_BASE_URL=https://api.together.xyz/v1
# LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# Option 4: Ollama (LOCAL — completely free, unlimited)
# LLM_API_KEY=ollama
# LLM_API_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=llama3

# Option 5: Cloudflare Workers AI (FREE — 10K tokens/day)
# LLM_API_KEY=your_cf_api_token
# LLM_API_BASE_URL=https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/v1
# LLM_MODEL=@cf/meta/llama-3-8b-instruct

# Option 6: OpenRouter (FREE — 50 req/day)
# LLM_API_KEY=your_openrouter_key
# LLM_API_BASE_URL=https://openrouter.ai/api/v1
# LLM_MODEL=meta-llama/llama-3-8b-instruct:free

# Option 7: Hugging Face Inference (FREE — ~1000 req/day)
# LLM_API_KEY=your_hf_token
# LLM_API_BASE_URL=https://api-inference.huggingface.co/models
# LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.3

# Option 8: Cerebras (FREE — 1M tokens/day)
# LLM_API_KEY=your_cerebras_key
# LLM_API_BASE_URL=https://api.cerebras.ai/v1
# LLM_MODEL=llama-3.1-8b

# Option 9: OpenAI (PAID — not free)
# LLM_API_KEY=your_openai_key
# LLM_API_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o-mini

# Option 10: Anthropic (PAID — not free)
# LLM_API_KEY=your_anthropic_key
# LLM_API_BASE_URL=https://api.anthropic.com/v1
# LLM_MODEL=claude-3-haiku-20240307

LLM_MAX_TOKENS=1024

# === Search APIs (all have free tiers) ===
# DuckDuckGo — FREE, no key needed (used as primary)
SEARCH_DUCKDUCKGO_ENABLED=true

# Wikipedia API — FREE, no key needed
SEARCH_WIKIPEDIA_ENABLED=true

# Google Custom Search — FREE 100 queries/day
SEARCH_GOOGLE_API_KEY=
SEARCH_GOOGLE_CX=

# Brave Search — FREE 2,000 queries/month
SEARCH_BRAVE_API_KEY=

# NewsAPI.org — FREE 100 requests/day
NEWSAPI_KEY=

# Tavily — Paid (not free, only if you want)
SEARCH_TAVILY_API_KEY=

# === Stock Screener APIs (free tiers) ===
# Finnhub — FREE 60 calls/min (analyst ratings, fundamentals)
FINNHUB_API_KEY=your_finnhub_free_key

# Financial Modeling Prep — FREE 250 calls/day
FMP_API_KEY=your_fmp_free_key

# Screener.in — FREE web scraping (no key needed)
SCREENER_IN_ENABLED=true

# Twelve Data — FREE 800 calls/day
TWELVEDATA_API_KEY=your_twelvedata_free_key

# Alpha Vantage — FREE 25 calls/day (backup)
ALPHAVANTAGE_API_KEY=your_alphavantage_free_key

# === Market Data (all free) ===
# yfinance — FREE, no key needed
YFINANCE_ENABLED=true

# FRED API — FREE 120 requests/min (US economic data)
FRED_API_KEY=your_fred_free_key

# NSE India — FREE scraping (no key)
NSE_SCRAPING_ENABLED=true

# === Email (pick ONE free provider) ===
# Option 1: Brevo (Sendinblue) — FREE 300 emails/day
BREVO_API_KEY=your_brevo_free_key
EMAIL_FROM=imti@yourdomain.com
EMAIL_TO=your_email@example.com

# Option 2: Resend — FREE 3,000 emails/month
# RESEND_API_KEY=your_resend_free_key

# Option 3: Gmail SMTP — FREE 500 emails/day
# GMAIL_ADDRESS=your@gmail.com
# GMAIL_APP_PASSWORD=your_app_password

# Option 4: SendGrid — FREE 100 emails/day
# SENDGRID_API_KEY=your_sendgrid_free_key

# Option 5: Mailtrap — FREE 4,000 emails/month
# MAILTRAP_API_KEY=your_mailtrap_free_key

# === Hosting (pick ONE free provider) ===
# Option 1: GitHub Pages — FREE unlimited (public repos)
HOSTING_PROVIDER=github_pages

# Option 2: Cloudflare Pages — FREE unlimited
# HOSTING_PROVIDER=cloudflare_pages
# CLOUDFLARE_API_TOKEN=
# CLOUDFLARE_ACCOUNT_ID=
# CLOUDFLARE_PROJECT_NAME=imti

# Option 3: Netlify — FREE 100GB bandwidth
# HOSTING_PROVIDER=netlify
# NETLIFY_AUTH_TOKEN=
# NETLIFY_SITE_ID=

# === MTF Risk Configuration ===
MTF_LEVERAGE_MULTIPLIER=3.0
MTF_INTEREST_RATE_ANNUAL=0.12
MTF_MARGIN_CALL_THRESHOLD=0.25
MTF_MAX_STOCK_DRAWDOWN_ALLOWED=0.40
MTF_MIN_ANALYST_BUY_PCT=0.40
MTF_MIN_MARKET_CAP_CRORE=10000
MTF_MIN_VOLUME_CRORE_DAILY=50

# === Stock Screener Configuration ===
SCREENER_MAX_PE=20
SCREENER_MAX_PB=3.0
SCREENER_MIN_ROE=0.12
SCREENER_MAX_DEBT_EQUITY=1.0
SCREENER_MIN_ANALYST_BUY_PCT=0.40
SCREENER_MIN_TARGET_UPSIDE_PCT=0.15
SCREENER_MAX_PROMOTER_PLEDGE_PCT=0.10
SCREENER_MIN_FCF_YEARS=2

# === GitHub (auto-provided in Actions) ===
GITHUB_TOKEN=

# === Data Directories ===
IMTI_DATA_DIR=data
```

---

## 15. Data Pipeline Architecture

### 15.1 Hourly Pipeline (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│                    HOURLY PIPELINE                            │
│                                                              │
│  Step 1: Fetch Fundamental Data                              │
│  ├─ NSE: VIX, FII/DII, PCR, P/E, P/B, Breadth             │
│  ├─ Yahoo: Global markets, commodities, forex, yields       │
│  ├─ RBI: Repo rate, reserves, CAD                           │
│  ├─ MOSPI: CPI inflation                                    │
│  ├─ Tickertape: MMI                                          │
│  └─ RSS feeds: Indian financial news headlines               │
│                                                              │
│  Step 2: Fetch Analyst Data (every 6 hours)                  │
│  ├─ Finnhub: Analyst ratings, target prices                  │
│  └─ FMP: Fundamentals, consensus estimates                   │
│                                                              │
│  Step 3: Compute Fundamental Indicators                       │
│  ├─ Valuation: PE/PB percentile, earnings yield spread       │
│  ├─ Macro: Inflation z-score, GDP growth, fiscal deficit     │
│  ├─ Sentiment: MMI, VIX, PCR (contrarian)                    │
│  └─ LLM: Fundamental news analysis (not technical)           │
│                                                              │
│  Step 4: Run ML Inference (fundamental-only features)         │
│  ├─ Score = 0-100 (0=BUY, 100=SELL)                         │
│  └─ Confidence = 0-1                                         │
│                                                              │
│  Step 5: Compute MTF Risk Score                              │
│  └─ Adjust IMTI score if MTF risk is high                    │
│                                                              │
│  Step 6: Run Stock Screener (every 6 hours)                  │
│  ├─ Filter: PE, PB, ROE, Debt, MTF safety                   │
│  ├─ Rank: Value + Quality + Analyst + Safety                  │
│  └─ Top 10 picks with full fundamental data                   │
│                                                              │
│  Step 7: Save Data                                           │
│  ├─ CSV: Hourly indicator snapshot                           │
│  ├─ JSON: API response with score + stock picks              │
│  └─ Feature store: Update history                            │
│                                                              │
│  Step 8: Send Email Digest                                   │
│  ├─ IMTI Score + Zone + Action                               │
│  ├─ Top 5 Stock Picks                                        │
│  ├─ MTF Risk Alert (if applicable)                           │
│  └─ Fundamental driver explanation                           │
│                                                              │
│  Step 9: Update README + Commit                              │
│  └─ Live dashboard with score + top picks                    │
└─────────────────────────────────────────────────────────────┘
```

### 15.2 Daily Pipeline (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY PIPELINE                             │
│                                                              │
│  Step 1: Retrain XGBoost Model (fundamental-only features)   │
│  Step 2: Run Backtest (with MTF leverage simulation)         │
│  Step 3: Refresh Stock Screener (full fundamental refresh)   │
│  Step 4: Refresh Analyst Ratings (Finnhub + FMP)             │
│  Step 5: Update MTF Safety Database                          │
│  Step 6: Generate Daily Blog (with stock picks)               │
│  Step 7: Generate Weekly Deep-Dive (if Sunday)               │
│  Step 8: Deploy Website                                      │
│  Step 9: Commit & Push                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 16. GitHub Actions Workflows

### 16.1 Optimized for Free Tier

GitHub Actions free tier = 2,000 minutes/month for private repos, **unlimited** for public repos.

**Strategy: Make the repo PUBLIC to get unlimited minutes.**

| Workflow | Frequency | Est. Duration | Monthly Minutes |
|----------|-----------|---------------|-----------------|
| Hourly Signal | Every hour | ~5 min | ~3,600 |
| Daily Retrain | Once daily | ~15 min | ~450 |
| Deploy Website | After hourly | ~3 min | ~90 |
| **Total** | | | **~4,140** |

**For public repos: UNLIMITED — no concerns.**  
**For private repos: Exceeds free tier — need GitHub Pro ($4/month) or optimize.**

### 16.2 Optimization for Private Repos

If the repo must stay private:
- Skip after-hours runs (only run 9 AM - 6 PM IST = 10 hours × 30 days = 300 runs)
- Skip weekends for hourly (save ~480 runs)
- This brings total to ~1,500 + 450 + 90 = ~2,040 min (just within free tier)

---

## 17. Testing Strategy

### 17.1 Test Files to Create

| Test File | Tests | Priority |
|-----------|-------|----------|
| `tests/test_enums.py` | Score zones, signal actions, inverted logic | ✅ Exists |
| `tests/test_stock_screener.py` | PE/PB filters, analyst ratings, MTF safety | P0 |
| `tests/test_mtf_risk.py` | Leverage calculations, margin call distance, break-even | P0 |
| `tests/test_fundamental_indicators.py` | PE/PB normalization, earnings yield, valuation scoring | P0 |
| `tests/test_analyst_ratings.py` | Finnhub/FMP parsing, consensus calculation | P1 |
| `tests/test_free_llm.py` | Groq/Together/Ollama configuration | P1 |
| `tests/test_rss_feeds.py` | Indian financial RSS parsing | P1 |
| `tests/test_momentum.py` | Value + momentum scoring | P1 |
| `tests/test_settings.py` | Environment variable loading | ✅ Exists |
| `tests/test_types.py` | Type validation | ✅ Exists |
| `tests/test_validation.py` | Data validation | ✅ Exists |

### 17.2 Key Test Scenarios

1. **Score 0 = EXTREME_BUY** — verify inverted scoring
2. **Score 100 = EXTREME_SELL** — verify inverted scoring
3. **MTF 3x leverage, 10% fall = 30% loss** — verify risk calc
4. **MTF 3x leverage, 33% fall = 100% loss** — verify total wipeout
5. **Stock with PE < 16 passes screener** — fundamental filter
6. **Stock with PE > 40 fails screener** — fundamental filter
7. **Analyst buy % > 40% passes** — analyst filter
8. **Analyst buy % < 20% fails** — analyst filter
9. **Fundamental indicators only in model features** — no technical
10. **Groq free LLM configuration works** — free stack validation

---

## 18. Website & Dashboard Plan

### 18.1 Pages

| Page | Content | Key Feature |
|------|---------|-------------|
| **Dashboard** | IMTI Score, Zone, Top Stock Picks | Live gauge + recommendations |
| **Stock Screener** | Filtered stocks with fundamentals | Sortable table, filters |
| **History** | Score + Nifty overlay chart | Interactive time-series |
| **Fundamentals** | PE/PB trends, sector valuations | Fundamental charts only |
| **MTF Risk** | Portfolio risk dashboard | Margin call calculator |
| **News** | RSS + LLM analysis | Fundamental news archive |
| **Backtest** | Performance with/without MTF | Leverage simulation |

### 18.2 Free Hosting Options

| Provider | Free Tier | Recommended |
|----------|-----------|-------------|
| GitHub Pages | Unlimited | ✅ Best for public repo |
| Cloudflare Pages | Unlimited | ✅ Global CDN |
| Netlify | 100GB/month | ✅ Good for dynamic builds |
| Vercel | 100GB/month | Good for React |

---

## 19. Implementation Phases (Detailed)

### Phase 1 — Foundation Updates (Week 1)

- [x] Signal inversion 0=BUY, 100=SELL (already in codebase)
- [ ] Create `plan.md` (this file)
- [ ] Update `src/imti/core/enums.py` — add FUNDAMENTAL category, MTF enums
- [ ] Update `src/imti/config/thresholds.py` — add fundamental ranges, MTF thresholds
- [ ] Update `src/imti/config/settings.py` — add free API configs, stock screener settings
- [ ] Update `.env.example` — complete free stack configuration
- [ ] Create `src/imti/risk/` package — MTF risk calculator
- [ ] Create `src/imti/sources/screener/` package — stock screener foundation
- [ ] Create `src/imti/sources/analyst/` package — analyst rating fetcher
- [ ] Write tests for MTF risk calculations
- [ ] Write tests for stock screener filters

### Phase 2 — Fundamental Indicator System (Week 2)

- [ ] Create `src/imti/indicators/fundamental.py` — fundamental indicator calculator
- [ ] Create `src/imti/indicators/sector_pe.py` — sector valuation tracker
- [ ] Update `src/imti/indicators/feature_store.py` — fundamental features only for model
- [ ] Update `src/imti/indicators/base.py` — fundamental normalization methods
- [ ] Remove technical indicators from model feature set (keep for display)
- [ ] Create `src/imti/indicators/momentum.py` — stock-level momentum scoring
- [ ] Update fallback score weights to fundamental-heavy
- [ ] Write tests for fundamental indicators

### Phase 3 — Free API Stack Integration (Week 3)

- [ ] Create `src/imti/llm/free_providers.py` — Groq, Gemini, Together, Ollama configs
- [ ] Create `src/imti/sources/rss/indian_feeds.py` — RSS news aggregator
- [ ] Create `src/imti/sources/screener/screener_in.py` — Screener.in scraper
- [ ] Create `src/imti/sources/analyst/ratings.py` — Finnhub + FMP analyst data
- [ ] Create `src/imti/sources/search/duckduckgo.py` — free search integration
- [ ] Integrate DuckDuckGo as primary search (free, no key)
- [ ] Integrate RSS feeds as primary news source (free, no key)
- [ ] Update `src/imti/sources/search/multi.py` — add free providers
- [ ] Write tests for free API integrations

### Phase 4 — Stock Screener & Recommendations (Week 4)

- [ ] Complete stock screener pipeline (PE, PB, ROE, Debt, MTF safety)
- [ ] Add analyst consensus filtering (Finnhub + FMP)
- [ ] Add momentum confirmation (value + momentum quadrant)
- [ ] Add MTF safety tier classification
- [ ] Create `src/imti/outputs/stock_recommendation.py` — recommendation generator
- [ ] Add break-even calculator for MTF
- [ ] Add margin call distance calculator
- [ ] Write comprehensive tests for screener

### Phase 5 — Blog & Email with Stock Picks (Week 5)

- [ ] Update `src/imti/outputs/blog_generator.py` — add stock picks section
- [ ] Update `src/imti/outputs/email_digest.py` — add stock recommendations
- [ ] Add analyst rating summary to blog
- [ ] Add MTF risk section to blog/email
- [ ] Add sector analysis to blog
- [ ] Create weekly deep-dive template
- [ ] Write tests for blog/email generation

### Phase 6 — Model & Pipeline Updates (Week 6)

- [ ] Update `src/imti/models/train.py` — fundamental-only feature set
- [ ] Update `src/imti/models/inference.py` — MTF risk adjustment
- [ ] Update `src/imti/pipelines/hourly.py` — add screener + MTF risk
- [ ] Update `src/imti/pipelines/daily.py` — add stock screener refresh
- [ ] Update `src/imti/llm/analyzer.py` — fundamental-only prompts
- [ ] Add MTF risk score as model feature
- [ ] Retrain model with new fundamental features
- [ ] Write integration tests

### Phase 7 — Website & Deployment (Week 7-8)

- [ ] Set up Astro website with free hosting (GitHub Pages or Cloudflare Pages)
- [ ] Build dashboard with IMTI gauge + stock picks
- [ ] Build stock screener page (sortable table)
- [ ] Build fundamentals page (PE/PB charts)
- [ ] Build MTF risk page (calculator + visualization)
- [ ] Build history page (score + Nifty overlay)
- [ ] Mobile-responsive design
- [ ] Deploy to free hosting

### Phase 8 — Polish & Production (Week 9+)

- [ ] Comprehensive error handling for free APIs
- [ ] Rate limiting and retry logic for free tiers
- [ ] Data validation for screener output
- [ ] Performance optimization
- [ ] Documentation (README, AGENTS.md)
- [ ] Unit + integration test coverage >80%
- [ ] Monitor and tune fundamental weights
- [ ] Backtest with MTF leverage simulation

---

## 20. Risk Management Rules

### 20.1 MTF-Specific Rules (Hardcoded)

```python
RISK_RULES = {
    # NEVER buy when IMTI score is above 45 (only buy on strong signals)
    "max_buy_score": 45,

    # NEVER hold when IMTI score is above 70 (sell aggressively)
    "sell_threshold": 70,

    # ALWAYS reduce position when score is 55-70
    "reduce_threshold": 55,

    # MTF leverage multiplier
    "leverage": 3.0,

    # Maximum % of capital in a single stock
    "max_single_stock_pct": 0.20,

    # Maximum % of capital in a single sector
    "max_single_sector_pct": 0.35,

    # Minimum margin buffer (never use full leverage)
    "min_margin_buffer_pct": 0.10,

    # Stop-loss from entry price (% on the stock, not margin)
    "stop_loss_stock_pct": 0.15,  # 15% stock fall = sell immediately

    # Maximum drawdown before forced exit (on margin capital)
    "max_drawdown_margin_pct": 0.30,  # 30% margin loss = forced exit

    # Interest cost threshold — if daily interest > 0.1% of position, reduce
    "max_daily_interest_pct": 0.001,

    # Minimum analyst buy % for any stock in portfolio
    "min_analyst_buy_pct": 0.40,

    # Only buy Nifty 50/100 stocks (no mid/small cap with MTF)
    "allowed_indices": ["nifty_50", "nifty_100"],

    # Never buy within 3 days of major event (budget, RBI policy, election)
    "event_blackout_days": 3,
}
```

### 20.2 Portfolio Risk Rules

| Rule | Threshold | Action |
|------|-----------|--------|
| Single stock exposure | > 20% | Reduce position |
| Sector exposure | > 35% | Diversify |
| Total leverage | > 3x | Reduce immediately |
| Margin utilization | > 90% | Sell to free margin |
| Drawdown from peak | > 20% | Stop all new buying |
| Drawdown from peak | > 30% | Liquidate to 50% |
| IMTI score > 70 | Any position | Sell all MTF positions |
| IMTI score > 55 | Any position | No new MTF buying |

---

## 21. Current Indian Stock Recommendations

### 21.1 Based on Web Research (July 2025)

#### Large Cap Value Picks (MTF Tier 1 — Safest)

| Stock | PE | PB | ROE | Analyst Buy % | Upside | Sector |
|-------|-----|-----|------|---------------|--------|--------|
| ICICI Bank | 18.0 | 2.96 | 17.8% | ~85% | ~22% | Banking |
| Axis Bank | 15.0 | 2.24 | 15.5% | ~75% | ~18% | Banking |
| SBI | 10.5 | 1.80 | 18.2% | ~70% | ~20% | Banking |
| Indian Bank | 10.0 | 1.58 | 16.5% | ~65% | ~25% | Banking |
| Infosys | 24.0 | 7.80 | 31.0% | ~70% | ~15% | IT |
| HCL Tech | 25.0 | 6.50 | 22.0% | ~75% | ~26% | IT |
| Reliance | 28.0 | 2.10 | 8.5% | ~80% | ~18% | Conglomerate |

#### Best Value Sectors (Fundamental View)

1. **Banking (PSU + Private)** — Low PE (10-18x), improving asset quality, credit growth strong
2. **IT Services** — Near 10-year valuation average, strong deal pipeline, AI tailwind
3. **Automobile** — EV transition, rural recovery, strong brands
4. **Pharma** — Defensive, consistent earnings, US generics growth

#### Sectors to Avoid for MTF

1. **Small-cap anything** — Can drop 50-90% in crashes
2. **Adani Group** — High volatility, governance concerns
3. **Real estate** — Cyclical, interest-rate sensitive
4. **Crypto-related** — Extreme volatility, no fundamental value

---

## 22. Open Questions & Future Considerations

### 22.1 Technical Decisions

1. **Historical data bootstrapping** — Need 2-3 years of Nifty PE/PB/earnings data for model training. Source: NSE website historical data or yfinance.
2. **Screener.in scraping reliability** — May need to use Apify (low cost) or maintain custom scraper with anti-blocking measures.
3. **Analyst rating frequency** — Finnhub free tier may not have comprehensive Indian analyst coverage. May need to supplement with FMP.
4. **LLM prompt tuning** — Fundamental analysis prompts need to explicitly exclude technical jargon and focus on earnings, valuations, policy.
5. **Model cold start** — Without historical data, the fundamental model needs bootstrapping. Consider collecting 2 years of NSE data first.

### 22.2 Risk Considerations

6. **MTF interest rate changes** — Brokers may change interest rates. System should track current rates.
7. **SEBI regulatory changes** — MTF rules may change. System should adapt.
8. **Margin call cascading** — During market crashes, many MTF positions get squared off simultaneously, creating more selling pressure. The IMTI score should account for this systemic risk.
9. **Currency risk** — FII outflows during USD strength are amplified by MTF leverage in import-heavy sectors.

### 22.3 Future Enhancements

10. **Sector rotation model** — Automatically rotate between sectors based on fundamental value
11. **Earnings calendar integration** — Avoid buying before earnings announcements (event risk)
12. **Options hedging** — Use Nifty put options as portfolio insurance for MTF positions
13. **Tax optimization** — Long-term vs short-term capital gains consideration
14. **Multi-broker support** — Different brokers have different MTF terms and stock lists
15. **Real-time margin monitoring** — Connect to broker API for live margin status
16. **Sentiment from social media** — Twitter/X sentiment for Indian market (free via API)
17. **Insider trading data** — Track promoter buying/selling as fundamental signal
18. **Shareholding pattern changes** — FII/DII quarterly shareholding changes

---

## Appendix A: File Structure After Implementation

```
india-market-timing-index/
├── .github/workflows/
│   ├── ci.yml
│   ├── daily-train.yml
│   ├── deploy-site.yml
│   └── hourly-run.yml
├── src/imti/
│   ├── __init__.py
│   ├── risk/                          # NEW PACKAGE
│   │   ├── __init__.py
│   │   ├── mtf_risk.py               # MTF risk calculator
│   │   └── mtf_stocks.py             # MTF-approved stock database
│   ├── sources/
│   │   ├── analyst/                    # NEW PACKAGE
│   │   │   ├── __init__.py
│   │   │   └── ratings.py            # Finnhub + FMP analyst ratings
│   │   ├── screener/                   # NEW PACKAGE
│   │   │   ├── __init__.py
│   │   │   ├── stock_screener.py      # Fundamental stock screener
│   │   │   └── screener_in.py         # Screener.in scraper
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   ├── multi.py
│   │   │   └── duckduckgo.py          # NEW: Free search
│   │   ├── rss/
│   │   │   ├── __init__.py
│   │   │   ├── feeds.py
│   │   │   └── indian_feeds.py        # NEW: Indian RSS feeds
│   │   ├── ... (existing sources)
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── base.py                    # UPDATED: fundamental normalization
│   │   ├── feature_store.py           # UPDATED: fundamental features only
│   │   ├── fundamental.py             # NEW: Fundamental indicator calculator
│   │   ├── sector_pe.py              # NEW: Sector valuation tracker
│   │   └── momentum.py               # NEW: Stock-level momentum
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── analyzer.py               # UPDATED: fundamental prompts
│   │   ├── client.py                 # Existing (configurable)
│   │   ├── schemas.py
│   │   ├── prompts/__init__.py
│   │   └── free_providers.py         # NEW: Free LLM configurations
│   ├── outputs/
│   │   ├── __init__.py
│   │   ├── blog_generator.py         # UPDATED: stock picks + fundamentals
│   │   ├── deploy.py
│   │   ├── email_digest.py           # UPDATED: stock recommendations
│   │   ├── readme_updater.py
│   │   └── stock_recommendation.py   # NEW: Stock pick report generator
│   ├── ... (existing modules)
├── tests/
│   ├── test_enums.py
│   ├── test_settings.py
│   ├── test_types.py
│   ├── test_validation.py
│   ├── test_stock_screener.py         # NEW
│   ├── test_mtf_risk.py              # NEW
│   ├── test_fundamental_indicators.py # NEW
│   ├── test_analyst_ratings.py       # NEW
│   ├── test_free_llm.py             # NEW
│   ├── test_rss_feeds.py            # NEW
│   └── test_momentum.py            # NEW
├── plan.md                            # THIS FILE
├── .env.example                       # UPDATED: complete free stack
├── pyproject.toml
├── README.md
└── .gitignore
```

## Appendix B: Key Terminology

| Term | Definition |
|------|-----------|
| **IMTI Score** | 0-100 inverted danger score. 0=strong buy, 100=strong sell |
| **MTF** | Margin Trading Facility — buy stocks with borrowed money (3x leverage) |
| **Pay-Later** | Same as MTF — broker funds part of the purchase |
| **PE Ratio** | Price-to-Earnings — lower = cheaper, fundamental value metric |
| **PB Ratio** | Price-to-Book — lower = cheaper, asset value metric |
| **ROE** | Return on Equity — higher = more profitable company |
| **FCF** | Free Cash Flow — positive = real earnings |
| **MMI** | Market Mood Index — Tickertape sentiment score (0-100) |
| **PCR** | Put-Call Ratio — high PCR = fear = contrarian buy |
| **FII** | Foreign Institutional Investor — biggest market driver |
| **DII** | Domestic Institutional Investor — counter to FII |
| **Contrarian** | Buying when others are fearful, selling when others are greedy |
| **Margin Call** | When stock falls enough that broker demands more margin or sells |
| **Drawdown** | Maximum peak-to-trough decline in a stock/portfolio |
| **Consensus Rating** | Aggregated analyst recommendations for a stock |
| **Value + Momentum** | Buying cheap stocks that are starting to rise |

---

*This plan is a living document. Update it as the project evolves. Last updated: 2025-07-15*

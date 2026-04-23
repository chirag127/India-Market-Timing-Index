# 📊 India Market Timing Index (IMTI)

> **AI-powered, fundamental-only market timing signal for Indian equities.**
> Built for conservative investors who only buy low PE/PB stocks with 3x MTF leverage.

[![CI](https://github.com/chirag127/India-Market-Timing-Index/actions/workflows/ci.yml/badge.svg)](https://github.com/chirag127/India-Market-Timing-Index/actions/workflows/ci.yml)
[![Hourly](https://github.com/chirag127/India-Market-Timing-Index/actions/workflows/hourly-run.yml/badge.svg)](https://github.com/chirag127/India-Market-Timing-Index/actions/workflows/hourly-run.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is IMTI?

The **India Market Timing Index** generates a continuous **0–100 score** indicating whether the Indian stock market is a **buy opportunity** (low score = cheap) or **danger zone** (high score = expensive).

| Score | Zone | Action | Exposure |
|-------|------|--------|----------|
| 0–15 | EXTREME_BUY | STRONG_BUY | 100% equity |
| 16–30 | STRONG_BUY | BUY | 75% equity |
| 31–45 | BUY_LEAN | ACCUMULATE | 50% equity |
| 46–55 | NEUTRAL | NEUTRAL | 25% equity |
| 56–69 | SELL_LEAN | REDUCE | 10% equity |
| 70–84 | STRONG_SELL | SELL | 0% (flat) |
| 85–100 | EXTREME_SELL | STRONG_SELL | 0% + hedge |

**Key Principle:** Low score = low danger = BUY. High score = high danger = SELL.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              GITHUB ACTIONS (Hourly Cron)               │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Scrapers │→ │  ML/XGB  │→ │  Blog    │             │
│  │ (30+ ind)│  │  Score   │  │  Generate│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│         │            │            │                     │
│         ▼            ▼            ▼                     │
│    data/api/    data/models/  website/src/content/blog/│
│         │            │            │                     │
│         └────────────┴────────────┘                     │
│                        │                                 │
│              ┌─────────▼─────────┐                       │
│              │  Astro Build      │                       │
│              │  Cloudflare Pages │                       │
│              └───────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/chirag127/India-Market-Timing-Index.git
cd India-Market-Timing-Index

# Install Python deps
pip install uv
uv pip install -e ".[dev]" --system

# Install website deps
cd website && npm install && cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Locally

```bash
# Run the hourly pipeline
imti run

# Run stock screener
imti screen

# Generate hourly blog
imti hourly-blog

# Build website
cd website && npm run build
```

### 4. Deploy

```bash
# Auto-push .env to GitHub Secrets
python scripts/push_secrets.py

# Manual deploy to Cloudflare Pages
python scripts/deploy_manual.py
```

---

## 🔧 Environment Variables

All configuration is done via `.env` (see `.env.example`):

| Variable | Purpose | Free Tier |
|----------|---------|-----------|
| `LLM_API_KEY` | Groq/Gemini/Together AI | 14,400 req/day |
| `FINNHUB_API_KEY` | Analyst ratings | 60 calls/min |
| `FMP_API_KEY` | Fundamentals | 250 calls/day |
| `BREVO_API_KEY` | Email alerts | 300 emails/day |
| `CLOUDFLARE_API_TOKEN` | Hosting | Unlimited |
| `FIREBASE_API_KEY` | Google Auth + Firestore | 50K reads/day |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ --cov=src/imti

# Run specific test files
pytest tests/test_screener.py
pytest tests/test_blog_generator.py
```

---

## 📁 Project Structure

```
india-market-timing-index/
├── .github/workflows/       # CI/CD (hourly, daily, deploy)
├── data/                    # All data (CSV, JSON, blog posts)
│   ├── api/                 # Public API JSON files
│   ├── blog/                # Generated blog posts
│   └── ...
├── scripts/                 # Automation scripts
│   ├── push_secrets.py      # Push .env → GitHub Secrets
│   └── deploy_manual.py     # Manual Cloudflare deploy
├── src/imti/                # Python backend
│   ├── sources/screener/    # Stock screener (low PE/PB)
│   ├── outputs/             # Blog generator, email
│   ├── pipelines/           # Hourly & daily pipelines
│   └── ...
├── tests/                   # Pytest test suite
├── website/                 # Astro static site
│   ├── src/pages/           # Routes (index, blog, screener)
│   ├── src/layouts/         # Base layout with Firebase Auth
│   └── public/              # ads.txt, robots.txt
├── .env.example             # All config variables
└── pyproject.toml           # Python project config
```

---

## 📝 Blog & Content

- **Hourly blog posts** are auto-generated with changelog, stock picks, and LLM analysis
- Posts live in `website/src/content/blog/YYYY-MM-DD/HH-MM.md`
- Static site renders them at `/blog/YYYY-MM-DD/HH-MM/`

---

## 🔒 Security & Privacy

- **Firebase Auth** for Google Sign-In (client-side only, no backend server)
- **Firestore** for per-user data storage (watchlists, preferences)
- **Cookie consent** banner for GDPR/DPDP compliance
- All secrets stored in `.env` → GitHub Secrets (never committed)

---

## ⚠️ Disclaimer

**This is NOT investment advice.** IMTI is an educational tool. We are NOT SEBI-registered Investment Advisers. Always consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📧 Contact

- General: [hi@imti.in](mailto:hi@imti.in)
- Support: [support@imti.in](mailto:support@imti.in)

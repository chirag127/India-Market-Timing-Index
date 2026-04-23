"""Central configuration for the IMTI system.

All settings are loaded from environment variables.
In development, these can be set via a .env file.
In production (GitHub Actions), these are set as GitHub Secrets.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present (development only)
load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    Every configurable aspect of the system can be changed via env vars,
    including the LLM provider (base URL + API key + model).
    """

    # --- Feature Flags ---
    enable_email: bool
    enable_llm: bool
    enable_deploy: bool
    enable_news_search: bool
    enable_blog_generation: bool
    log_level: str

    # --- LLM Configuration (flexible — swap provider via env vars) ---
    llm_api_key: str
    llm_api_base_url: str
    llm_model: str
    llm_max_tokens: int

    # --- Search APIs ---
    search_google_api_key: str
    search_google_cx: str
    search_tavily_api_key: str
    search_brave_api_key: str
    newsapi_key: str

    # --- Email ---
    sendgrid_api_key: str
    email_from: str
    email_to: str

    # --- Cloudflare ---
    cloudflare_api_token: str
    cloudflare_account_id: str
    cloudflare_project_name: str

    # --- Stock Screener & Analyst APIs (all free tiers) ---
    finnhub_api_key: str
    fmp_api_key: str
    twelvedata_api_key: str
    screener_in_enabled: bool

    # --- MTF Risk Configuration ---
    mtf_leverage_multiplier: float
    mtf_interest_rate_annual: float
    mtf_margin_call_threshold: float
    mtf_max_stock_drawdown_allowed: float

    # --- Stock Screener Configuration ---
    screener_max_pe: float
    screener_max_pb: float
    screener_min_roe: float
    screener_max_debt_equity: float
    screener_min_analyst_buy_pct: float
    screener_min_target_upside_pct: float
    screener_max_promoter_pledge_pct: float

    # --- Optional Data APIs ---
    fred_api_key: str
    alphavantage_api_key: str

    # --- GitHub ---
    github_token: str

    # --- Data Directories ---
    data_dir: str

    def __init__(self) -> None:
        """Load all settings from environment variables with defaults."""
        # Feature flags
        self.enable_email = self._bool("IMTI_ENABLE_EMAIL", True)
        self.enable_llm = self._bool("IMTI_ENABLE_LLM", True)
        self.enable_deploy = self._bool("IMTI_ENABLE_DEPLOY", True)
        self.enable_news_search = self._bool("IMTI_ENABLE_NEWS_SEARCH", True)
        self.enable_blog_generation = self._bool("IMTI_ENABLE_BLOG_GENERATION", True)
        self.enable_stock_screener = self._bool("IMTI_ENABLE_STOCK_SCREENER", True)
        self.enable_analyst_ratings = self._bool("IMTI_ENABLE_ANALYST_RATINGS", True)
        self.enable_mtf_risk_check = self._bool("IMTI_ENABLE_MTF_RISK_CHECK", True)
        self.log_level = os.getenv("IMTI_LOG_LEVEL", "INFO")

        # LLM — fully configurable: change provider, model, key via env vars
        # Examples:
        #   OpenAI:    LLM_API_BASE_URL=https://api.openai.com/v1  LLM_MODEL=gpt-4o-mini
        #   Anthropic: LLM_API_BASE_URL=https://api.anthropic.com   LLM_MODEL=claude-3-haiku
        #   Groq:      LLM_API_BASE_URL=https://api.groq.com/openai/v1  LLM_MODEL=llama-3
        #   Ollama:    LLM_API_BASE_URL=http://localhost:11434/v1  LLM_MODEL=llama3
        #   Any OpenAI-compatible API: just change base_url + api_key + model
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_api_base_url = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))

        # Search APIs
        self.search_google_api_key = os.getenv("SEARCH_GOOGLE_API_KEY", "")
        self.search_google_cx = os.getenv("SEARCH_GOOGLE_CX", "")
        self.search_tavily_api_key = os.getenv("SEARCH_TAVILY_API_KEY", "")
        self.search_brave_api_key = os.getenv("SEARCH_BRAVE_API_KEY", "")
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")

        # Email — multiple free providers supported
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        self.brevo_api_key = os.getenv("BREVO_API_KEY", "")
        self.resend_api_key = os.getenv("RESEND_API_KEY", "")
        self.gmail_address = os.getenv("GMAIL_ADDRESS", "")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "imti@example.com")
        self.email_to = os.getenv("EMAIL_TO", "")

        # Cloudflare
        self.cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN", "")
        self.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        self.cloudflare_project_name = os.getenv("CLOUDFLARE_PROJECT_NAME", "imti")

        # Hosting provider (github_pages, cloudflare_pages, netlify)
        self.hosting_provider = os.getenv("HOSTING_PROVIDER", "github_pages")

        # Stock Screener & Analyst APIs (all free tiers)
        self.finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
        self.fmp_api_key = os.getenv("FMP_API_KEY", "")
        self.twelvedata_api_key = os.getenv("TWELVEDATA_API_KEY", "")
        self.screener_in_enabled = self._bool("SCREENER_IN_ENABLED", True)

        # MTF Risk Configuration
        self.mtf_leverage_multiplier = float(os.getenv("MTF_LEVERAGE_MULTIPLIER", "3.0"))
        self.mtf_interest_rate_annual = float(os.getenv("MTF_INTEREST_RATE_ANNUAL", "0.12"))
        self.mtf_margin_call_threshold = float(os.getenv("MTF_MARGIN_CALL_THRESHOLD", "0.25"))
        self.mtf_max_stock_drawdown_allowed = float(os.getenv("MTF_MAX_STOCK_DRAWDOWN_ALLOWED", "0.40"))

        # Stock Screener Configuration
        self.screener_max_pe = float(os.getenv("SCREENER_MAX_PE", "20"))
        self.screener_max_pb = float(os.getenv("SCREENER_MAX_PB", "3.0"))
        self.screener_min_roe = float(os.getenv("SCREENER_MIN_ROE", "0.12"))
        self.screener_max_debt_equity = float(os.getenv("SCREENER_MAX_DEBT_EQUITY", "1.0"))
        self.screener_min_analyst_buy_pct = float(os.getenv("SCREENER_MIN_ANALYST_BUY_PCT", "0.40"))
        self.screener_min_target_upside_pct = float(os.getenv("SCREENER_MIN_TARGET_UPSIDE_PCT", "0.15"))
        self.screener_max_promoter_pledge_pct = float(os.getenv("SCREENER_MAX_PROMOTER_PLEDGE_PCT", "0.10"))

        # Optional APIs
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.alphavantage_api_key = os.getenv("ALPHAVANTAGE_API_KEY", "")

        # GitHub
        self.github_token = os.getenv("GITHUB_TOKEN", "")

        # Data directories
        self.data_dir = os.getenv("IMTI_DATA_DIR", "data")

    @staticmethod
    def _bool(key: str, default: bool) -> bool:
        """Parse a boolean env var."""
        val = os.getenv(key, "").lower()
        if val in ("true", "1", "yes"):
            return True
        if val in ("false", "0", "no"):
            return False
        return default

    @property
    def llm_is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(self.llm_api_key and self.llm_api_base_url and self.llm_model)

    @property
    def email_is_configured(self) -> bool:
        """Check if email sending is configured (any provider)."""
        return bool(
            (self.sendgrid_api_key or self.brevo_api_key or self.resend_api_key
             or (self.gmail_address and self.gmail_app_password))
            and self.email_to
        )

    @property
    def search_is_configured(self) -> bool:
        """Check if at least one search API is configured.
        DuckDuckGo is always available (free, no key needed)."""
        return True  # DuckDuckGo is always available as free fallback

    @property
    def analyst_is_configured(self) -> bool:
        """Check if at least one analyst rating API is configured."""
        return bool(self.finnhub_api_key or self.fmp_api_key)

    @property
    def screener_is_configured(self) -> bool:
        """Check if stock screener can run."""
        return self.screener_in_enabled or self.analyst_is_configured


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()

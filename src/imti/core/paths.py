"""Path management for the IMTI project."""

from pathlib import Path

from imti.config.settings import get_settings


def get_project_root() -> Path:
    """Find the project root directory (contains pyproject.toml)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


class ProjectPaths:
    """Centralized path definitions for all project data directories."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            settings = get_settings()
            root = get_project_root()
            base_dir = root / settings.data_dir
        self.base = Path(base_dir)

    @property
    def raw(self) -> Path:
        return self.base / "raw"

    @property
    def normalized(self) -> Path:
        return self.base / "normalized"

    @property
    def snapshots(self) -> Path:
        return self.base / "snapshots"

    @property
    def indicators(self) -> Path:
        return self.base / "indicators"

    @property
    def indicators_hourly(self) -> Path:
        return self.indicators / "hourly"

    @property
    def features(self) -> Path:
        return self.base / "features"

    @property
    def models(self) -> Path:
        return self.base / "models"

    @property
    def experiments(self) -> Path:
        return self.base / "experiments"

    @property
    def backtests(self) -> Path:
        return self.base / "backtests"

    @property
    def news(self) -> Path:
        return self.base / "news"

    @property
    def api(self) -> Path:
        return self.base / "api"

    @property
    def blog(self) -> Path:
        return self.base / "blog"

    @property
    def errors(self) -> Path:
        return self.base / "errors"

    @property
    def source_health(self) -> Path:
        return self.base / "source-health"

    def ensure_all_dirs(self) -> None:
        """Create all data directories if they don't exist."""
        dirs = [
            self.raw, self.normalized, self.snapshots,
            self.indicators, self.indicators_hourly,
            self.features, self.models, self.experiments,
            self.backtests, self.news, self.api,
            self.blog, self.errors, self.source_health,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def raw_source_dir(self, source_name: str) -> Path:
        """Get directory for raw data from a specific source."""
        return self.raw / source_name

    def raw_source_date_dir(self, source_name: str, date_str: str) -> Path:
        """Get directory for raw data from a source on a specific date."""
        return self.raw / source_name / date_str

    def snapshot_file(self, timestamp_str: str) -> Path:
        """Get path for a specific snapshot file."""
        return self.snapshots / f"{timestamp_str}.json"

    def news_file(self, date_str: str) -> Path:
        """Get path for a specific date's news data."""
        return self.news / f"{date_str}.json"

    def blog_file(self, date_str: str) -> Path:
        """Get path for a specific date's blog data."""
        return self.blog / f"{date_str}.json"

    def hourly_indicator_file(self, date_str: str) -> Path:
        """Get path for a specific date's hourly indicators CSV."""
        return self.indicators_hourly / f"{date_str}.csv"

    def source_health_file(self, date_str: str) -> Path:
        """Get path for a specific date's source health report."""
        return self.source_health / f"{date_str}.json"

    def error_file(self, timestamp_str: str) -> Path:
        """Get path for a specific error log."""
        return self.errors / f"{timestamp_str}.json"

"""JSON storage for snapshots, news archives, and blog data.

Stores complete snapshots, news collections, and blog page data
as JSON files for API serving and historical reference.
"""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Any

from imti.core.logger import get_logger
from imti.core.types import Snapshot, DailyBlogData

logger = get_logger("storage.json")


class JSONStore:
    """JSON-based storage for snapshots, news, and blog data."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            from imti.core.paths import ProjectPaths
            paths = ProjectPaths()
            base_dir = paths.base
        self.base_dir = Path(base_dir)
        self.snapshots_dir = self.base_dir / "snapshots"
        self.news_dir = self.base_dir / "news"
        self.blog_dir = self.base_dir / "blog"
        self.api_dir = self.base_dir / "api"

        for d in [self.snapshots_dir, self.news_dir, self.blog_dir, self.api_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: Snapshot) -> Path:
        """Save a complete snapshot as JSON."""
        ts_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        path = self.snapshots_dir / f"{ts_str}.json"

        data = snapshot.model_dump(mode="json")
        # Convert datetime objects to strings
        self._serialize_datetimes(data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved snapshot to {path}")
        return path

    def save_news(self, target_date: date, headlines: list[str],
                  llm_analysis: dict[str, Any] | None = None) -> Path:
        """Save a day's news collection and LLM analysis."""
        date_str = target_date.strftime("%Y-%m-%d")
        path = self.news_dir / f"{date_str}.json"

        data = {
            "date": date_str,
            "headlines": headlines,
            "llm_analysis": llm_analysis,
            "saved_at": datetime.now().isoformat(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved news data to {path}")
        return path

    def save_blog_data(self, blog_data: DailyBlogData) -> Path:
        """Save blog page data for a specific date."""
        date_str = blog_data.date.strftime("%Y-%m-%d")
        path = self.blog_dir / f"{date_str}.json"

        data = blog_data.model_dump(mode="json")
        self._serialize_datetimes(data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved blog data to {path}")
        return path

    def save_api_response(self, endpoint: str, data: dict[str, Any]) -> Path:
        """Save an API response for serving via the website."""
        path = self.api_dir / f"{endpoint}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved API response to {path}")
        return path

    def load_latest_snapshot(self) -> dict[str, Any] | None:
        """Load the most recent snapshot."""
        snapshots = sorted(self.snapshots_dir.glob("*.json"))
        if not snapshots:
            return None

        latest = snapshots[-1]
        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_blog_data(self, target_date: date) -> dict[str, Any] | None:
        """Load blog data for a specific date."""
        date_str = target_date.strftime("%Y-%m-%d")
        path = self.blog_dir / f"{date_str}.json"

        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _serialize_datetimes(obj: Any) -> None:
        """Convert datetime objects to ISO strings in-place (handles nested dicts/lists)."""
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if isinstance(value, datetime):
                    obj[key] = value.isoformat()
                elif isinstance(value, date):
                    obj[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    JSONStore._serialize_datetimes(value)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                if isinstance(value, datetime):
                    obj[i] = value.isoformat()
                elif isinstance(value, date):
                    obj[i] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    JSONStore._serialize_datetimes(value)

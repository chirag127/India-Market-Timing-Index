"""CSV storage for indicator time-series data.

Stores hourly indicator snapshots as CSV files for backtesting
and historical analysis. One CSV per day with hourly rows.
"""

from __future__ import annotations

from datetime import datetime, date
from pathlib import Path
from typing import Any

import pandas as pd

from imti.core.logger import get_logger
from imti.core.types import Snapshot

logger = get_logger("storage.csv")


class CSVStore:
    """CSV-based storage for indicator time-series data.

    Stores one CSV file per trading day, with each row representing
    an hourly snapshot of all indicator values.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            from imti.core.paths import ProjectPaths
            paths = ProjectPaths()
            data_dir = paths.indicators_hourly
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: Snapshot) -> Path:
        """Save a snapshot's indicator values to the daily CSV."""
        date_str = snapshot.timestamp.strftime("%Y-%m-%d")
        csv_path = self.data_dir / f"{date_str}.csv"

        # Build row from indicator values
        row: dict[str, Any] = {
            "timestamp": snapshot.timestamp.isoformat(),
            "run_type": snapshot.run_type.value,
            "market_status": snapshot.market_status.value,
        }

        for name, iv in snapshot.indicators.items():
            row[name] = iv.value

        # Append to existing CSV or create new one
        new_row = pd.DataFrame([row])

        if csv_path.exists():
            existing = pd.read_csv(csv_path)
            combined = pd.concat([existing, new_row], ignore_index=True)
            combined.to_csv(csv_path, index=False)
        else:
            new_row.to_csv(csv_path, index=False)

        logger.info(f"Saved snapshot to {csv_path}")
        return csv_path

    def load_day(self, target_date: date) -> pd.DataFrame:
        """Load all hourly snapshots for a specific date."""
        date_str = target_date.strftime("%Y-%m-%d")
        csv_path = self.data_dir / f"{date_str}.csv"

        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def load_range(self, start: date, end: date) -> pd.DataFrame:
        """Load all snapshots for a date range."""
        frames: list[pd.DataFrame] = []
        current = start
        while current <= end:
            df = self.load_day(current)
            if not df.empty:
                frames.append(df)
            # Move to next day
            from datetime import timedelta
            current = current + timedelta(days=1)

        if frames:
            return pd.concat(frames, ignore_index=True)
        return pd.DataFrame()

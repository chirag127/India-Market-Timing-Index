"""Abstract base class for all data source connectors.

Every connector (NSE, Yahoo, Tickertape, etc.) implements this interface.
The SourceRegistry resolves requests through primary → fallback chains.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from imti.core.enums import SourceStatus
from imti.core.logger import get_logger
from imti.core.types import SourceHealth


class BaseSource(ABC):
    """Abstract base class for a data source connector.

    Subclasses must implement `fetch()` and declare their `name`, `priority`,
    and which indicators they can provide.
    """

    # Subclasses must set these
    name: str = "unknown"
    priority: int = 100  # Lower = higher priority (tried first)
    timeout_seconds: float = 30.0
    max_retries: int = 2

    # Which indicators this source can provide
    provides: list[str] = []

    def __init__(self) -> None:
        self.logger = get_logger(f"source.{self.name}")
        self._last_fetch_time: float = 0.0
        self._last_fetch_status: SourceStatus = SourceStatus.SUCCESS

    @abstractmethod
    def fetch(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch data from this source.

        Returns:
            Dictionary of {indicator_name: raw_value} pairs.
            Must also include "_metadata" key with source-specific info.
        """
        ...

    def safe_fetch(self, **kwargs: Any) -> tuple[dict[str, Any], SourceHealth]:
        """Fetch with error handling, timing, and health reporting.

        Returns:
            (data_dict, source_health_record)
        """
        start = time.monotonic()
        data: dict[str, Any] = {}
        status = SourceStatus.SUCCESS
        error_msg: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                data = self.fetch(**kwargs)
                status = SourceStatus.SUCCESS
                break
            except TimeoutError:
                status = SourceStatus.TIMEOUT
                error_msg = f"Timeout after {self.timeout_seconds}s (attempt {attempt})"
                self.logger.warning(error_msg)
            except ConnectionError as e:
                status = SourceStatus.FAILED
                error_msg = f"Connection error: {e} (attempt {attempt})"
                self.logger.warning(error_msg)
            except Exception as e:
                status = SourceStatus.FAILED
                error_msg = f"Unexpected error: {e} (attempt {attempt})"
                self.logger.warning(error_msg)

            if attempt < self.max_retries:
                time.sleep(1.0 * attempt)  # Simple backoff

        latency_ms = (time.monotonic() - start) * 1000
        self._last_fetch_time = time.monotonic()
        self._last_fetch_status = status

        health = SourceHealth(
            source_name=self.name,
            fetch_timestamp=datetime.now(),
            source_status=status,
            latency_ms=latency_ms,
            error_message=error_msg,
        )

        if status != SourceStatus.SUCCESS:
            data = {}  # Return empty on failure

        return data, health

    def can_provide(self, indicator_name: str) -> bool:
        """Check if this source can provide a specific indicator."""
        return indicator_name in self.provides

    @property
    def last_status(self) -> SourceStatus:
        """Status of the most recent fetch attempt."""
        return self._last_fetch_status

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} priority={self.priority}>"

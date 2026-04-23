"""Source registry with fallback chain resolution.

The registry maps each indicator to an ordered list of source connectors.
When fetching, it tries the primary source first, then fallbacks in order.
This provides 45+ source connectors with 2–5 fallbacks per indicator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from imti.core.enums import SourceStatus
from imti.core.logger import get_logger
from imti.core.types import SourceHealth
from imti.sources.base import BaseSource

logger = get_logger("registry")


class SourceRegistry:
    """Registry of all data source connectors with fallback resolution.

    Each indicator maps to an ordered list of sources (primary → fallbacks).
    Fetching tries each source in order until one succeeds.
    """

    def __init__(self) -> None:
        self._sources: dict[str, BaseSource] = {}  # name -> source instance
        self._indicator_sources: dict[str, list[str]] = {}  # indicator -> [source_names]

    def register(self, source: BaseSource) -> None:
        """Register a source connector."""
        self._sources[source.name] = source
        for indicator in source.provides:
            if indicator not in self._indicator_sources:
                self._indicator_sources[indicator] = []
            if source.name not in self._indicator_sources[indicator]:
                self._indicator_sources[indicator].append(source.name)
                # Sort by priority — lower number = tried first
                self._indicator_sources[indicator].sort(
                    key=lambda n: self._sources[n].priority
                )
        logger.info(f"Registered source: {source.name} (provides: {len(source.provides)} indicators)")

    def get_source(self, name: str) -> BaseSource | None:
        """Get a source by name."""
        return self._sources.get(name)

    @property
    def source_names(self) -> list[str]:
        """List of all registered source names."""
        return list(self._sources.keys())

    @property
    def source_count(self) -> int:
        """Number of registered sources."""
        return len(self._sources)

    def fetch_indicator(self, indicator_name: str, **kwargs: Any) -> tuple[float | None, SourceHealth]:
        """Fetch a single indicator value with fallback resolution.

        Tries each source in priority order until one succeeds.

        Returns:
            (value, source_health_record)
        """
        source_names = self._indicator_sources.get(indicator_name, [])
        if not source_names:
            health = SourceHealth(
                source_name="none",
                fetch_timestamp=datetime.now(),
                source_status=SourceStatus.FAILED,
                error_message=f"No source registered for indicator '{indicator_name}'",
            )
            return None, health

        for source_name in source_names:
            source = self._sources[source_name]
            data, health = source.safe_fetch(**kwargs)

            if indicator_name in data and data[indicator_name] is not None:
                if source_name != source_names[0]:
                    health.fallback_triggered = True
                    health.fallback_source = source_name
                    health.source_status = SourceStatus.FALLBACK_USED
                    logger.info(
                        f"Using fallback '{source_name}' for indicator '{indicator_name}'"
                    )
                return data[indicator_name], health

        # All sources failed
        health.source_status = SourceStatus.FAILED
        health.error_message = f"All sources failed for indicator '{indicator_name}'"
        return None, health

    def fetch_list_indicator(self, indicator_name: str, **kwargs: Any) -> tuple[list[str] | None, SourceHealth]:
        """Fetch a list-type indicator (e.g., headlines) with fallback resolution.

        Unlike fetch_indicator which returns a scalar float, this returns
        a list of strings for indicators like 'rss_headlines'.

        Returns:
            (list_of_strings, source_health_record)
        """
        source_names = self._indicator_sources.get(indicator_name, [])
        if not source_names:
            health = SourceHealth(
                source_name="none",
                fetch_timestamp=datetime.now(),
                source_status=SourceStatus.FAILED,
                error_message=f"No source registered for indicator '{indicator_name}'",
            )
            return None, health

        for source_name in source_names:
            source = self._sources[source_name]
            data, health = source.safe_fetch(**kwargs)

            if indicator_name in data and isinstance(data[indicator_name], list):
                if source_name != source_names[0]:
                    health.fallback_triggered = True
                    health.fallback_source = source_name
                    health.source_status = SourceStatus.FALLBACK_USED
                    logger.info(
                        f"Using fallback '{source_name}' for list indicator '{indicator_name}'"
                    )
                return data[indicator_name], health

        # All sources failed
        health.source_status = SourceStatus.FAILED
        health.error_message = f"All sources failed for list indicator '{indicator_name}'"
        return None, health

    def fetch_all(self, indicators: list[str] | None = None, **kwargs: Any) -> tuple[dict[str, float], list[SourceHealth]]:
        """Fetch multiple indicators with fallback resolution.

        Args:
            indicators: List of indicator names to fetch. If None, fetches all.

        Returns:
            (values_dict, health_records)
        """
        if indicators is None:
            indicators = list(self._indicator_sources.keys())

        values: dict[str, float] = {}
        health_records: list[SourceHealth] = []

        for indicator_name in indicators:
            value, health = self.fetch_indicator(indicator_name, **kwargs)
            if value is not None:
                values[indicator_name] = value
            health_records.append(health)

        success_count = sum(1 for h in health_records if h.source_status == SourceStatus.SUCCESS)
        logger.info(
            f"Fetched {success_count}/{len(indicators)} indicators successfully "
            f"({len(values)} values returned)"
        )
        return values, health_records

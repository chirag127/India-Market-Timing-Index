"""Source health audit — tracks source reliability and fallback usage.

After each snapshot, the audit records which sources succeeded/failed,
how often fallbacks were triggered, and produces a health report
for the daily blog.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from imti.core.enums import SourceStatus
from imti.core.logger import get_logger
from imti.core.types import Snapshot, SourceHealth

logger = get_logger("ingestion.audit")


class SourceAudit:
    """Audits source health and produces reliability reports."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def audit_snapshot(self, snapshot: Snapshot) -> dict[str, Any]:
        """Produce an audit report from a snapshot's source health records."""
        health_records = snapshot.source_health

        total = len(health_records)
        success = sum(1 for h in health_records if h.source_status == SourceStatus.SUCCESS)
        fallback = sum(1 for h in health_records if h.fallback_triggered)
        failed = sum(1 for h in health_records if h.source_status == SourceStatus.FAILED)
        timeout = sum(1 for h in health_records if h.source_status == SourceStatus.TIMEOUT)
        stale = sum(1 for h in health_records if h.source_status == SourceStatus.STALE_DATA)

        # Compute average latency
        latencies = [h.latency_ms for h in health_records if h.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Find slowest and fastest sources
        by_latency = sorted(
            [h for h in health_records if h.latency_ms is not None],
            key=lambda h: h.latency_ms or 0,
        )
        slowest = by_latency[-1].source_name if by_latency else "none"
        fastest = by_latency[0].source_name if by_latency else "none"

        # Find all failed sources
        failed_names = [h.source_name for h in health_records if h.source_status == SourceStatus.FAILED]

        report = {
            "timestamp": snapshot.timestamp.isoformat(),
            "date": snapshot.timestamp.strftime("%Y-%m-%d"),
            "total_sources": total,
            "success_count": success,
            "fallback_count": fallback,
            "failed_count": failed,
            "timeout_count": timeout,
            "stale_count": stale,
            "success_rate": success / total if total > 0 else 0.0,
            "avg_latency_ms": avg_latency,
            "slowest_source": slowest,
            "fastest_source": fastest,
            "failed_sources": failed_names,
            "indicators_available": len(snapshot.indicators),
            "indicators_stale": len(snapshot.stale_indicators),
        }

        self._history.append(report)

        logger.info(
            f"Source audit: {success}/{total} OK, {fallback} fallbacks, "
            f"{failed} failed, avg latency {avg_latency:.0f}ms"
        )

        return report

    def get_daily_summary(self, target_date: date | None = None) -> dict[str, Any]:
        """Get a summary of all audits for a specific date."""
        if target_date is None:
            target_date = date.today()

        date_str = target_date.isoformat()
        day_reports = [r for r in self._history if r.get("date") == date_str]

        if not day_reports:
            return {"date": date_str, "runs": 0, "summary": "no data"}

        total_runs = len(day_reports)
        avg_success_rate = sum(r["success_rate"] for r in day_reports) / total_runs
        all_failed = set()
        for r in day_reports:
            all_failed.update(r.get("failed_sources", []))

        return {
            "date": date_str,
            "runs": total_runs,
            "avg_success_rate": avg_success_rate,
            "sources_that_failed_at_least_once": list(all_failed),
            "worst_run": min(day_reports, key=lambda r: r["success_rate"]),
            "best_run": max(day_reports, key=lambda r: r["success_rate"]),
        }

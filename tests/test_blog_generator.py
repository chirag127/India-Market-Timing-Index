"""Tests for the blog generator module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from imti.outputs.blog_generator import _build_changelog_section, _build_indicator_table, _compute_changelog


class TestComputeChangelog:
    """Tests for changelog computation."""

    def test_first_run(self) -> None:
        changes = _compute_changelog(None, None)
        assert len(changes) == 1
        assert changes[0]["type"] == "info"
        assert "First run" in changes[0]["message"]

    def test_no_changes(self) -> None:
        current = MagicMock()
        current.indicators = {
            "tickertape_mmi": MagicMock(value=50.0),
            "india_vix": MagicMock(value=15.0),
        }
        current.indices = {"nifty_50": {"score": 50.0}}
        previous = MagicMock()
        previous.indicators = {
            "tickertape_mmi": MagicMock(value=50.0),
            "india_vix": MagicMock(value=15.0),
        }
        previous.indices = {"nifty_50": {"score": 50.0}}
        changes = _compute_changelog(current, previous)
        assert len(changes) == 1
        assert "No significant changes" in changes[0]["message"]

    def test_indicator_change(self) -> None:
        current = MagicMock()
        current.indicators = {
            "tickertape_mmi": MagicMock(value=55.0),
        }
        current.indices = {"nifty_50": {"score": 50.0}}
        previous = MagicMock()
        previous.indicators = {
            "tickertape_mmi": MagicMock(value=50.0),
        }
        previous.indices = {"nifty_50": {"score": 50.0}}
        changes = _compute_changelog(current, previous)
        assert len(changes) == 1
        assert changes[0]["type"] == "indicator_change"
        assert changes[0]["label"] == "Tickertape MMI"
        assert "📈" in changes[0]["direction"]

    def test_score_change(self) -> None:
        current = MagicMock()
        current.indicators = {}
        current.indices = {"nifty_50": {"score": 45.0}}
        previous = MagicMock()
        previous.indicators = {}
        previous.indices = {"nifty_50": {"score": 40.0}}
        changes = _compute_changelog(current, previous)
        assert changes[0]["type"] == "score_change"
        assert changes[0]["label"] == "IMTI Score"


class TestBuildChangelogSection:
    """Tests for changelog markdown rendering."""

    def test_empty(self) -> None:
        md = _build_changelog_section([])
        assert "No changes detected" in md

    def test_score_change(self) -> None:
        changes = [{"type": "score_change", "label": "Score", "old": "40", "new": "45", "diff": "+5"}]
        md = _build_changelog_section(changes)
        assert "Score" in md
        assert "45" in md
        assert "+5" in md

    def test_indicator_change(self) -> None:
        changes = [{"type": "indicator_change", "label": "VIX", "old": "15", "new": "18", "diff": "+3", "direction": "📈"}]
        md = _build_changelog_section(changes)
        assert "VIX" in md
        assert "📈" in md


class TestBuildIndicatorTable:
    """Tests for indicator table rendering."""

    def test_no_indicators(self) -> None:
        snapshot = MagicMock()
        snapshot.indicators = {}
        md = _build_indicator_table(snapshot)
        assert "Indicator" in md
        assert "Value" in md

    def test_with_indicators(self) -> None:
        snapshot = MagicMock()
        snapshot.indicators = {
            "tickertape_mmi": MagicMock(value=50.0),
            "india_vix": MagicMock(value=15.5),
        }
        md = _build_indicator_table(snapshot)
        assert "Tickertape MMI" in md
        assert "India VIX" in md
        assert "50.0" in md

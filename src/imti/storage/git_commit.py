"""Git commit utility for automated data commits from GitHub Actions.

Commits new data files (CSV, JSON, blog pages) to the repository
so they persist between workflow runs and are available on the website.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from imti.core.logger import get_logger

logger = get_logger("storage.git")


class GitCommitter:
    """Automated git commit utility for CI/CD data persistence.

    Commits data files to the repository after each pipeline run.
    This ensures all historical data is preserved and available
    for backtesting, the website, and API endpoints.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        if repo_root is None:
            from imti.core.paths import get_project_root
            repo_root = get_project_root()
        self.repo_root = Path(repo_root)

    def _run_git(self, *args: str) -> str:
        """Run a git command in the repository root."""
        cmd = ["git", "-C", str(self.repo_root)] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.warning(f"Git command failed: {' '.join(args)} — {result.stderr.strip()}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(args)}")
            return ""
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return ""

    def commit_data(self, message: str, paths: list[Path] | None = None) -> bool:
        """Add and commit data files to the repository.

        Args:
            message: Commit message
            paths: Specific files to add. If None, adds all changes in data/.

        Returns:
            True if commit was created, False if nothing to commit.
        """
        # Configure git user (for GitHub Actions)
        self._run_git("config", "user.name", "IMTI Bot")
        self._run_git("config", "user.email", "imti-bot@users.noreply.github.com")

        if paths:
            for p in paths:
                self._run_git("add", str(p))
        else:
            self._run_git("add", "data/")

        # Check if there are changes to commit
        status = self._run_git("status", "--porcelain", "data/")
        if not status:
            logger.info("No data changes to commit")
            return False

        self._run_git("commit", "-m", message)
        logger.info(f"Committed data: {message}")
        return True

    def push(self) -> bool:
        """Push commits to remote."""
        result = self._run_git("push")
        if result:
            logger.info("Pushed to remote")
            return True
        logger.warning("Push failed")
        return False

    def get_last_commit_message(self) -> str:
        """Get the last commit message."""
        return self._run_git("log", "-1", "--pretty=%B")

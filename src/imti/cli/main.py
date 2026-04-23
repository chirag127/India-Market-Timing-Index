"""CLI entry point for the IMTI system.

Usage:
    imti run          — Run the hourly pipeline
    imti daily        — Run the daily pipeline
    imti fetch        — Fetch data only (no scoring)
    imti score        — Compute score from existing data
    imti status       — Show current score and status
    imti sources      — List registered sources and their health
    imti train        — Retrain the ML model
    imti blog         — Generate daily blog page
    imti deploy       — Deploy website to Cloudflare Pages
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="imti",
        description="India Market Timing Index — AI-powered market timing signal",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run hourly pipeline
    subparsers.add_parser("run", help="Run the hourly pipeline (fetch + score + save)")

    # Run daily pipeline
    subparsers.add_parser("daily", help="Run the daily pipeline (retrain + blog + deploy)")

    # Fetch data only
    subparsers.add_parser("fetch", help="Fetch data from all sources (no scoring)")

    # Compute score
    subparsers.add_parser("score", help="Compute IMTI score from existing data")

    # Show status
    subparsers.add_parser("status", help="Show current IMTI score and status")

    # List sources
    subparsers.add_parser("sources", help="List all registered data sources")

    # Train model
    subparsers.add_parser("train", help="Retrain the XGBoost model")

    # Generate blog
    subparsers.add_parser("blog", help="Generate daily blog page")

    # Deploy website
    subparsers.add_parser("deploy", help="Deploy website to Cloudflare Pages")

    # Stock screener
    subparsers.add_parser("screen", help="Run the stock screener")

    # Hourly blog
    subparsers.add_parser("hourly-blog", help="Generate hourly blog post")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the appropriate handler
    handlers: dict[str, Any] = {
        "run": _cmd_run,
        "daily": _cmd_daily,
        "fetch": _cmd_fetch,
        "score": _cmd_score,
        "status": _cmd_status,
        "sources": _cmd_sources,
        "train": _cmd_train,
        "blog": _cmd_blog,
        "deploy": _cmd_deploy,
        "screen": _cmd_screen,
        "hourly-blog": _cmd_hourly_blog,
    }

    handler = handlers.get(args.command)
    if handler:
        handler()
    else:
        parser.print_help()


def _cmd_run() -> None:
    """Run the hourly pipeline."""
    from imti.pipelines.hourly import run_hourly_pipeline
    result = run_hourly_pipeline()
    _print_result(result)


def _cmd_daily() -> None:
    """Run the daily pipeline."""
    from imti.pipelines.daily import run_daily_pipeline
    result = run_daily_pipeline()
    _print_result(result)


def _cmd_fetch() -> None:
    """Fetch data only."""
    from imti.ingestion.fetch_snapshot import fetch_full_snapshot
    snapshot = fetch_full_snapshot()
    print(f"Fetched {len(snapshot.indicators)} indicators")
    print(f"Run type: {snapshot.run_type.value}")
    print(f"Market status: {snapshot.market_status.value}")


def _cmd_score() -> None:
    """Compute IMTI score from existing data."""
    from imti.pipelines.hourly import run_hourly_pipeline
    result = run_hourly_pipeline()
    _print_result(result)


def _cmd_status() -> None:
    """Show current IMTI score and status."""
    from imti.storage.json_store import JSONStore
    store = JSONStore()
    latest = store.load_latest_snapshot()

    if not latest:
        print("No data available. Run 'imti run' first.")
        return

    indices = latest.get("indices", {})
    nifty = indices.get("nifty_50", {})

    if nifty:
        score = nifty.get("score", "N/A")
        zone = nifty.get("score_zone", "N/A")
        action = nifty.get("signal_action", "N/A")
        print(f"  Score:  {score}")
        print(f"  Zone:   {zone}")
        print(f"  Action: {action}")
    else:
        print("No score computed yet. Run 'imti run' first.")


def _cmd_sources() -> None:
    """List all registered data sources."""
    from imti.sources.registry import SourceRegistry
    from imti.ingestion.fetch_snapshot import _register_all_sources

    registry = SourceRegistry()
    _register_all_sources(registry)

    print(f"Registered sources: {registry.source_count}")
    for name in registry.source_names:
        source = registry.get_source(name)
        if source:
            print(f"  {name:25s} priority={source.priority:3d}  provides={len(source.provides)} indicators")


def _cmd_train() -> None:
    """Retrain the ML model."""
    from imti.models.train import retrain_model
    result = retrain_model()
    _print_result(result)


def _cmd_blog() -> None:
    """Generate daily blog page."""
    from datetime import date
    from imti.outputs.blog_generator import generate_daily_blog
    result = generate_daily_blog(date.today())
    _print_result(result)


def _cmd_deploy() -> None:
    """Deploy website to Cloudflare Pages."""
    from imti.outputs.deploy import deploy_to_cloudflare
    result = deploy_to_cloudflare()
    _print_result(result)


def _cmd_screen() -> None:
    """Run the stock screener."""
    from imti.sources.screener import StockScreener
    result = StockScreener().run_screen()
    _print_result(result)


def _cmd_hourly_blog() -> None:
    """Generate hourly blog post."""
    from imti.outputs.blog_generator import generate_hourly_blog
    from imti.storage.json_store import JSONStore
    store = JSONStore()
    latest = store.load_latest_snapshot() or {}
    score = latest.get("score", 50.0)
    confidence = latest.get("confidence", 0.5)
    result = generate_hourly_blog(score, confidence, None)
    _print_result(result)


def _print_result(result: dict[str, Any]) -> None:
    """Print a pipeline result as formatted JSON."""
    # Remove large/verbose fields for readability
    display = {k: v for k, v in result.items() if k not in ("audit", "feature_selection")}
    print(json.dumps(display, indent=2, default=str))


# Entry point alias
app = main


if __name__ == "__main__":
    main()

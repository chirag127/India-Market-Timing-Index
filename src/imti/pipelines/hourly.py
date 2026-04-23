"""Hourly pipeline — the main execution loop.

Runs every hour (via GitHub Actions cron) to:
1. Fetch all data from all sources
2. Compute indicators and normalize
3. Run ML inference (if model exists)
4. Generate score
5. Save data (CSV, JSON)
6. Update README
7. Send email digest
8. Commit data to repo
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from imti.config.settings import get_settings
from imti.core.enums import IndexName, ScoreZone
from imti.core.logger import get_logger
from imti.core.types import IndexScore, Snapshot
from imti.ingestion.fetch_snapshot import fetch_full_snapshot
from imti.ingestion.source_audit import SourceAudit
from imti.indicators.feature_store import FeatureStore
from imti.storage.csv_store import CSVStore
from imti.storage.json_store import JSONStore

logger = get_logger("pipeline.hourly")


def run_hourly_pipeline() -> dict[str, Any]:
    """Execute the hourly pipeline.

    Returns:
        Summary dict with score, indicators, and status info.
    """
    start_time = datetime.now()
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("HOURLY PIPELINE START")
    logger.info("=" * 60)

    # Step 1: Fetch all data
    logger.info("Step 1: Fetching data from all sources...")
    try:
        snapshot = fetch_full_snapshot()
    except Exception as e:
        logger.error(f"Data fetch failed: {e}")
        return {"status": "error", "error": str(e), "stage": "fetch"}

    # Step 2: Compute feature vector
    logger.info("Step 2: Computing feature vector...")
    feature_store = FeatureStore()
    feature_store.load_history()
    feature_store.add_snapshot(snapshot)
    features = feature_store.compute_feature_vector(snapshot)
    missing = feature_store.get_missing_indicators(snapshot)

    logger.info(f"Features computed: {len(features)}, Missing indicators: {len(missing)}")
    if missing:
        logger.warning(f"Missing indicators: {missing[:10]}{'...' if len(missing) > 10 else ''}")

    # Step 3: Run ML inference (if model exists)
    logger.info("Step 3: Running ML inference...")
    nifty_score: float = 50.0  # Default to neutral
    confidence: float = 0.5

    try:
        from imti.models.inference import predict_score
        nifty_score, confidence = predict_score(features)
        logger.info(f"Model prediction: score={nifty_score:.1f}, confidence={confidence:.2f}")
    except Exception as e:
        logger.warning(f"ML inference failed (using fallback): {e}")
        # Fallback: simple weighted average of key indicators
        nifty_score = _fallback_score(snapshot)
        confidence = 0.3
        logger.info(f"Fallback score: {nifty_score:.1f}")

    # Step 4: Build IndexScore
    nifty_index_score = IndexScore.from_raw_score(
        index_name=IndexName.NIFTY_50,
        score=nifty_score,
        confidence=confidence,
        timestamp=snapshot.timestamp,
    )
    snapshot.indices[IndexName.NIFTY_50.value] = nifty_index_score

    # Step 5: Save data
    logger.info("Step 5: Saving data...")
    csv_store = CSVStore()
    json_store = JSONStore()

    csv_path = csv_store.save_snapshot(snapshot)
    json_path = json_store.save_snapshot(snapshot)
    feature_store.save_history()

    # Step 6: Source audit
    logger.info("Step 6: Running source audit...")
    audit = SourceAudit()
    audit_report = audit.audit_snapshot(snapshot)

    # Step 7: Save API response for website
    logger.info("Step 7: Saving API responses...")
    api_data = {
        "score": nifty_score,
        "confidence": confidence,
        "zone": nifty_index_score.score_zone.value,
        "action": nifty_index_score.signal_action.value,
        "exposure": nifty_index_score.exposure_suggestion,
        "color": nifty_index_score.score_zone.color,
        "emoji": nifty_index_score.score_zone.emoji,
        "timestamp": snapshot.timestamp.isoformat(),
        "top_drivers": nifty_index_score.top_drivers,
        "indicators": {k: v.value for k, v in snapshot.indicators.items() if v.value is not None},
        "market_status": snapshot.market_status.value,
        "source_health": audit_report,
    }
    json_store.save_api_response("current", api_data)

    # Step 8: Send email (if enabled)
    if settings.enable_email and settings.email_is_configured:
        logger.info("Step 8: Sending email digest...")
        try:
            from imti.outputs.email_digest import send_hourly_digest
            send_hourly_digest(nifty_index_score, snapshot, audit_report)
        except Exception as e:
            logger.warning(f"Email send failed: {e}")
    else:
        logger.info("Step 8: Email disabled or not configured")

    # Step 9: Update README
    logger.info("Step 9: Updating README...")
    try:
        from imti.outputs.readme_updater import update_readme
        update_readme(nifty_index_score, snapshot)
    except Exception as e:
        logger.warning(f"README update failed: {e}")

    # Step 10: Commit data
    logger.info("Step 10: Committing data to repo...")
    try:
        from imti.storage.git_commit import GitCommitter
        committer = GitCommitter()
        date_str = snapshot.timestamp.strftime("%Y-%m-%d")
        time_str = snapshot.timestamp.strftime("%H:%M")
        committer.commit_data(
            message=f"📊 IMTI hourly update: {date_str} {time_str} — Score: {nifty_score:.1f} ({nifty_index_score.score_zone.value})",
            paths=[csv_path, json_path, feature_store.data_dir / "indicator_history.csv"],
        )
    except Exception as e:
        logger.warning(f"Git commit failed: {e}")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"HOURLY PIPELINE COMPLETE in {elapsed:.1f}s")
    logger.info(f"Score: {nifty_score:.1f} ({nifty_index_score.score_zone.value})")
    logger.info(f"Indicators: {len(snapshot.indicators)}, Confidence: {confidence:.2f}")
    logger.info("=" * 60)

    return {
        "status": "success",
        "score": nifty_score,
        "zone": nifty_index_score.score_zone.value,
        "action": nifty_index_score.signal_action.value,
        "confidence": confidence,
        "indicators_available": len(snapshot.indicators),
        "indicators_missing": len(missing),
        "elapsed_seconds": elapsed,
        "audit": audit_report,
    }


def _fallback_score(snapshot: Snapshot) -> float:
    """Compute a simple fallback score from key indicators.

    Uses weighted average of normalized indicator values when
    the ML model is unavailable.

    In the inverted system:
    - Direct indicators (MMI, RSI, PE, LLM danger): high value = high danger
    - Contrarian indicators (VIX, PCR, FII selling): high value = fear = BUY opportunity
      → We invert them so high VIX maps to LOW score (buy opportunity)
    """
    # Weights for the inverted system: higher value = more danger
    weights: dict[str, float] = {
        "tickertape_mmi": 0.25,       # MMI directly maps to danger
        "india_vix": 0.15,            # High VIX = fear → contrarian buy → invert
        "llm_danger_score": 0.20,     # LLM danger directly maps
        "put_call_ratio": 0.10,       # High PCR = fear → contrarian buy → invert
        "advance_decline_ratio": 0.05, # High A/D = strength → danger
        "rsi_14": 0.10,               # RSI directly maps (high=overbought=danger)
        "nifty_pe": 0.10,             # High PE = overvalued = danger
        "fii_cash_net": 0.05,         # FII buying = euphoria → danger (direct mapping)
    }

    # Contrarian indicators: high value means fear, which maps to LOW score (buy)
    # Note: FII cash_net is NOT contrarian — high FII buying = euphoria = danger (direct),
    # low FII selling = fear = buy opportunity (direct). The normalized value already
    # maps correctly without inversion.
    contrarian = {"india_vix", "put_call_ratio"}

    weighted_sum = 0.0
    total_weight = 0.0

    for name, weight in weights.items():
        if name in snapshot.indicators:
            iv = snapshot.indicators[name]
            if iv.value is not None:
                normalized = _quick_normalize(name, iv.value)
                # Contrarian: invert so high fear → low score (buy opportunity)
                if name in contrarian:
                    normalized = 100.0 - normalized
                weighted_sum += normalized * weight
                total_weight += weight

    # Weighted average of normalized values (0-100)
    if total_weight == 0:
        return 50.0  # No data → neutral

    score = weighted_sum / total_weight
    return max(0.0, min(100.0, score))


def _quick_normalize(name: str, value: float) -> float:
    """Quick normalization of indicator value to 0-100 range."""
    from imti.config.thresholds import INDICATOR_RANGES

    if name in INDICATOR_RANGES:
        low, high = INDICATOR_RANGES[name]
        if high > low:
            return max(0.0, min(100.0, (value - low) / (high - low) * 100))

    # Default: assume value is already roughly 0-100
    return max(0.0, min(100.0, value))

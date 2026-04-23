"""Daily pipeline — model retraining, blog generation, and daily tasks.

Runs once per day (via GitHub Actions cron at 00:30 IST) to:
1. Retrain the XGBoost model with all accumulated data
2. Generate the daily blog page
3. Run feature selection experiments
4. Produce daily audit report
5. Deploy website to Cloudflare Pages
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any

from imti.config.settings import get_settings
from imti.core.logger import get_logger
from imti.core.types import DailyBlogData

logger = get_logger("pipeline.daily")


def run_daily_pipeline() -> dict[str, Any]:
    """Execute the daily pipeline.

    Returns:
        Summary dict with training results and blog generation status.
    """
    start_time = datetime.now()
    settings = get_settings()
    today = date.today()

    logger.info("=" * 60)
    logger.info("DAILY PIPELINE START")
    logger.info(f"Date: {today.isoformat()}")
    logger.info("=" * 60)

    results: dict[str, Any] = {"date": today.isoformat()}

    # Step 1: Retrain model
    logger.info("Step 1: Retraining XGBoost model...")
    try:
        from imti.models.train import retrain_model
        train_result = retrain_model()
        results["training"] = train_result
        logger.info(f"Model retrained: {train_result.get('status', 'unknown')}")
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        results["training"] = {"status": "error", "error": str(e)}

    # Step 2: Feature selection
    logger.info("Step 2: Running feature selection...")
    try:
        from imti.experiments.feature_selection import run_feature_selection
        fs_result = run_feature_selection()
        results["feature_selection"] = fs_result
        logger.info(f"Feature selection: top features = {fs_result.get('top_features', [])[:5]}")
    except Exception as e:
        logger.warning(f"Feature selection failed: {e}")
        results["feature_selection"] = {"status": "skipped", "error": str(e)}

    # Step 3: Generate daily blog page
    if settings.enable_blog_generation:
        logger.info("Step 3: Generating daily blog page...")
        try:
            from imti.outputs.blog_generator import generate_daily_blog
            blog_result = generate_daily_blog(today)
            results["blog"] = blog_result
            logger.info(f"Blog generated: {blog_result.get('path', 'unknown')}")
        except Exception as e:
            logger.warning(f"Blog generation failed: {e}")
            results["blog"] = {"status": "error", "error": str(e)}
    else:
        logger.info("Step 3: Blog generation disabled")

    # Step 4: Source health daily summary
    logger.info("Step 4: Generating source health daily summary...")
    try:
        from imti.ingestion.source_audit import SourceAudit
        audit = SourceAudit()
        daily_summary = audit.get_daily_summary(today)
        results["source_audit"] = daily_summary
    except Exception as e:
        logger.warning(f"Source audit summary failed: {e}")

    # Step 5: Deploy website
    if settings.enable_deploy:
        logger.info("Step 5: Deploying website to Cloudflare Pages...")
        try:
            from imti.outputs.deploy import deploy_to_cloudflare
            deploy_result = deploy_to_cloudflare()
            results["deploy"] = deploy_result
        except Exception as e:
            logger.warning(f"Deployment failed: {e}")
            results["deploy"] = {"status": "error", "error": str(e)}
    else:
        logger.info("Step 5: Deployment disabled")

    # Step 6: Commit and push
    logger.info("Step 6: Committing and pushing daily data...")
    try:
        from imti.storage.git_commit import GitCommitter
        committer = GitCommitter()
        committed = committer.commit_data(
            message=f"📦 IMTI daily update: {today.isoformat()} — retrain + blog + deploy"
        )
        if committed:
            committer.push()
        results["committed"] = committed
    except Exception as e:
        logger.warning(f"Git commit/push failed: {e}")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"DAILY PIPELINE COMPLETE in {elapsed:.1f}s")
    logger.info("=" * 60)

    results["elapsed_seconds"] = elapsed
    results["status"] = "success"

    return results

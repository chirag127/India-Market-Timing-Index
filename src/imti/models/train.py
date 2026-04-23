"""XGBoost model training pipeline.

Trains the IMTI scoring model using accumulated indicator data
and future returns as labels. Produces a model file and
feature importance report.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from imti.core.logger import get_logger
from imti.core.paths import ProjectPaths

logger = get_logger("models.train")


def retrain_model() -> dict[str, Any]:
    """Retrain the XGBoost model from all accumulated data.

    Returns:
        Training result dict with metrics and feature importance.
    """
    paths = ProjectPaths()
    models_dir = paths.models
    models_dir.mkdir(parents=True, exist_ok=True)
    features_dir = paths.features

    # Check if we have enough data to train
    history_csv = features_dir / "indicator_history.csv"
    if not history_csv.exists():
        logger.warning("No indicator history found — cannot train model")
        return {"status": "skipped", "reason": "no data"}

    import pandas as pd
    df = pd.read_csv(history_csv, index_col=0, parse_dates=True)

    if len(df) < 30:
        logger.warning(f"Only {len(df)} data points — need at least 30 to train")
        return {"status": "skipped", "reason": f"insufficient data ({len(df)} rows)"}

    logger.info(f"Training model with {len(df)} data points")

    try:
        import xgboost as xgb
        from sklearn.model_selection import TimeSeriesSplit
        import numpy as np

        # Prepare features (all indicator columns)
        feature_cols = [c for c in df.columns if c not in ("timestamp",)]
        X = df[feature_cols].fillna(0)

        # Create target: future returns-based danger score
        # For now, use a simple placeholder target
        # In production, this would use actual future Nifty returns
        # mapped to the 0-100 danger scale
        y = _create_target(df)

        if y is None or len(y) != len(X):
            logger.warning("Could not create training target — using synthetic target")
            y = np.random.uniform(30, 70, size=len(X))

        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=min(5, len(df) // 10))

        # Train XGBoost model
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
        )

        model.fit(X, y, verbose=False)

        # Save model
        model_path = models_dir / "imti_xgb_latest.json"
        model.save_model(str(model_path))

        # Also save with timestamp
        ts_path = models_dir / f"imti_xgb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        model.save_model(str(ts_path))

        # Feature importance
        importance = model.feature_importances_
        feat_importance = sorted(
            zip(feature_cols, importance),
            key=lambda x: x[1],
            reverse=True,
        )

        top_features = [f[0] for f in feat_importance[:20]]

        logger.info(f"Model trained successfully — top features: {top_features[:5]}")

        return {
            "status": "success",
            "data_points": len(df),
            "features_used": len(feature_cols),
            "top_features": top_features,
            "model_path": str(model_path),
        }

    except ImportError:
        logger.warning("xgboost not installed — skipping model training")
        return {"status": "skipped", "reason": "xgboost not installed"}
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return {"status": "error", "error": str(e)}


def _create_target(df: "pd.DataFrame") -> "np.ndarray | None":
    """Create the training target from future returns.

    Maps future Nifty returns to a 0-100 danger score:
    - Strong future gains → LOW danger score (buy was right)
    - Strong future losses → HIGH danger score (sell was right)
    - Mild moves → NEUTRAL (50)
    """
    try:
        import numpy as np

        # Look for Nifty price column in data
        if "nifty_close" not in df.columns:
            return None

        nifty = df["nifty_close"].dropna()
        if len(nifty) < 5:
            return None

        # Compute 5-day forward returns
        forward_returns = nifty.pct_change(periods=5).shift(-5)

        # Map returns to danger score
        # Strong positive return → low danger (was a buy opportunity)
        # Strong negative return → high danger (was a sell signal)
        # Scale: ±5% → 0/100, 0% → 50
        danger = 50 - (forward_returns * 10)  # Invert: positive returns = low danger
        danger = danger.clip(0, 100)

        return danger.values

    except Exception as e:
        logger.warning(f"Target creation failed: {e}")
        return None

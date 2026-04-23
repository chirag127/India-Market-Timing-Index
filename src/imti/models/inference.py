"""Model inference — loads trained model and predicts IMTI score.

If no trained model exists, falls back to the weighted-average
fallback scoring method.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imti.core.logger import get_logger
from imti.core.paths import ProjectPaths

logger = get_logger("models.inference")


def predict_score(features: dict[str, float]) -> tuple[float, float]:
    """Predict the IMTI danger score from a feature vector.

    Args:
        features: Dict of {feature_name: value}

    Returns:
        (score_0_100, confidence_0_1)
    """
    paths = ProjectPaths()
    model_path = paths.models / "imti_xgb_latest.json"

    if not model_path.exists():
        logger.warning("No trained model found — returning neutral score")
        return 50.0, 0.2

    try:
        import xgboost as xgb
        import numpy as np

        model = xgb.XGBRegressor()
        model.load_model(str(model_path))

        # Prepare feature vector in the same order as training
        # Use model's feature names if available
        feature_names = model.get_booster().feature_names
        if feature_names:
            X = np.array([[features.get(name, 0.0) for name in feature_names]])
        else:
            # Fallback: use all features in sorted order
            sorted_features = sorted(features.keys())
            X = np.array([[features.get(name, 0.0) for name in sorted_features]])

        prediction = float(model.predict(X)[0])

        # Clamp to 0-100
        score = max(0.0, min(100.0, prediction))

        # Estimate confidence based on feature completeness
        available = sum(1 for v in features.values() if v != 0.0)
        total = len(features)
        confidence = min(1.0, available / max(total, 1) * 1.5)

        logger.info(f"Model prediction: score={score:.1f}, confidence={confidence:.2f}")

        return score, confidence

    except ImportError:
        logger.warning("xgboost not installed — returning neutral score")
        return 50.0, 0.2
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        return 50.0, 0.2

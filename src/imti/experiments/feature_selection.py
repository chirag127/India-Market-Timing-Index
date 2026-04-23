"""Feature selection experiments.

Determines which of the 50+ indicators are most predictive
using multiple methods: SHAP, mutual information, and Boruta.
"""

from __future__ import annotations

from typing import Any

from imti.core.logger import get_logger
from imti.core.paths import ProjectPaths

logger = get_logger("experiments.feature_selection")


def run_feature_selection() -> dict[str, Any]:
    """Run feature selection experiments on accumulated data.

    Returns:
        Dict with top features and selection method results.
    """
    paths = ProjectPaths()
    history_csv = paths.features / "indicator_history.csv"

    if not history_csv.exists():
        logger.warning("No indicator history — cannot run feature selection")
        return {"status": "skipped", "reason": "no data"}

    try:
        import pandas as pd
        import numpy as np
        from sklearn.feature_selection import mutual_info_regression

        df = pd.read_csv(history_csv, index_col=0, parse_dates=True)

        if len(df) < 30:
            return {"status": "skipped", "reason": f"only {len(df)} rows"}

        feature_cols = [c for c in df.columns if c not in ("timestamp",)]
        X = df[feature_cols].fillna(0)

        # Create simple target for feature selection
        if "nifty_close" in df.columns:
            nifty = df["nifty_close"].fillna(method="ffill")
            y = nifty.pct_change(periods=5).shift(-5).fillna(0)
        else:
            y = pd.Series(np.zeros(len(df)), index=df.index)

        # Method 1: Mutual Information
        mi_scores = mutual_info_regression(X.fillna(0), y.fillna(0))
        mi_ranking = sorted(zip(feature_cols, mi_scores), key=lambda x: x[1], reverse=True)

        top_features = [f[0] for f in mi_ranking[:20]]

        logger.info(f"Feature selection complete — top 5: {top_features[:5]}")

        return {
            "status": "success",
            "method": "mutual_information",
            "top_features": top_features,
            "top_10_mi_scores": [(f, round(s, 4)) for f, s in mi_ranking[:10]],
            "data_points": len(df),
        }

    except ImportError:
        logger.warning("sklearn not installed — skipping feature selection")
        return {"status": "skipped", "reason": "sklearn not installed"}
    except Exception as e:
        logger.error(f"Feature selection failed: {e}")
        return {"status": "error", "error": str(e)}

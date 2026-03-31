"""
Lead scoring inference.
Loads the latest registered model from MLflow and scores leads by conversion probability.

Usage:
    from models.lead_scoring.predict import score_leads
    df = score_leads(lead_ids=["LEAD0001", "LEAD0002"])
"""

import os
import mlflow.xgboost
import pandas as pd
from dotenv import load_dotenv

from models.lead_scoring.features import FEATURE_COLS, load_features

load_dotenv()

MODEL_URI = "models:/lead_scoring_model/latest"


def _load_model():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    return mlflow.xgboost.load_model(MODEL_URI)


def score_leads(lead_ids: list | None = None) -> pd.DataFrame:
    """
    Score leads by conversion probability.

    Args:
        lead_ids: Optional list of lead_ids to score. If None, scores all leads.

    Returns:
        DataFrame with columns: lead_id, score, rank (1 = highest priority)
    """
    X, _, _ = load_features()

    # Re-attach lead_id for filtering and output
    from db.queries import get_lead_features
    full_df = get_lead_features()
    full_df = full_df[["lead_id"] + FEATURE_COLS].copy()

    if lead_ids is not None:
        full_df = full_df[full_df["lead_id"].isin(lead_ids)].reset_index(drop=True)
        if full_df.empty:
            raise ValueError(f"No matching leads found for provided lead_ids.")

    model = _load_model()
    scores = model.predict_proba(full_df[FEATURE_COLS])[:, 1]

    result = pd.DataFrame({
        "lead_id": full_df["lead_id"],
        "score":   scores.round(4),
    })
    result["rank"] = result["score"].rank(ascending=False, method="first").astype(int)
    result = result.sort_values("rank").reset_index(drop=True)

    return result


if __name__ == "__main__":
    df = score_leads()
    print(f"Scored {len(df)} leads")
    print(f"\nTop 10 leads by conversion probability:")
    print(df.head(10).to_string(index=False))
    print(f"\nScore distribution:")
    print(df["score"].describe().round(4).to_string())

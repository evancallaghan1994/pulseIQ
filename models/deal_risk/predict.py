"""
Deal risk inference.
Loads the latest registered model from MLflow and scores active deals by risk probability.

Usage:
    from models.deal_risk.predict import score_deals
    df = score_deals(deal_ids=["DEAL0001", "DEAL0002"])
"""

import os
import mlflow.xgboost
import pandas as pd
from dotenv import load_dotenv

from models.deal_risk.features import FEATURE_COLS, load_features

load_dotenv()

MODEL_URI = "models:/deal_risk_model/latest"


def _load_model():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    return mlflow.xgboost.load_model(MODEL_URI)


def score_deals(deal_ids: list | None = None) -> pd.DataFrame:
    """
    Score deals by risk probability.

    Args:
        deal_ids: Optional list of deal_ids to score. If None, scores all closed deals.

    Returns:
        DataFrame with columns: deal_id, risk_score, risk_rank (1 = highest risk)
    """
    # Re-attach deal_id for filtering and output
    from db.queries import get_deal_features
    full_df = get_deal_features()
    full_df = full_df[["deal_id"] + FEATURE_COLS].copy()

    if deal_ids is not None:
        full_df = full_df[full_df["deal_id"].isin(deal_ids)].reset_index(drop=True)
        if full_df.empty:
            raise ValueError("No matching deals found for provided deal_ids.")

    model = _load_model()
    scores = model.predict_proba(full_df[FEATURE_COLS])[:, 1]

    result = pd.DataFrame({
        "deal_id":    full_df["deal_id"],
        "risk_score": scores.round(4),
    })
    result["risk_rank"] = result["risk_score"].rank(ascending=False, method="first").astype(int)
    result = result.sort_values("risk_rank").reset_index(drop=True)

    return result


if __name__ == "__main__":
    df = score_deals()
    print(f"Scored {len(df)} deals")
    print(f"\nTop 10 deals by risk probability:")
    print(df.head(10).to_string(index=False))
    print(f"\nRisk score distribution:")
    print(df["risk_score"].describe().round(4).to_string())

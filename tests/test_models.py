"""
Tests for ML model inference.
Requires a running PostgreSQL DB with loaded data and trained models in MLflow.
No network calls.
"""

import pytest
from models.lead_scoring.predict import score_leads
from models.deal_risk.predict import score_deals


def test_lead_scoring_returns_scores():
    """score_leads() with 10 IDs must return scores in [0, 1] for all rows."""
    lead_ids = [f"LEAD{i:04d}" for i in range(1, 11)]
    df = score_leads(lead_ids=lead_ids)

    assert set(df.columns) >= {"lead_id", "score", "rank"}
    assert len(df) == 10
    assert (df["score"] >= 0).all() and (df["score"] <= 1).all(), \
        f"Scores out of [0,1] range: {df['score'].describe()}"


def test_deal_risk_returns_flags():
    """score_deals() with 10 IDs must return valid risk_scores and integer ranks."""
    # Use IDs from deal_features (closed deals only) to guarantee matches
    from db.queries import get_deal_features
    deal_ids = get_deal_features()["deal_id"].head(10).tolist()
    df = score_deals(deal_ids=deal_ids)

    assert set(df.columns) >= {"deal_id", "risk_score", "risk_rank"}
    assert len(df) == 10
    assert (df["risk_score"] >= 0).all() and (df["risk_score"] <= 1).all(), \
        f"Risk scores out of [0,1] range: {df['risk_score'].describe()}"
    assert df["risk_rank"].dtype in ["int32", "int64"], \
        f"risk_rank should be integer, got {df['risk_rank'].dtype}"

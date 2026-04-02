"""
Feature preparation for the deal risk detection model.
Loads from the deal_features table (pre-engineered by pipeline/transform.py).
Returns X, y, and the feature column list for use at training and inference time.
"""

import pandas as pd
from db.queries import get_deal_features

# days_since_last_contact is the primary signal — deals going dark are the key risk indicator
FEATURE_COLS = [
    "days_since_last_contact",
    "deal_age_days",
    "engagement_count",
    "meeting_count",
    "email_reply_rate",
    "deal_value",
]
TARGET_COL = "is_at_risk"


def load_features() -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Returns:
        X: feature DataFrame
        y: binary target Series (1 = at risk / closed_lost, 0 = closed_won)
        feature_cols: ordered list of feature column names
    """
    df = get_deal_features()

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected feature columns: {missing}")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].astype(int)

    assert X.isnull().sum().sum() == 0, "Nulls found in deal feature columns"
    assert y.isin([0, 1]).all(), "Target must be binary"

    return X, y, FEATURE_COLS

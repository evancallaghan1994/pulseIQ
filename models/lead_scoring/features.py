"""
Feature preparation for the lead scoring model.
Loads from the lead_features table (pre-encoded by pipeline/transform.py).
Returns X, y, and the feature column list for use at training and inference time.
"""

import pandas as pd
from db.queries import get_lead_features

FEATURE_COLS = [
    "source_encoded",
    "company_size_encoded",
    "industry_encoded",
    "lead_month",
]
TARGET_COL = "converted"


def load_features() -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Returns:
        X: feature DataFrame
        y: binary target Series (1 = converted, 0 = not converted)
        feature_cols: ordered list of feature column names
    """
    df = get_lead_features()

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected feature columns: {missing}")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].astype(int)

    assert X.isnull().sum().sum() == 0, "Nulls found in lead feature columns"
    assert y.isin([0, 1]).all(), "Target must be binary"

    return X, y, FEATURE_COLS

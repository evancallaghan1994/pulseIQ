"""
Tests for pipeline validation and loading.
test_load_leads_row_count hits the real DB (uses the already-loaded data).
test_validate_deals_catches_bad_dates runs entirely in memory.
"""

import datetime
import pandas as pd
import pytest

from pipeline.validate import validate_deals


def _minimal_leads_df(n: int = 3) -> pd.DataFrame:
    """Minimal leads DataFrame with required columns for validate_deals."""
    return pd.DataFrame({
        "lead_id": [f"LEAD{i:04d}" for i in range(1, n + 1)],
    })


def _minimal_deals_df(leads_df: pd.DataFrame) -> pd.DataFrame:
    """Valid deals DataFrame — all dates consistent."""
    today = datetime.date.today()
    return pd.DataFrame({
        "deal_id":           [f"DEAL{i:04d}" for i in range(1, len(leads_df) + 1)],
        "lead_id":           leads_df["lead_id"].tolist(),
        "created_at":        [today - datetime.timedelta(days=30)] * len(leads_df),
        "last_contact_date": [today - datetime.timedelta(days=5)]  * len(leads_df),
        "close_date":        [None] * len(leads_df),
        "stage":             ["discovery"] * len(leads_df),
        "outcome":           ["open"] * len(leads_df),
    })


def test_validate_deals_catches_bad_dates():
    """Validator must flag rows where last_contact_date < created_at."""
    leads_df = _minimal_leads_df(3)
    deals_df = _minimal_deals_df(leads_df)

    # Inject one bad row: last_contact_date set before created_at
    deals_df.loc[0, "last_contact_date"] = (
        pd.to_datetime(deals_df.loc[0, "created_at"]) - datetime.timedelta(days=1)
    ).date()

    issues = validate_deals(deals_df, leads_df)
    assert any("last_contact_date < created_at" in issue for issue in issues), (
        f"Expected date order issue not caught. Issues: {issues}"
    )


def test_load_leads_row_count():
    """Lead count in the DB must match the CSV on disk."""
    import pandas as pd
    from db.connection import get_engine

    csv_df = pd.read_csv("data/raw/leads.csv")
    db_df  = pd.read_sql("SELECT COUNT(*) AS n FROM leads", get_engine())
    assert len(csv_df) == db_df["n"].iloc[0], (
        f"CSV has {len(csv_df)} rows but DB has {db_df['n'].iloc[0]}"
    )

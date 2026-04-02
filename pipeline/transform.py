"""
Feature engineering for ML models.
Reads from PostgreSQL and writes feature tables back to PostgreSQL.

- lead_features: used by the lead scoring model
- deal_features:  used by the deal risk model

Usage (from project root):
    python -m pipeline.transform
"""

import pandas as pd
from sqlalchemy import text
from db.connection import get_engine


def build_lead_features(engine) -> pd.DataFrame:
    query = """
        SELECT
            l.lead_id,
            l.source,
            l.company_size,
            l.industry,
            l.converted::int AS converted,
            EXTRACT(MONTH FROM l.created_at)::int AS lead_month
        FROM leads l
    """
    df = pd.read_sql(query, engine)

    # Encode categoricals as integer codes
    df["source_encoded"]       = df["source"].astype("category").cat.codes
    df["company_size_encoded"] = df["company_size"].astype("category").cat.codes
    df["industry_encoded"]     = df["industry"].astype("category").cat.codes

    # Drop raw string columns — model uses encoded versions only
    df = df.drop(columns=["source", "company_size", "industry"])

    assert df.isnull().sum().sum() == 0, "Nulls in lead_features"
    return df


def build_deal_features(engine) -> pd.DataFrame:
    query = """
        SELECT
            d.deal_id,
            d.outcome,
            d.value                                         AS deal_value,
            d.last_contact_date - d.created_at             AS deal_age_days,
            d.close_date - d.last_contact_date              AS days_since_last_contact,
            COUNT(e.event_id)                               AS engagement_count,
            SUM(CASE WHEN e.event_type = 'meeting'
                     THEN 1 ELSE 0 END)                    AS meeting_count,
            SUM(CASE WHEN e.event_type = 'email_reply'
                     THEN 1 ELSE 0 END)::float /
                NULLIF(SUM(CASE WHEN e.event_type = 'email_sent'
                     THEN 1 ELSE 0 END), 0)                AS email_reply_rate
        FROM deals d
        LEFT JOIN engagement e ON e.deal_id = d.deal_id
        WHERE d.outcome != 'open'
        GROUP BY d.deal_id, d.outcome, d.value,
                 d.last_contact_date, d.created_at
    """
    df = pd.read_sql(query, engine)

    # Convert interval columns to integer days
    for col in ["deal_age_days", "days_since_last_contact"]:
        df[col] = pd.to_numeric(df[col].apply(
            lambda x: x.days if hasattr(x, "days") else int(x)
        ))

    # Fill null email_reply_rate (deals with no emails sent) with 0
    df["email_reply_rate"] = df["email_reply_rate"].fillna(0.0)

    # Binary target: closed_lost = at risk (1), closed_won = not at risk (0)
    df["is_at_risk"] = (df["outcome"] == "closed_lost").astype(int)
    df = df.drop(columns=["outcome"])

    assert df.isnull().sum().sum() == 0, "Nulls in deal_features"
    return df


def run() -> None:
    engine = get_engine()

    print("Building lead_features...")
    lead_df = build_lead_features(engine)
    lead_df.to_sql("lead_features", con=engine, if_exists="replace", index=False)
    print(f"  lead_features — {len(lead_df)} rows, {lead_df.columns.tolist()}")

    print("Building deal_features...")
    deal_df = build_deal_features(engine)
    deal_df.to_sql("deal_features", con=engine, if_exists="replace", index=False)
    print(f"  deal_features — {len(deal_df)} rows, {deal_df.columns.tolist()}")

    print("\nFeature tables written to PostgreSQL.")


if __name__ == "__main__":
    run()

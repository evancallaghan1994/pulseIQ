"""
Reusable query helpers. Single source of truth for all data retrieval
used by models, the insight agent, and the dashboard.
"""

import pandas as pd
from db.connection import get_engine


def get_lead_features() -> pd.DataFrame:
    """Feature table for lead scoring model training and inference."""
    query = "SELECT * FROM lead_features"
    return pd.read_sql(query, get_engine())


def get_deal_features() -> pd.DataFrame:
    """Feature table for deal risk model training and inference."""
    query = "SELECT * FROM deal_features"
    return pd.read_sql(query, get_engine())


def get_active_deals() -> pd.DataFrame:
    """Open deals with rep name and engagement summary — used by deal risk dashboard."""
    query = """
        SELECT
            d.deal_id,
            d.rep_id,
            r.name                                          AS rep_name,
            d.product,
            d.stage,
            d.value,
            d.created_at,
            d.last_contact_date,
            CURRENT_DATE - d.last_contact_date             AS days_since_last_contact,
            COUNT(e.event_id)                               AS engagement_count,
            SUM(CASE WHEN e.event_type = 'meeting' THEN 1 ELSE 0 END) AS meeting_count
        FROM deals d
        JOIN reps r ON d.rep_id = r.rep_id
        LEFT JOIN engagement e ON e.deal_id = d.deal_id
        WHERE d.outcome = 'open'
        GROUP BY d.deal_id, d.rep_id, r.name, d.product, d.stage,
                 d.value, d.created_at, d.last_contact_date
        ORDER BY d.last_contact_date ASC
    """
    df = pd.read_sql(query, get_engine())
    df["days_since_last_contact"] = df["days_since_last_contact"].apply(
        lambda x: x.days if hasattr(x, "days") else int(x)
    )
    return df


def get_mrr_timeseries() -> pd.DataFrame:
    """Monthly MRR aggregated from active customers — used by insights dashboard."""
    query = """
        SELECT
            DATE_TRUNC('month', gs.month)::date             AS month,
            COALESCE(SUM(c.mrr), 0)                         AS mrr
        FROM generate_series(
            (SELECT MIN(start_date) FROM customers),
            (SELECT GREATEST(MAX(start_date), MAX(churn_date)) FROM customers),
            INTERVAL '1 month'
        ) AS gs(month)
        LEFT JOIN customers c
            ON c.start_date <= gs.month
            AND (c.churn_date IS NULL OR c.churn_date > gs.month)
        GROUP BY gs.month
        ORDER BY gs.month
    """
    return pd.read_sql(query, get_engine())


def get_churn_rate_by_tier() -> pd.DataFrame:
    """Churn rate grouped by subscription tier — used by insights dashboard."""
    query = """
        SELECT
            subscription_tier,
            COUNT(*)                                        AS total_customers,
            SUM(CASE WHEN churn_date IS NOT NULL THEN 1 ELSE 0 END) AS churned,
            ROUND(
                SUM(CASE WHEN churn_date IS NOT NULL THEN 1 ELSE 0 END)::numeric
                / COUNT(*) * 100, 1
            )                                               AS churn_rate_pct
        FROM customers
        GROUP BY subscription_tier
        ORDER BY churn_rate_pct DESC
    """
    return pd.read_sql(query, get_engine())


def get_pipeline_summary() -> pd.DataFrame:
    """Deal count and total value by stage — used by lead scoring dashboard."""
    query = """
        SELECT
            stage,
            COUNT(*)                                        AS deal_count,
            SUM(value)                                      AS total_value,
            ROUND(AVG(value))                               AS avg_value
        FROM deals
        GROUP BY stage
        ORDER BY
            CASE stage
                WHEN 'prospecting'  THEN 1
                WHEN 'discovery'    THEN 2
                WHEN 'proposal'     THEN 3
                WHEN 'negotiation'  THEN 4
                WHEN 'closed_won'   THEN 5
                WHEN 'closed_lost'  THEN 6
            END
    """
    return pd.read_sql(query, get_engine())

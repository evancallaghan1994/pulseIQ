"""
Tests for synthetic data generation.
No DB or network required — runs entirely in memory.
"""

import pytest
from data.generate.leads import generate_leads
from data.generate.customers import generate_customers


def test_leads_seed_reproducibility():
    """Running the generator twice with the same seed must produce identical output."""
    df1 = generate_leads()
    df2 = generate_leads()
    assert df1.equals(df2), "Lead generation is not deterministic — check SEED usage"


def test_leads_conversion_pattern():
    """Referral leads must convert at a higher rate than paid_search leads."""
    df = generate_leads()
    referral_rate  = df[df["source"] == "referral"]["converted"].mean()
    paid_rate      = df[df["source"] == "paid_search"]["converted"].mean()
    assert referral_rate > paid_rate, (
        f"Expected referral ({referral_rate:.2%}) > paid_search ({paid_rate:.2%})"
    )


def test_customers_churn_by_tier():
    """Starter tier must churn at a higher rate than enterprise tier."""
    df = generate_customers()
    df["churned"] = df["churn_date"].notna()
    starter_churn    = df[df["subscription_tier"] == "starter"]["churned"].mean()
    enterprise_churn = df[df["subscription_tier"] == "enterprise"]["churned"].mean()
    assert starter_churn > enterprise_churn, (
        f"Expected starter churn ({starter_churn:.2%}) > enterprise ({enterprise_churn:.2%})"
    )

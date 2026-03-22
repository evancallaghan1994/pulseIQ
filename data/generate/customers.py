import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta
from faker import Faker

SEED = 42
fake = Faker()
Faker.seed(SEED)
rng = np.random.default_rng(SEED)

# Observation window end — churn after this date is not yet observed
DATASET_END = date(2026, 1, 1)

# Subscription tier assigned from lead company_size
TIER_MAP = {
    "1-10":     "starter",
    "11-50":    "starter",
    "51-200":   "growth",
    "201-1000": "enterprise",
}

# MRR range by tier (monthly, in USD)
MRR_RANGES = {
    "starter":    (1_800,  2_500),
    "growth":     (5_000,  7_500),
    "enterprise": (12_000, 18_000),
}

# Annual churn probability by tier — starter churns at ~3x enterprise
ANNUAL_CHURN_RATE = {
    "starter":    0.45,
    "growth":     0.25,
    "enterprise": 0.15,
}

# Months of tenure where churn spikes (post-trial and annual renewal)
CHURN_SPIKE_MONTHS = {4: 2.5, 12: 2.5}
MAX_TENURE_MONTHS = 36

# Churn reason weights by tier
CHURN_REASONS = ["price", "product_fit", "competition", "went_dark"]
CHURN_REASON_WEIGHTS = {
    "starter":    [0.40, 0.35, 0.15, 0.10],
    "growth":     [0.25, 0.25, 0.30, 0.20],
    "enterprise": [0.15, 0.20, 0.35, 0.30],
}

# Life sciences company name suffixes for realism
LS_SUFFIXES = [
    "Biosciences", "Therapeutics", "Genomics", "Pharma", "Diagnostics",
    "Life Sciences", "BioTech", "Oncology", "Research Labs", "Sciences",
]


def ls_company_name() -> str:
    return f"{fake.last_name()} {rng.choice(LS_SUFFIXES)}"


def churn_month_weights() -> list[float]:
    """Return a probability distribution over months 1–MAX_TENURE_MONTHS."""
    weights = [1.0] * MAX_TENURE_MONTHS
    for month, multiplier in CHURN_SPIKE_MONTHS.items():
        if month <= MAX_TENURE_MONTHS:
            weights[month - 1] *= multiplier
    total = sum(weights)
    return [w / total for w in weights]


CHURN_WEIGHTS = churn_month_weights()


def generate_customers() -> pd.DataFrame:
    deals = pd.read_csv("data/raw/deals.csv")
    leads = pd.read_csv("data/raw/leads.csv")

    won_deals = deals[deals["outcome"] == "closed_won"].copy()
    won_deals["close_date"] = pd.to_datetime(won_deals["close_date"]).dt.date

    # Join to get company_size from leads
    won_deals = won_deals.merge(leads[["lead_id", "company_size"]], on="lead_id")

    records = []
    for i, (_, deal) in enumerate(won_deals.iterrows()):
        tier = TIER_MAP[deal["company_size"]]
        start_date = deal["close_date"]

        mrr_lo, mrr_hi = MRR_RANGES[tier]
        mrr = int(rng.integers(mrr_lo, mrr_hi + 1))

        # Determine if customer churns within observation window
        annual_rate = ANNUAL_CHURN_RATE[tier]
        churned = rng.random() < annual_rate

        churn_date = None
        churn_reason = None
        if churned:
            # Pick churn month weighted to spike at months 4 and 12
            tenure_month = int(rng.choice(MAX_TENURE_MONTHS, p=CHURN_WEIGHTS)) + 1
            candidate_churn = start_date + relativedelta(months=tenure_month)
            if candidate_churn <= DATASET_END:
                churn_date = candidate_churn
                reason_weights = CHURN_REASON_WEIGHTS[tier]
                churn_reason = CHURN_REASONS[
                    int(rng.choice(len(CHURN_REASONS), p=reason_weights))
                ]

        records.append({
            "customer_id": f"CUST{i + 1:04d}",
            "company_name": ls_company_name(),
            "subscription_tier": tier,
            "mrr": mrr,
            "start_date": start_date,
            "churn_date": churn_date,
            "churn_reason": churn_reason,
        })

    df = pd.DataFrame(records)

    # Validation
    assert df["customer_id"].is_unique, "customer_id must be unique"
    required = ["customer_id", "company_name", "subscription_tier", "mrr", "start_date"]
    assert df[required].isnull().sum().sum() == 0, "Nulls in required fields"
    churned = df[df["churn_date"].notna()]
    assert (churned["churn_date"] > churned["start_date"]).all(), \
        "churn_date must be after start_date"
    assert (df["mrr"] > 0).all(), "MRR must be positive"

    return df


if __name__ == "__main__":
    df = generate_customers()
    df.to_csv("data/raw/customers.csv", index=False)

    total = len(df)
    n_churned = df["churn_date"].notna().sum()
    print(f"customers.csv — {total} rows, {n_churned} churned ({n_churned / total:.1%})")

    print("\nChurn rate by tier (starter should be ~3x enterprise):")
    print(df.groupby("subscription_tier")["churn_date"].apply(
        lambda x: x.notna().mean()
    ).round(3).to_string())

    print("\nChurn reasons (among churned customers):")
    print(df["churn_reason"].value_counts(dropna=True).to_string())

    print("\nAvg MRR by tier:")
    print(df.groupby("subscription_tier")["mrr"].mean().round(0).to_string())

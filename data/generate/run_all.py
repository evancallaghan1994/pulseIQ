"""
Run all synthetic data generators in dependency order.
Produces reproducible CSVs in data/raw/ with a fixed seed.

Usage (from project root):
    python -m data.generate.run_all
"""

import pandas as pd
from .reps import generate_reps
from .leads import generate_leads
from .deals import generate_deals
from .engagement import generate_engagement
from .customers import generate_customers

OUTPUT_DIR = "data/raw"

# Required non-null fields per table
REQUIRED_FIELDS = {
    "reps":       ["rep_id", "name", "hire_date", "territory", "annual_quota"],
    "leads":      ["lead_id", "source", "created_at", "company_size", "industry", "converted"],
    "deals":      ["deal_id", "lead_id", "rep_id", "stage", "created_at",
                   "last_contact_date", "value", "outcome"],
    "engagement": ["event_id", "deal_id", "event_type", "timestamp", "channel"],
    "customers":  ["customer_id", "company_name", "subscription_tier", "mrr", "start_date"],
}


def validate(name: str, df: pd.DataFrame) -> None:
    required = REQUIRED_FIELDS[name]
    nulls = df[required].isnull().sum()
    if nulls.any():
        raise ValueError(f"{name}: nulls found in required fields:\n{nulls[nulls > 0]}")


def run():
    steps = [
        ("reps",       generate_reps),
        ("leads",      generate_leads),
        ("deals",      generate_deals),
        ("engagement", generate_engagement),
        ("customers",  generate_customers),
    ]

    print("Generating synthetic data...\n")
    results = {}

    for name, fn in steps:
        df = fn()
        validate(name, df)
        path = f"{OUTPUT_DIR}/{name}.csv"
        df.to_csv(path, index=False)
        results[name] = df
        print(f"  {name:<12} {len(df):>6} rows  →  {path}")

    print("\nAll validations passed.")
    print(f"\nSummary:")
    print(f"  Leads generated:     {len(results['leads']):,}")
    print(f"  Leads converted:     {results['leads']['converted'].sum():,} "
          f"({results['leads']['converted'].mean():.1%})")
    print(f"  Deals created:       {len(results['deals']):,}")
    print(f"  Deals won:           {(results['deals']['outcome'] == 'closed_won').sum():,}")
    print(f"  Engagement events:   {len(results['engagement']):,}")
    print(f"  Customers:           {len(results['customers']):,}")
    print(f"  Churned customers:   {results['customers']['churn_date'].notna().sum():,}")


if __name__ == "__main__":
    run()

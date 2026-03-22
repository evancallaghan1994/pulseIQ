import pandas as pd
import numpy as np
from datetime import date, timedelta
from faker import Faker

SEED = 42
fake = Faker()
Faker.seed(SEED)
rng = np.random.default_rng(SEED)

N_LEADS = 2000
DATE_START = date(2023, 1, 1)
DATE_END = date(2024, 12, 31)
DATE_RANGE_DAYS = (DATE_END - DATE_START).days

SOURCES = ["paid_search", "organic", "referral", "outbound", "event"]
SOURCE_WEIGHTS = [0.30, 0.25, 0.20, 0.15, 0.10]

# Referral and event convert at 2x the rate of paid_search
SOURCE_CONVERSION_RATES = {
    "paid_search": 0.12,
    "organic":     0.16,
    "referral":    0.24,
    "outbound":    0.14,
    "event":       0.24,
}

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-1000"]
COMPANY_SIZE_WEIGHTS = [0.20, 0.30, 0.30, 0.20]

# 51-200 converts at the highest rate
COMPANY_SIZE_MULTIPLIERS = {
    "1-10":     0.6,
    "11-50":    0.9,
    "51-200":   1.4,
    "201-1000": 1.1,
}

INDUSTRIES = [
    "pharma", "biotech", "medical_devices", "cro",
    "research_university", "hospital_system", "diagnostics",
]
INDUSTRY_WEIGHTS = [0.20, 0.25, 0.15, 0.10, 0.10, 0.10, 0.10]

# Conversion rate reduced 40% in months 3 and 8 (seasonal slowdown)
SLOW_MONTH_MULTIPLIER = 0.60
SLOW_MONTHS = {3, 8}

# Days after lead creation before conversion is recorded (nurturing period)
NURTURE_DAYS_MIN = 7
NURTURE_DAYS_MAX = 60


def conversion_probability(source: str, company_size: str, month: int) -> float:
    base = SOURCE_CONVERSION_RATES[source]
    p = base * COMPANY_SIZE_MULTIPLIERS[company_size]
    if month in SLOW_MONTHS:
        p *= SLOW_MONTH_MULTIPLIER
    return min(p, 1.0)


def generate_leads() -> pd.DataFrame:
    # Sample lead attributes
    sources = rng.choice(SOURCES, size=N_LEADS, p=SOURCE_WEIGHTS)
    company_sizes = rng.choice(COMPANY_SIZES, size=N_LEADS, p=COMPANY_SIZE_WEIGHTS)
    industries = rng.choice(INDUSTRIES, size=N_LEADS, p=INDUSTRY_WEIGHTS)

    # Random creation dates spread across the 24-month window
    day_offsets = rng.integers(0, DATE_RANGE_DAYS, size=N_LEADS)
    created_dates = [DATE_START + timedelta(days=int(d)) for d in day_offsets]

    records = []
    for i in range(N_LEADS):
        created_at = created_dates[i]
        source = sources[i]
        company_size = company_sizes[i]
        industry = industries[i]

        p = conversion_probability(source, company_size, created_at.month)
        converted = bool(rng.random() < p)

        converted_at = None
        conversion_value = None
        if converted:
            nurture_days = int(rng.integers(NURTURE_DAYS_MIN, NURTURE_DAYS_MAX))
            conv_date = created_at + timedelta(days=nurture_days)
            # Don't allow conversion date to exceed dataset end
            converted_at = min(conv_date, DATE_END)
            conversion_value = int(rng.integers(50_000, 500_001))

        records.append({
            "lead_id": f"LEAD{i + 1:04d}",
            "source": source,
            "created_at": created_at,
            "company_size": company_size,
            "industry": industry,
            "converted": converted,
            "converted_at": converted_at,
            "conversion_value": conversion_value,
        })

    df = pd.DataFrame(records)

    # Validation
    assert len(df) == N_LEADS, f"Expected {N_LEADS} leads"
    assert df["lead_id"].is_unique, "lead_id must be unique"
    required_always = ["lead_id", "source", "created_at", "company_size", "industry", "converted"]
    assert df[required_always].isnull().sum().sum() == 0, "Nulls in required fields"
    converted_rows = df[df["converted"]]
    assert (converted_rows["conversion_value"] > 0).all(), "conversion_value must be positive"
    assert (converted_rows["converted_at"] >= converted_rows["created_at"]).all(), \
        "converted_at must not precede created_at"

    return df


if __name__ == "__main__":
    df = generate_leads()
    df.to_csv("data/raw/leads.csv", index=False)

    total = len(df)
    n_converted = df["converted"].sum()
    print(f"leads.csv — {total} rows, {n_converted} converted ({n_converted / total:.1%})")
    print("\nConversion rate by source:")
    print(df.groupby("source")["converted"].mean().round(3).to_string())
    print("\nConversion rate by company_size:")
    print(df.groupby("company_size")["converted"].mean().round(3).to_string())

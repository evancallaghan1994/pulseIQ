import pandas as pd
import numpy as np
from datetime import date
from faker import Faker

SEED = 42
fake = Faker()
Faker.seed(SEED)
rng = np.random.default_rng(SEED)

# 5 territories, 12 reps total (2-3 per territory)
TERRITORIES = [
    "oncology_accounts",
    "oncology_accounts",
    "oncology_accounts",
    "genomics_accounts",
    "genomics_accounts",
    "diagnostics_accounts",
    "diagnostics_accounts",
    "diagnostics_accounts",
    "research_university_accounts",
    "research_university_accounts",
    "medical_devices_accounts",
    "medical_devices_accounts",
]

# Annual quota range reflects enterprise life sciences SaaS ($800k–$1.5M)
QUOTA_MIN = 800_000
QUOTA_MAX = 1_500_000

# Hire dates span 4 years — some tenured, some newer
HIRE_DATE_START = date(2021, 1, 1)
HIRE_DATE_END = date(2024, 6, 1)


def generate_reps() -> pd.DataFrame:
    records = []
    for i, territory in enumerate(TERRITORIES):
        records.append({
            "rep_id": f"REP{i + 1:03d}",
            "name": fake.name(),
            "hire_date": fake.date_between(
                start_date=HIRE_DATE_START, end_date=HIRE_DATE_END
            ),
            "territory": territory,
            "annual_quota": int(rng.integers(QUOTA_MIN, QUOTA_MAX)),
        })

    df = pd.DataFrame(records)

    assert len(df) == 12, "Expected 12 reps"
    assert df["rep_id"].is_unique, "rep_id must be unique"
    assert df.isnull().sum().sum() == 0, "No nulls expected"

    return df


if __name__ == "__main__":
    df = generate_reps()
    df.to_csv("data/raw/reps.csv", index=False)
    print(f"reps.csv — {len(df)} rows")
    print(df.to_string(index=False))

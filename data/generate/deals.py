import pandas as pd
import numpy as np
from datetime import date, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

# Must match DATE_END in leads.py
DATASET_END = date(2024, 12, 31)

# Deals created on or after this date may still be open (recent pipeline)
OPEN_DEAL_CUTOFF = date(2024, 10, 1)

STAGES_OPEN = ["prospecting", "discovery", "proposal", "negotiation"]
STAGES_OPEN_WEIGHTS = [0.15, 0.30, 0.35, 0.20]

PRODUCTS = [
    "LIMS Software",
    "Lab Automation Platform",
    "Genomic Sequencing Tools",
    "Clinical Trial Management Software",
    "Reagent Supply Contract",
]

# First 3 reps (by index) are overperformers
N_OVERPERFORMERS = 3
OVERPERFORMER_WIN_MULTIPLIER = 1.6

# Base win rate for closed deals
BASE_WIN_RATE = 0.55

# Deals where last contact was >14 days before close win 40% less
STALE_CONTACT_DAYS = 14
STALE_CONTACT_MULTIPLIER = 0.60


def generate_deals() -> pd.DataFrame:
    leads = pd.read_csv("data/raw/leads.csv")
    reps = pd.read_csv("data/raw/reps.csv")

    converted = leads[leads["converted"]].copy()
    converted["converted_at"] = pd.to_datetime(converted["converted_at"]).dt.date

    rep_ids = reps["rep_id"].tolist()
    overperformer_ids = set(rep_ids[:N_OVERPERFORMERS])

    records = []
    for i, (_, lead) in enumerate(converted.iterrows()):
        created_at = lead["converted_at"]
        rep_id = rep_ids[int(rng.integers(0, len(rep_ids)))]
        product = PRODUCTS[int(rng.integers(0, len(PRODUCTS)))]

        # Deal velocity: mean 28 days, sd 15, clipped to 7–90
        velocity_days = int(np.clip(rng.normal(28, 15), 7, 90))
        projected_close = created_at + timedelta(days=velocity_days)
        close_date = min(projected_close, DATASET_END)

        # Determine if this is a recent (potentially open) deal
        is_recent = created_at >= OPEN_DEAL_CUTOFF

        if is_recent and rng.random() < 0.65:
            # Open deal — still in pipeline
            stage = STAGES_OPEN[
                int(rng.choice(len(STAGES_OPEN), p=STAGES_OPEN_WEIGHTS))
            ]
            outcome = "open"
            # Last contact is somewhere between created_at and dataset end
            max_days = (DATASET_END - created_at).days
            contact_offset = int(rng.integers(0, max(1, max_days)))
            last_contact_date = created_at + timedelta(days=contact_offset)
            close_date = None
        else:
            # Closed deal — last contact is between created_at and close_date
            max_days = max(1, (close_date - created_at).days)
            contact_offset = int(rng.integers(0, max_days))
            last_contact_date = created_at + timedelta(days=contact_offset)

            # Staleness: days between last contact and close
            days_stale = (close_date - last_contact_date).days

            # Win probability influenced by staleness and rep performance
            win_p = BASE_WIN_RATE
            if days_stale > STALE_CONTACT_DAYS:
                win_p *= STALE_CONTACT_MULTIPLIER
            if rep_id in overperformer_ids:
                win_p = min(win_p * OVERPERFORMER_WIN_MULTIPLIER, 0.95)

            won = rng.random() < win_p
            stage = "closed_won" if won else "closed_lost"
            outcome = "closed_won" if won else "closed_lost"

        value = int(rng.integers(50_000, 500_001))

        records.append({
            "deal_id": f"DEAL{i + 1:04d}",
            "lead_id": lead["lead_id"],
            "rep_id": rep_id,
            "product": product,
            "stage": stage,
            "created_at": created_at,
            "last_contact_date": last_contact_date,
            "close_date": close_date,
            "value": value,
            "outcome": outcome,
        })

    df = pd.DataFrame(records)

    # Validation
    assert df["deal_id"].is_unique, "deal_id must be unique"
    assert df["lead_id"].is_unique, "one deal per lead"
    required = ["deal_id", "lead_id", "rep_id", "stage", "created_at",
                "last_contact_date", "value", "outcome"]
    assert df[required].isnull().sum().sum() == 0, "Nulls in required fields"

    return df


if __name__ == "__main__":
    df = generate_deals()
    df.to_csv("data/raw/deals.csv", index=False)

    total = len(df)
    won = (df["outcome"] == "closed_won").sum()
    lost = (df["outcome"] == "closed_lost").sum()
    open_ = (df["outcome"] == "open").sum()

    print(f"deals.csv — {total} rows")
    print(f"  closed_won: {won}  closed_lost: {lost}  open: {open_}")
    print(f"\nWin rate (closed only): {won / (won + lost):.1%}")
    print(f"Avg deal value: ${df['value'].mean():,.0f}")
    print(f"\nWin rate by rep (top 5):")
    closed = df[df["outcome"] != "open"]
    print(closed.groupby("rep_id")["outcome"].apply(
        lambda x: (x == "closed_won").mean()
    ).sort_values(ascending=False).head(5).round(3).to_string())

import pandas as pd
import numpy as np
from datetime import date, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

# Event counts per deal by outcome — won deals have more total touchpoints
EVENT_COUNTS = {
    "closed_won":  (7, 15),
    "closed_lost": (3, 10),
    "open":        (3, 12),
}

# Base event type weights by outcome
# Won deals have significantly higher meeting frequency
EVENT_WEIGHTS = {
    "closed_won":  {"email_sent": 0.30, "email_reply": 0.25, "call": 0.25, "meeting": 0.20},
    "closed_lost": {"email_sent": 0.40, "email_reply": 0.25, "call": 0.25, "meeting": 0.10},
    "open":        {"email_sent": 0.38, "email_reply": 0.22, "call": 0.28, "meeting": 0.12},
}

# In the last 7 days before a lost deal closes, email reply rate drops sharply
COLD_WINDOW_DAYS = 7
COLD_EMAIL_REPLY_WEIGHT = 0.05  # near-zero replies when deal is going cold

# Channel is derived from event type
MEETING_CHANNELS = ["zoom", "in_person"]
MEETING_CHANNEL_WEIGHTS = [0.75, 0.25]


def channel_for(event_type: str) -> str:
    if event_type in ("email_sent", "email_reply"):
        return "email"
    if event_type == "call":
        return "phone"
    # meeting
    return MEETING_CHANNELS[
        int(rng.choice(len(MEETING_CHANNELS), p=MEETING_CHANNEL_WEIGHTS))
    ]


def random_timestamps(start: date, end: date, n: int) -> list[date]:
    """Return n sorted random dates between start and end (inclusive)."""
    span = (end - start).days
    if span < 1:
        return [start] * n
    offsets = sorted(rng.integers(0, span + 1, size=n).tolist())
    return [start + timedelta(days=int(o)) for o in offsets]


def generate_events_for_deal(deal: pd.Series) -> list[dict]:
    outcome = deal["outcome"]
    created_at = deal["created_at"]

    # Determine the end of the engagement window
    if pd.notna(deal["close_date"]):
        end_date = deal["close_date"]
    else:
        end_date = deal["last_contact_date"]

    if pd.isna(end_date) or end_date < created_at:
        end_date = created_at

    lo, hi = EVENT_COUNTS[outcome]
    n_events = int(rng.integers(lo, hi + 1))
    timestamps = random_timestamps(created_at, end_date, n_events)

    cold_window_start = end_date - timedelta(days=COLD_WINDOW_DAYS)

    weights = EVENT_WEIGHTS[outcome]
    event_types = list(weights.keys())
    base_probs = list(weights.values())

    events = []
    for ts in timestamps:
        # Apply cold window adjustment for lost deals
        if outcome == "closed_lost" and ts >= cold_window_start:
            probs = [
                COLD_EMAIL_REPLY_WEIGHT if et == "email_reply" else w
                for et, w in zip(event_types, base_probs)
            ]
            total = sum(probs)
            probs = [p / total for p in probs]
        else:
            probs = base_probs

        event_type = event_types[int(rng.choice(len(event_types), p=probs))]
        events.append({
            "deal_id": deal["deal_id"],
            "event_type": event_type,
            "timestamp": ts,
            "channel": channel_for(event_type),
        })

    return events


def generate_engagement() -> pd.DataFrame:
    deals = pd.read_csv("data/raw/deals.csv")
    deals["created_at"] = pd.to_datetime(deals["created_at"]).dt.date
    deals["close_date"] = pd.to_datetime(deals["close_date"], errors="coerce").dt.date
    deals["last_contact_date"] = pd.to_datetime(deals["last_contact_date"]).dt.date

    all_events = []
    for _, deal in deals.iterrows():
        all_events.extend(generate_events_for_deal(deal))

    df = pd.DataFrame(all_events)
    df.insert(0, "event_id", [f"EVT{i + 1:05d}" for i in range(len(df))])

    # Validation
    assert df["event_id"].is_unique, "event_id must be unique"
    assert df.isnull().sum().sum() == 0, "No nulls expected"
    assert df["event_type"].isin(["email_sent", "email_reply", "call", "meeting"]).all()
    assert df["channel"].isin(["email", "phone", "zoom", "in_person"]).all()

    return df


if __name__ == "__main__":
    df = generate_engagement()
    df.to_csv("data/raw/engagement.csv", index=False)

    print(f"engagement.csv — {len(df)} rows across {df['deal_id'].nunique()} deals")
    print(f"Avg events per deal: {len(df) / df['deal_id'].nunique():.1f}")

    print("\nEvent type distribution (all deals):")
    print(df["event_type"].value_counts(normalize=True).round(3).to_string())

    # Verify meeting frequency is higher for won deals
    deals = pd.read_csv("data/raw/deals.csv")
    merged = df.merge(deals[["deal_id", "outcome"]], on="deal_id")
    meeting_rate = merged.groupby("outcome").apply(
        lambda x: (x["event_type"] == "meeting").mean()
    ).round(3)
    print("\nMeeting rate by outcome (won should be highest):")
    print(meeting_rate.to_string())

"""
Load synthetic CSVs into PostgreSQL.
Tables are truncated then reloaded on each run, preserving schema constraints.
Run order respects foreign key dependencies: reps → leads → deals → engagement → customers.

Usage (from project root):
    python -m pipeline.load
"""

import pandas as pd
from sqlalchemy import text
from db.connection import get_engine

DATA_DIR = "data/raw"

# Truncate in reverse FK order to avoid constraint violations
TRUNCATE_ORDER = ["engagement", "customers", "deals", "leads", "reps"]

# Load in forward FK order
LOAD_ORDER = ["reps", "leads", "deals", "engagement", "customers"]

# Columns to parse as dates per table
DATE_COLS = {
    "reps":       ["hire_date"],
    "leads":      ["created_at", "converted_at"],
    "deals":      ["created_at", "last_contact_date", "close_date"],
    "engagement": ["timestamp"],
    "customers":  ["start_date", "churn_date"],
}


def _truncate_all(engine) -> None:
    with engine.begin() as conn:
        for table in TRUNCATE_ORDER:
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))


def _load_table(name: str, engine) -> int:
    path = f"{DATA_DIR}/{name}.csv"
    df = pd.read_csv(path, parse_dates=DATE_COLS.get(name, []))

    # Normalise date columns to plain date (drop time component if present)
    for col in DATE_COLS.get(name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    df.to_sql(name, con=engine, if_exists="append", index=False)
    return len(df)


def load_reps(engine=None) -> int:
    engine = engine or get_engine()
    return _load_table("reps", engine)


def load_leads(engine=None) -> int:
    engine = engine or get_engine()
    return _load_table("leads", engine)


def load_deals(engine=None) -> int:
    engine = engine or get_engine()
    return _load_table("deals", engine)


def load_engagement(engine=None) -> int:
    engine = engine or get_engine()
    return _load_table("engagement", engine)


def load_customers(engine=None) -> int:
    engine = engine or get_engine()
    return _load_table("customers", engine)


def load_all() -> None:
    engine = get_engine()

    print("Truncating existing data...")
    _truncate_all(engine)

    print("Loading tables...\n")
    for name in LOAD_ORDER:
        n = _load_table(name, engine)
        print(f"  {name:<12} {n:>6} rows loaded")

    print("\nAll tables loaded successfully.")


if __name__ == "__main__":
    load_all()

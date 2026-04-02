"""
Data validation functions for each table.
Each validator accepts a DataFrame and returns a list of issue strings.
Empty list means no issues found.

Usage:
    from pipeline.validate import validate_all
    issues = validate_all(dataframes_dict)
"""

import pandas as pd
from datetime import date

VALID_LEAD_SOURCES   = {"paid_search", "organic", "referral", "outbound", "event"}
VALID_COMPANY_SIZES  = {"1-10", "11-50", "51-200", "201-1000"}
VALID_DEAL_STAGES    = {"prospecting", "discovery", "proposal", "negotiation",
                        "closed_won", "closed_lost"}
VALID_OUTCOMES       = {"closed_won", "closed_lost", "open"}
VALID_EVENT_TYPES    = {"email_sent", "email_reply", "call", "meeting"}
VALID_CHANNELS       = {"email", "phone", "zoom", "in_person"}
VALID_TIERS          = {"starter", "growth", "enterprise"}
VALID_CHURN_REASONS  = {"price", "product_fit", "competition", "went_dark"}


def _as_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def validate_leads(df: pd.DataFrame) -> list[str]:
    issues = []
    today = date.today()

    # converted leads must have a positive conversion_value
    converted = df[df["converted"] == True]
    bad_value = converted[
        converted["conversion_value"].isna() | (converted["conversion_value"] <= 0)
    ]
    if len(bad_value):
        issues.append(
            f"leads: {len(bad_value)} converted rows have missing or non-positive conversion_value"
        )

    # converted_at must not precede created_at
    has_conv = df["converted_at"].notna()
    if has_conv.any():
        created = _as_date(df.loc[has_conv, "created_at"])
        converted_at = _as_date(df.loc[has_conv, "converted_at"])
        bad_dates = (converted_at < created).sum()
        if bad_dates:
            issues.append(f"leads: {bad_dates} rows where converted_at < created_at")

    # no future dates in created_at
    future = (_as_date(df["created_at"]) > today).sum()
    if future:
        issues.append(f"leads: {future} rows with created_at in the future")

    # valid enum values
    bad_source = ~df["source"].isin(VALID_LEAD_SOURCES)
    if bad_source.any():
        issues.append(f"leads: {bad_source.sum()} rows with invalid source values")

    bad_size = ~df["company_size"].isin(VALID_COMPANY_SIZES)
    if bad_size.any():
        issues.append(f"leads: {bad_size.sum()} rows with invalid company_size values")

    return issues


def validate_deals(df: pd.DataFrame, leads_df: pd.DataFrame) -> list[str]:
    issues = []

    # last_contact_date must be >= created_at
    created = _as_date(df["created_at"])
    last_contact = _as_date(df["last_contact_date"])
    bad_contact = (last_contact < created).sum()
    if bad_contact:
        issues.append(f"deals: {bad_contact} rows where last_contact_date < created_at")

    # close_date must be >= created_at when present
    has_close = df["close_date"].notna()
    if has_close.any():
        close = _as_date(df.loc[has_close, "close_date"])
        cr = _as_date(df.loc[has_close, "created_at"])
        bad_close = (close < cr).sum()
        if bad_close:
            issues.append(f"deals: {bad_close} rows where close_date < created_at")

    # valid enum values
    bad_stage = ~df["stage"].isin(VALID_DEAL_STAGES)
    if bad_stage.any():
        issues.append(f"deals: {bad_stage.sum()} rows with invalid stage values")

    bad_outcome = ~df["outcome"].isin(VALID_OUTCOMES)
    if bad_outcome.any():
        issues.append(f"deals: {bad_outcome.sum()} rows with invalid outcome values")

    # FK: every lead_id in deals must exist in leads
    missing_leads = ~df["lead_id"].isin(leads_df["lead_id"])
    if missing_leads.any():
        issues.append(f"deals: {missing_leads.sum()} rows reference non-existent lead_id")

    return issues


def validate_engagement(df: pd.DataFrame, deals_df: pd.DataFrame) -> list[str]:
    issues = []

    # FK: every deal_id in engagement must exist in deals
    missing_deals = ~df["deal_id"].isin(deals_df["deal_id"])
    if missing_deals.any():
        issues.append(
            f"engagement: {missing_deals.sum()} rows reference non-existent deal_id"
        )

    # timestamps must fall within deal lifespan (created_at to close_date or last_contact_date)
    # Parse date columns before merge so fillna operates on date objects, not strings
    deals_window = deals_df[["deal_id", "created_at", "close_date", "last_contact_date"]].copy()
    deals_window["close_date"] = _as_date(deals_window["close_date"])
    deals_window["last_contact_date"] = _as_date(deals_window["last_contact_date"])

    merged = df.merge(deals_window, on="deal_id", how="left")
    ts = _as_date(merged["timestamp"])
    deal_start = _as_date(merged["created_at"])

    # end of deal window: close_date if present, else last_contact_date
    deal_end = merged["close_date"].combine_first(merged["last_contact_date"])

    before_start = (ts < deal_start).sum()
    after_end = (ts > deal_end).sum()

    if before_start:
        issues.append(f"engagement: {before_start} events before deal created_at")
    if after_end:
        issues.append(f"engagement: {after_end} events after deal end date")

    # valid enum values
    bad_type = ~df["event_type"].isin(VALID_EVENT_TYPES)
    if bad_type.any():
        issues.append(f"engagement: {bad_type.sum()} rows with invalid event_type")

    bad_channel = ~df["channel"].isin(VALID_CHANNELS)
    if bad_channel.any():
        issues.append(f"engagement: {bad_channel.sum()} rows with invalid channel")

    return issues


def validate_customers(df: pd.DataFrame) -> list[str]:
    issues = []

    # MRR must be positive
    bad_mrr = (df["mrr"] <= 0).sum()
    if bad_mrr:
        issues.append(f"customers: {bad_mrr} rows with non-positive MRR")

    # churn_date must be after start_date when present
    has_churn = df["churn_date"].notna()
    if has_churn.any():
        start = _as_date(df.loc[has_churn, "start_date"])
        churn = _as_date(df.loc[has_churn, "churn_date"])
        bad_churn = (churn <= start).sum()
        if bad_churn:
            issues.append(f"customers: {bad_churn} rows where churn_date <= start_date")

    # churned rows must have a churn_reason
    churned_no_reason = has_churn & df["churn_reason"].isna()
    if churned_no_reason.any():
        issues.append(
            f"customers: {churned_no_reason.sum()} churned rows missing churn_reason"
        )

    # valid enum values
    bad_tier = ~df["subscription_tier"].isin(VALID_TIERS)
    if bad_tier.any():
        issues.append(f"customers: {bad_tier.sum()} rows with invalid subscription_tier")

    return issues


def validate_all(data: dict) -> dict:
    """
    Run all validators. Accepts a dict of {table_name: DataFrame}.
    Returns a dict of {table_name: [issue_strings]}.
    """
    results = {
        "leads":      validate_leads(data["leads"]),
        "deals":      validate_deals(data["deals"], data["leads"]),
        "engagement": validate_engagement(data["engagement"], data["deals"]),
        "customers":  validate_customers(data["customers"]),
    }
    return results


if __name__ == "__main__":
    import os
    data = {
        name: pd.read_csv(f"data/raw/{name}.csv")
        for name in ["leads", "deals", "engagement", "customers"]
    }

    all_issues = validate_all(data)
    total = sum(len(v) for v in all_issues.values())

    if total == 0:
        print("All validations passed — no issues found.")
    else:
        print(f"{total} issue(s) found:\n")
        for table, issues in all_issues.items():
            for issue in issues:
                print(f"  WARNING: {issue}")

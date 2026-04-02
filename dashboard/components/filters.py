"""
Reusable sidebar filter components for the PulseIQ dashboard.
"""

import pandas as pd
import streamlit as st


def source_filter(df: pd.DataFrame) -> str:
    """Selectbox filter for lead source. Returns selected value or 'All'."""
    options = ["All"] + sorted(df["source"].unique().tolist())
    return st.selectbox("Source", options)


def industry_filter(df: pd.DataFrame) -> str:
    """Selectbox filter for industry. Returns selected value or 'All'."""
    options = ["All"] + sorted(df["industry"].unique().tolist())
    return st.selectbox("Industry", options)


def company_size_filter(df: pd.DataFrame) -> str:
    """Selectbox filter for company size. Returns selected value or 'All'."""
    options = ["All"] + sorted(df["company_size"].unique().tolist())
    return st.selectbox("Company Size", options)


def apply_filters(df: pd.DataFrame, source: str, industry: str, size: str) -> pd.DataFrame:
    """Apply source, industry, and company_size filters to a DataFrame."""
    if source   != "All": df = df[df["source"]       == source]
    if industry != "All": df = df[df["industry"]     == industry]
    if size     != "All": df = df[df["company_size"] == size]
    return df

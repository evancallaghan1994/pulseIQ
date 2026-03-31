"""
Insights page.
Shows AI-generated insights, MRR trend, and churn by tier.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from db.connection import get_engine
from db.queries import get_churn_rate_by_tier, get_mrr_timeseries

st.set_page_config(page_title="Insights · PulseIQ", page_icon="📊", layout="wide")

with st.sidebar:
    st.markdown("## 🔬 PulseIQ")
    st.markdown("*AI Sales Intelligence*")
    st.divider()
    st.page_link("app.py",                          label="Home",               icon="🏠")
    st.page_link("pages/01_lead_scoring.py",        label="Lead Scoring",        icon="🎯")
    st.page_link("pages/02_deal_risk.py",           label="Deal Risk",           icon="⚠️")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant", icon="💬")
    st.page_link("pages/04_insights.py",            label="Insights",            icon="📊")

BADGE_COLORS = {
    "mrr":      "🟦",
    "churn":    "🟥",
    "pipeline": "🟧",
    "leads":    "🟩",
    "deals":    "🟨",
}


@st.cache_resource
def _get_engine():
    return get_engine()


def load_insights() -> pd.DataFrame:
    engine = _get_engine()
    return pd.read_sql(
        "SELECT id, insight_type, summary, generated_at FROM insights ORDER BY generated_at DESC",
        engine,
    )


st.title("📊 Autonomous Insights")
st.caption("AI-generated business insights · Powered by Claude · Run daily at midnight")

# Refresh button
col_btn, col_spacer = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Refresh Insights", use_container_width=True):
        with st.spinner("Running insight agent..."):
            from agents.insight_agent import run_insight_agent
            run_insight_agent()
        st.success("New insights generated!")
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Insight cards ─────────────────────────────────────────────────────────────
st.subheader("Latest Insights")
insights_df = load_insights()

if insights_df.empty:
    st.info("No insights yet. Click 'Refresh Insights' to generate the first batch.")
else:
    for _, row in insights_df.iterrows():
        badge = BADGE_COLORS.get(row["insight_type"], "⬜")
        ts    = pd.to_datetime(row["generated_at"]).strftime("%b %d, %Y %H:%M")
        with st.container(border=True):
            st.markdown(f"{badge} **{row['insight_type'].upper()}** &nbsp;·&nbsp; {ts}")
            st.markdown(row["summary"])

st.divider()

# ── MRR trend ─────────────────────────────────────────────────────────────────
st.subheader("MRR Trend")

@st.cache_data(ttl=300)
def load_mrr():
    return get_mrr_timeseries()

mrr_df = load_mrr()
mrr_df["month"] = pd.to_datetime(mrr_df["month"])
fig_mrr = px.line(
    mrr_df, x="month", y="mrr",
    labels={"month": "Month", "mrr": "MRR ($)"},
    markers=True,
)
fig_mrr.update_traces(line_color="#1f77b4")
st.plotly_chart(fig_mrr, use_container_width=True)

st.divider()

# ── Churn by tier ─────────────────────────────────────────────────────────────
st.subheader("Churn Rate by Subscription Tier")

@st.cache_data(ttl=300)
def load_churn():
    return get_churn_rate_by_tier()

churn_df = load_churn()
fig_churn = px.bar(
    churn_df,
    x="subscription_tier", y="churn_rate_pct",
    color="subscription_tier",
    color_discrete_sequence=["#d62728", "#ff7f0e", "#2ca02c"],
    labels={"subscription_tier": "Tier", "churn_rate_pct": "Churn Rate (%)"},
    text="churn_rate_pct",
)
fig_churn.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_churn.update_layout(showlegend=False)
st.plotly_chart(fig_churn, use_container_width=True)

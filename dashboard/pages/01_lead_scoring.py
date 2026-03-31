"""
Lead Scoring page.
Displays model scores for all leads with filters, metric cards, and charts.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from db.connection import get_engine
from models.lead_scoring.predict import score_leads

st.set_page_config(page_title="Lead Scoring · PulseIQ", page_icon="🎯", layout="wide")

with st.sidebar:
    st.markdown("## 🔬 PulseIQ")
    st.markdown("*AI Sales Intelligence*")
    st.divider()
    st.page_link("app.py",                          label="Home",               icon="🏠")
    st.page_link("pages/01_lead_scoring.py",        label="Lead Scoring",        icon="🎯")
    st.page_link("pages/02_deal_risk.py",           label="Deal Risk",           icon="⚠️")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant", icon="💬")
    st.page_link("pages/04_insights.py",            label="Insights",            icon="📊")


@st.cache_resource
def _get_engine():
    return get_engine()


@st.cache_data(ttl=300)
def load_lead_scores() -> pd.DataFrame:
    engine = _get_engine()
    leads = pd.read_sql("SELECT lead_id, source, company_size, industry, converted FROM leads", engine)
    scores = score_leads()
    df = leads.merge(scores, on="lead_id", how="inner")
    df = df.sort_values("rank").reset_index(drop=True)
    return df


def score_color(score: float) -> str:
    if score >= 0.7:
        return "🟢"
    elif score >= 0.4:
        return "🟡"
    return "🔴"


st.title("🎯 Lead Scoring")
st.caption("Conversion probability scored by XGBoost · Refreshes every 5 minutes")

with st.spinner("Loading lead scores..."):
    df = load_lead_scores()

# ── Filters ──────────────────────────────────────────────────────────────────
with st.expander("Filters", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        sources = ["All"] + sorted(df["source"].unique().tolist())
        source_filter = st.selectbox("Source", sources)
    with col2:
        industries = ["All"] + sorted(df["industry"].unique().tolist())
        industry_filter = st.selectbox("Industry", industries)
    with col3:
        sizes = ["All"] + sorted(df["company_size"].unique().tolist())
        size_filter = st.selectbox("Company Size", sizes)

filtered = df.copy()
if source_filter   != "All": filtered = filtered[filtered["source"]       == source_filter]
if industry_filter != "All": filtered = filtered[filtered["industry"]     == industry_filter]
if size_filter     != "All": filtered = filtered[filtered["company_size"] == size_filter]

# ── Metric cards ─────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Leads",       len(filtered))
m2.metric("Conversion Rate",   f"{filtered['converted'].mean():.1%}")
m3.metric("Avg Score",         f"{filtered['score'].mean():.2f}")
top_source = filtered.groupby("source")["score"].mean().idxmax()
m4.metric("Top Source",        top_source)

st.divider()

# ── Lead table ────────────────────────────────────────────────────────────────
st.subheader("Lead Priority Table")

display = filtered[["rank", "lead_id", "source", "industry", "company_size", "score", "converted"]].copy()
display["priority"] = display["score"].apply(score_color)
display = display.rename(columns={
    "rank": "Rank", "lead_id": "Lead ID", "source": "Source",
    "industry": "Industry", "company_size": "Company Size",
    "score": "Score", "converted": "Converted", "priority": "Priority",
})
display = display[["Rank", "Priority", "Lead ID", "Source", "Industry", "Company Size", "Score", "Converted"]]

st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

# ── Chart: avg score by source ────────────────────────────────────────────────
st.subheader("Average Score by Acquisition Source")
source_avg = (
    filtered.groupby("source")["score"]
    .mean()
    .reset_index()
    .sort_values("score", ascending=False)
)
fig = px.bar(
    source_avg,
    x="source", y="score",
    color="score",
    color_continuous_scale=["#d62728", "#ff7f0e", "#2ca02c"],
    range_color=[0, 1],
    labels={"source": "Source", "score": "Avg Score"},
)
fig.update_layout(coloraxis_showscale=False, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

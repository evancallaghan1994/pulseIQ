"""
PulseIQ Streamlit app entry point.

Usage (from project root):
    streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="PulseIQ",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("## PulseIQ")
    st.caption("Sales intelligence for life sciences teams")
    st.divider()
    st.page_link("pages/01_lead_scoring.py",        label="Lead Scoring")
    st.page_link("pages/02_deal_risk.py",           label="Deal Risk")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant")
    st.page_link("pages/04_insights.py",            label="Insights")
    st.divider()
    st.caption("Synthetic demo data")

st.title("PulseIQ")
st.markdown(
    "Small B2B sales teams have more data than they can act on and no analyst to "
    "make sense of it. PulseIQ turns raw leads, deals and activity into four things "
    "a rep or manager can use every day."
)

cards = [
    ("Lead Scoring", "pages/01_lead_scoring.py",
     "Which inbound leads to call first, ranked by an XGBoost model (ROC-AUC 0.75)."),
    ("Deal Risk", "pages/02_deal_risk.py",
     "Open deals likely to close lost, based on engagement signals (ROC-AUC 0.94)."),
    ("Knowledge Assistant", "pages/03_knowledge_assistant.py",
     "Answers from internal sales docs with sources, and says so when the docs don't cover it."),
    ("Daily Insights", "pages/04_insights.py",
     "Three prioritized insights written by Claude from a nightly metrics snapshot."),
]

for col, (name, page, description) in zip(st.columns(4), cards):
    with col:
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(description)
            st.page_link(page, label="Open")

st.divider()
st.caption(
    "Built by Evan Callaghan as a portfolio project. All data is synthetic "
    "(Faker + NumPy, seed 42). Stack: PostgreSQL, XGBoost + MLflow, ChromaDB, "
    "Claude API, Airflow, Streamlit, on one VM."
)

"""
PulseIQ — AI Sales Intelligence Platform
Streamlit app entry point.

Usage (from project root):
    streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="PulseIQ",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar branding
with st.sidebar:
    st.markdown("## 🔬 PulseIQ")
    st.markdown("*AI Sales Intelligence*")
    st.divider()
    st.markdown("**Navigation**")
    st.page_link("pages/01_lead_scoring.py",      label="Lead Scoring",        icon="🎯")
    st.page_link("pages/02_deal_risk.py",          label="Deal Risk",           icon="⚠️")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant", icon="💬")
    st.page_link("pages/04_insights.py",           label="Insights",            icon="📊")
    st.divider()
    st.caption("Synthetic demo data · For portfolio use only")

# Home page content
st.title("Welcome to PulseIQ")
st.markdown("#### AI-powered sales intelligence for life sciences teams.")
st.markdown("")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info("**🎯 Lead Scoring**\n\nPrioritise leads by conversion probability using XGBoost.")

with col2:
    st.warning("**⚠️ Deal Risk**\n\nFlag at-risk deals before they go dark using engagement signals.")

with col3:
    st.success("**💬 Knowledge Assistant**\n\nAnswer sales rep questions using your internal knowledge base.")

with col4:
    st.info("**📊 Insights**\n\nAutonomous daily AI insights powered by Claude.")

st.markdown("---")
st.markdown("Select a page from the sidebar to get started.")

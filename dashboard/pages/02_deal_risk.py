"""
Deal Risk page.
Shows active deals scored by risk probability with alert callouts and charts.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from db.queries import get_active_deals
from models.deal_risk.predict import score_deals

st.set_page_config(page_title="Deal Risk · PulseIQ", layout="wide")

with st.sidebar:
    st.markdown("## PulseIQ")
    st.caption("Sales intelligence for life sciences teams")
    st.divider()
    st.page_link("app.py",                          label="Home")
    st.page_link("pages/01_lead_scoring.py",        label="Lead Scoring")
    st.page_link("pages/02_deal_risk.py",           label="Deal Risk")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant")
    st.page_link("pages/04_insights.py",            label="Insights")
    st.divider()
    st.caption("Synthetic demo data")


@st.cache_data(ttl=300)
def load_deal_risk() -> pd.DataFrame:
    deals  = get_active_deals()
    from db.connection import get_engine
    from sqlalchemy import text

    # deal_features only holds closed deals (they have labels), so open deals are
    # scored here from live data. "Days since contact" is measured against the latest
    # contact date in the dataset rather than today's date, because the synthetic data
    # ends in 2024 and CURRENT_DATE would make every open deal look 600+ days silent.
    engine = get_engine()
    open_features_query = text("""
        SELECT
            d.deal_id,
            d.value                                         AS deal_value,
            d.last_contact_date - d.created_at             AS deal_age_days,
            (SELECT MAX(last_contact_date) FROM deals) - d.last_contact_date AS days_since_last_contact,
            COUNT(e.event_id)                               AS engagement_count,
            SUM(CASE WHEN e.event_type = 'meeting' THEN 1 ELSE 0 END) AS meeting_count,
            SUM(CASE WHEN e.event_type = 'email_reply' THEN 1 ELSE 0 END)::float /
                NULLIF(SUM(CASE WHEN e.event_type = 'email_sent' THEN 1 ELSE 0 END), 0) AS email_reply_rate
        FROM deals d
        LEFT JOIN engagement e ON e.deal_id = d.deal_id
        WHERE d.outcome = 'open'
        GROUP BY d.deal_id, d.value, d.last_contact_date, d.created_at
    """)
    with engine.connect() as conn:
        feat_df = pd.read_sql(open_features_query, conn)

    for col in ["deal_age_days", "days_since_last_contact"]:
        feat_df[col] = feat_df[col].apply(lambda x: x.days if hasattr(x, "days") else int(x))
    feat_df["email_reply_rate"] = feat_df["email_reply_rate"].fillna(0.0)

    import mlflow.xgboost, os
    from dotenv import load_dotenv
    load_dotenv()
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    model = mlflow.xgboost.load_model("models:/deal_risk_model/latest")

    from models.deal_risk.features import FEATURE_COLS
    scores = model.predict_proba(feat_df[FEATURE_COLS])[:, 1]
    feat_df["risk_score"] = scores.round(4)

    df = deals.merge(feat_df[["deal_id", "risk_score"]], on="deal_id", how="left")
    df["risk_score"] = df["risk_score"].fillna(0.0)
    df["at_risk"] = df["risk_score"] > 0.7
    df = df.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return df


st.title("Deal Risk")
st.caption("Open deals scored by probability of closing lost (XGBoost). Deals above 0.7 are flagged.")

with st.spinner("Scoring active deals..."):
    df = load_deal_risk()

# Metric cards
total       = len(df)
at_risk_n   = int(df["at_risk"].sum())
at_risk_pct = at_risk_n / total if total else 0
avg_age     = df["days_since_last_contact"].mean()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Open Deals",          total)
m2.metric("Deals At Risk",       f"{at_risk_n} ({at_risk_pct:.0%})")
m3.metric("Avg Days Since Contact", f"{avg_age:.0f}")
m4.metric("Total Pipeline Value", f"${df['value'].sum():,.0f}")

# High-risk alerts
critical = df[df["risk_score"] > 0.8]
if not critical.empty:
    st.divider()
    st.error(f"**{len(critical)} deals have a risk score above 0.8**")
    for _, row in critical.iterrows():
        st.warning(
            f"**{row['deal_id']}** — {row['rep_name']} · ${row['value']:,.0f} · "
            f"{row['days_since_last_contact']} days silent · Risk: {row['risk_score']:.2f}"
        )

st.divider()

# Deal table
st.subheader("Active Deal Risk Table")

display = df[[
    "deal_id", "rep_name", "stage", "value",
    "days_since_last_contact", "engagement_count", "risk_score", "at_risk"
]].copy()
display["risk_score"] = display["risk_score"].map("{:.2f}".format)
display["value"]      = display["value"].map("${:,.0f}".format)
display = display.rename(columns={
    "deal_id": "Deal ID", "rep_name": "Rep", "stage": "Stage",
    "value": "Value", "days_since_last_contact": "Days Silent",
    "engagement_count": "Engagements", "risk_score": "Risk Score", "at_risk": "At Risk",
})
st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

# Scatter: risk score vs days since last contact
st.subheader("Risk Score vs Days Since Last Contact")
fig = px.scatter(
    df,
    x="days_since_last_contact",
    y="risk_score",
    color="at_risk",
    color_discrete_map={True: "#d62728", False: "#2ca02c"},
    hover_data=["deal_id", "rep_name", "value"],
    labels={
        "days_since_last_contact": "Days Since Last Contact",
        "risk_score": "Risk Score",
        "at_risk": "At Risk",
    },
)
fig.add_hline(y=0.7, line_dash="dash", line_color="orange", annotation_text="Risk threshold (0.7)")
st.plotly_chart(fig, use_container_width=True)

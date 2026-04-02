"""
Autonomous insight agent.
Pulls a structured data snapshot from PostgreSQL, sends it to Claude,
parses the response into individual insights, and writes them to the insights table.

Usage (from project root):
    python -m agents.insight_agent
"""

import json
import os
from datetime import date, timedelta

import anthropic
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from db.connection import get_engine
from db.queries import get_churn_rate_by_tier, get_mrr_timeseries
from models.deal_risk.predict import score_deals

load_dotenv()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-6")

SYSTEM_PROMPT = """You are a business analyst for a B2B SaaS company called PulseIQ.
You will be given a structured data snapshot. Identify exactly 3 important patterns or anomalies a founder should act on.

Format your response as a JSON array with exactly 3 objects. Each object must have:
- "insight_type": one of ["mrr", "churn", "pipeline", "leads", "deals"]
- "summary": a concise, specific, actionable insight (2-3 sentences max)

Return ONLY the JSON array. No preamble, no explanation outside the JSON."""


def _build_snapshot() -> dict:
    """Pull all data needed for the insight snapshot."""
    engine = get_engine()

    # MRR: last 30 days vs prior 30 days
    mrr_df = get_mrr_timeseries()
    if len(mrr_df) >= 2:
        mrr_current = float(mrr_df.iloc[-1]["mrr"])
        mrr_prior   = float(mrr_df.iloc[-2]["mrr"])
        mrr_change_pct = round((mrr_current - mrr_prior) / mrr_prior * 100, 1) if mrr_prior else 0.0
    else:
        mrr_current = mrr_prior = mrr_change_pct = 0.0

    # Churn rate by tier
    churn_df = get_churn_rate_by_tier()
    churn_by_tier = churn_df.set_index("subscription_tier")["churn_rate_pct"].to_dict()

    # Deal velocity: avg days from created_at to close_date, this month vs last month
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    velocity_query = text("""
        SELECT
            DATE_TRUNC('month', close_date)::date AS month,
            ROUND(AVG(close_date - created_at))   AS avg_velocity_days
        FROM deals
        WHERE outcome != 'open'
          AND close_date >= :last_month_start
        GROUP BY 1
        ORDER BY 1
    """)
    with engine.connect() as conn:
        vel_rows = conn.execute(velocity_query, {"last_month_start": last_month_start}).fetchall()
    velocity = {str(r[0]): int(r[1]) for r in vel_rows if r[1] is not None}

    # Top 3 acquisition channels by conversion rate
    channel_query = text("""
        SELECT source, ROUND(AVG(converted::int) * 100, 1) AS conversion_rate_pct
        FROM leads
        GROUP BY source
        ORDER BY conversion_rate_pct DESC
        LIMIT 3
    """)
    with engine.connect() as conn:
        ch_rows = conn.execute(channel_query).fetchall()
    top_channels = [{"source": r[0], "conversion_rate_pct": float(r[1])} for r in ch_rows]

    # Deals flagged at-risk (risk_score > 0.7)
    risk_df = score_deals()
    at_risk_count = int((risk_df["risk_score"] > 0.7).sum())
    at_risk_total_value_query = text("""
        SELECT COALESCE(SUM(value), 0) FROM deals WHERE outcome = 'open'
    """)
    with engine.connect() as conn:
        open_pipeline_value = int(conn.execute(at_risk_total_value_query).scalar())

    return {
        "mrr": {
            "current_month": mrr_current,
            "prior_month":   mrr_prior,
            "change_pct":    mrr_change_pct,
        },
        "churn_by_tier": churn_by_tier,
        "deal_velocity_days": velocity,
        "top_acquisition_channels": top_channels,
        "deals_at_risk": {
            "count":               at_risk_count,
            "open_pipeline_value": open_pipeline_value,
        },
    }


def _call_claude(snapshot: dict) -> list[dict]:
    """Send snapshot to Claude and parse the JSON insight array."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    snapshot_text = json.dumps(snapshot, indent=2, default=str)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Data snapshot:\n{snapshot_text}"}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    insights = json.loads(raw)
    assert isinstance(insights, list) and len(insights) == 3, \
        f"Expected 3 insights, got: {raw}"
    return insights


def _write_insights(insights: list[dict], snapshot: dict) -> list[dict]:
    """Write insight records to the insights table."""
    engine = get_engine()
    snapshot_json = json.dumps(snapshot, default=str)
    written = []

    with engine.begin() as conn:
        for item in insights:
            conn.execute(text("""
                INSERT INTO insights (insight_type, summary, data_snapshot)
                VALUES (:insight_type, :summary, :data_snapshot)
            """), {
                "insight_type":  item["insight_type"],
                "summary":       item["summary"],
                "data_snapshot": snapshot_json,
            })
            written.append(item)

    return written


def run_insight_agent() -> list[dict]:
    """
    Run the full insight agent pipeline.

    Returns:
        List of insight dicts written to the DB.
    """
    print("Building data snapshot...")
    snapshot = _build_snapshot()

    print("Calling Claude for insights...")
    insights = _call_claude(snapshot)

    print("Writing insights to DB...")
    written = _write_insights(insights, snapshot)

    print(f"\n{len(written)} insights written:")
    for i, item in enumerate(written, 1):
        print(f"  {i}. [{item['insight_type']}] {item['summary']}")

    return written


if __name__ == "__main__":
    run_insight_agent()

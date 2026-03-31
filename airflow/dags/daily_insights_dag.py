"""
PulseIQ daily insights DAG.
Runs at midnight every day, calls run_insight_agent(), and writes
new insights to the PostgreSQL insights table.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# Ensure the project root is on the path so imports resolve correctly
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _run_agent():
    from agents.insight_agent import run_insight_agent
    insights = run_insight_agent()
    print(f"Insight agent wrote {len(insights)} insights.")


default_args = {
    "owner":            "pulseiq",
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

with DAG(
    dag_id="pulseiq_daily_insights",
    description="Run the PulseIQ insight agent and write results to PostgreSQL",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["pulseiq"],
) as dag:

    run_insights = PythonOperator(
        task_id="run_insight_agent",
        python_callable=_run_agent,
    )

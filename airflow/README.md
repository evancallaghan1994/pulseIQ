# Airflow Setup — PulseIQ

Airflow runs locally using the **LocalExecutor** with a SQLite metadata database. No Docker required — install directly into the project virtualenv.

## Prerequisites

- Python 3.12 virtualenv activated
- `AIRFLOW_HOME` set to the `airflow/` directory inside the project

## Installation

```bash
# From the project root, with virtualenv activated
export AIRFLOW_HOME=$(pwd)/airflow

pip install "apache-airflow==2.9.*" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt"
```

## Initialise the database and create admin user

```bash
export AIRFLOW_HOME=$(pwd)/airflow

airflow db init

airflow users create \
  --role Admin \
  --username admin \
  --password admin \
  --firstname Evan \
  --lastname Dev \
  --email dev@example.com
```

## Configure LocalExecutor

Edit `airflow/airflow.cfg` and set:

```ini
[core]
executor = LocalExecutor

[database]
sql_alchemy_conn = sqlite:///airflow/airflow.db
```

## Start Airflow

Run webserver and scheduler in separate terminals (or background them):

```bash
export AIRFLOW_HOME=$(pwd)/airflow

# Terminal 1
airflow webserver -p 8080

# Terminal 2
airflow scheduler
```

The UI is available at **http://localhost:8080** (login: admin / admin).

## DAGs

| DAG ID | Schedule | Purpose |
|--------|----------|---------|
| `pulseiq_daily_insights` | `@daily` (midnight) | Runs insight agent, writes to `insights` table |

## Manual trigger

```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow dags trigger pulseiq_daily_insights
```

## Verify insights were written

```bash
psql $DATABASE_URL -c "SELECT id, insight_type, generated_at, LEFT(summary, 80) FROM insights ORDER BY generated_at DESC LIMIT 5;"
```

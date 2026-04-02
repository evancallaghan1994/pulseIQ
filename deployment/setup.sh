#!/bin/bash
# PulseIQ — VM Bootstrap Script
# Run as root (or with sudo) on a fresh Ubuntu 22.04 LTS server.
# Usage: bash setup.sh
set -euo pipefail

# ── Configuration — edit these before running ────────────────────────────────
REPO_URL="https://github.com/evancallaghan1994/pulseIQ.git"
APP_USER="pulseiq"
APP_DIR="/home/${APP_USER}/pulseiq"
DB_NAME="pulseiq"
DB_USER="pulseiq_user"
DB_PASSWORD="changeme"                                     # replace with a strong password
PYTHON_VERSION="3.12"
AIRFLOW_HOME="/home/${APP_USER}/airflow"
# ─────────────────────────────────────────────────────────────────────────────

echo "==> [1/10] Updating apt and installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl

echo "==> [2/10] Creating PostgreSQL database and user..."
systemctl start postgresql
sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};" 2>/dev/null || true

echo "==> [3/10] Creating app user and cloning repo..."
id -u ${APP_USER} &>/dev/null || useradd -m -s /bin/bash ${APP_USER}
sudo -u ${APP_USER} git clone ${REPO_URL} ${APP_DIR} 2>/dev/null || \
    (cd ${APP_DIR} && sudo -u ${APP_USER} git pull)

echo "==> [4/10] Copying .env to server..."
# Copy your local .env to the server before running this script:
#   scp .env root@<server-ip>:/home/pulseiq/pulseiq/.env
# This step assumes .env is already present at ${APP_DIR}/.env
if [ ! -f "${APP_DIR}/.env" ]; then
    echo "  WARNING: ${APP_DIR}/.env not found. Copy it with:"
    echo "    scp .env root@<server-ip>:${APP_DIR}/.env"
    echo "  Then re-run from step 5 onward."
    exit 1
fi

echo "==> [5/10] Creating virtualenv and installing dependencies..."
sudo -u ${APP_USER} python${PYTHON_VERSION} -m venv ${APP_DIR}/.venv
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/pip install --quiet --upgrade pip
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/pip install --quiet -r ${APP_DIR}/requirements.txt

echo "==> [6/10] Running data generation and load pipeline..."
cd ${APP_DIR}
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python -m data.generate.run_all
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python -m pipeline.load
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python -m pipeline.transform

echo "==> [7/10] Training ML models..."
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python -m models.lead_scoring.train
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python -m models.deal_risk.train

echo "==> [8/10] Ingesting RAG knowledge base..."
sudo -u ${APP_USER} ${APP_DIR}/.venv/bin/python rag/ingest.py

echo "==> [9/10] Initialising Airflow..."
sudo -u ${APP_USER} bash -c "
    export AIRFLOW_HOME=${AIRFLOW_HOME}
    ${APP_DIR}/.venv/bin/pip install --quiet 'apache-airflow==2.9.*' \
        --constraint 'https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt'
    ${APP_DIR}/.venv/bin/airflow db init
    ${APP_DIR}/.venv/bin/airflow users create \
        --role Admin --username admin --password admin \
        --firstname Evan --lastname Dev --email dev@example.com
"
# Copy DAGs into Airflow home
mkdir -p ${AIRFLOW_HOME}/dags
cp ${APP_DIR}/airflow/dags/daily_insights_dag.py ${AIRFLOW_HOME}/dags/

echo "==> [10/10] Starting Airflow webserver and scheduler..."
sudo -u ${APP_USER} bash -c "
    export AIRFLOW_HOME=${AIRFLOW_HOME}
    nohup ${APP_DIR}/.venv/bin/airflow webserver -p 8080 > ${AIRFLOW_HOME}/webserver.log 2>&1 &
    nohup ${APP_DIR}/.venv/bin/airflow scheduler > ${AIRFLOW_HOME}/scheduler.log 2>&1 &
"

echo ""
echo "==> Bootstrap complete."
echo "    Next steps:"
echo "    1. Start Streamlit:  see deployment/README.md"
echo "    2. Configure Nginx:  cp deployment/nginx.conf /etc/nginx/sites-available/pulseiq"
echo "    3. Open port 80:     ufw allow 'Nginx Full'"

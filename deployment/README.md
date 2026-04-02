# PulseIQ — Deployment Guide

## Infrastructure

| Resource | Spec | Cost |
|----------|------|------|
| VM | Digital Ocean Droplet — Ubuntu 22.04 LTS, 2 vCPU, 4 GB RAM, 80 GB SSD | ~$24/month |
| Database | PostgreSQL (installed on the same VM) | included |
| Domain | Optional — dashboard works via IP if no domain available | ~$12/year |

Alternatives: Hetzner CX22 (~$6/month), AWS EC2 t3.small (~$17/month), Linode 4GB (~$24/month).

---

## Step-by-step: Zero to Live URL

### 1. Provision the VM

1. Create a Droplet (or equivalent) with Ubuntu 22.04 LTS, minimum 4 GB RAM.
2. Add your SSH public key during creation.
3. Note the server IP address.

### 2. Copy your `.env` to the server

```bash
scp .env root@<server-ip>:/home/pulseiq/pulseiq/.env
```

The `.env` file is never committed to git. It must be present before the bootstrap script runs.

### 3. Run the bootstrap script

SSH into the server and run:

```bash
ssh root@<server-ip>
bash <(curl -s https://raw.githubusercontent.com/<your-org>/pulseiq/main/deployment/setup.sh)
```

Or clone manually and run:

```bash
git clone https://github.com/<your-org>/pulseiq.git
cd pulseiq
bash deployment/setup.sh
```

This script:
- Installs Python 3.12, PostgreSQL, Nginx, Git
- Creates the database and user
- Clones the repo and installs dependencies
- Runs data generation, loading, feature engineering
- Trains both ML models
- Ingests the RAG knowledge base
- Initialises Airflow and creates the admin user
- Starts Airflow webserver (port 8080) and scheduler

### 4. Start Streamlit

**Simple (nohup):**
```bash
cd /home/pulseiq/pulseiq
nohup .venv/bin/streamlit run dashboard/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > streamlit.log 2>&1 &
echo $! > streamlit.pid
```

**Robust (systemd service):**
```bash
# Copy the service file
cp deployment/pulseiq-streamlit.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pulseiq-streamlit
systemctl start pulseiq-streamlit
```

`deployment/pulseiq-streamlit.service`:
```ini
[Unit]
Description=PulseIQ Streamlit Dashboard
After=network.target postgresql.service

[Service]
User=pulseiq
WorkingDirectory=/home/pulseiq/pulseiq
ExecStart=/home/pulseiq/pulseiq/.venv/bin/streamlit run dashboard/app.py \
    --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 5. Configure Nginx

```bash
cp deployment/nginx.conf /etc/nginx/sites-available/pulseiq
ln -s /etc/nginx/sites-available/pulseiq /etc/nginx/sites-enabled/pulseiq
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ufw allow 'Nginx Full'
```

Edit `/etc/nginx/sites-available/pulseiq` and replace `yourdomain.com` with your domain or server IP.

### 6. Verify everything is running

```bash
# Streamlit
curl -s http://localhost:8501 | head -5

# Airflow
curl -s http://localhost:8080/health

# PostgreSQL
psql $DATABASE_URL -c "SELECT COUNT(*) FROM leads;"
```

Dashboard should be accessible at `http://<server-ip>` or `http://yourdomain.com`.

---

## Operations

### SSH into the server
```bash
ssh pulseiq@<server-ip>
cd pulseiq
```

### Check if Streamlit is running
```bash
# nohup approach
cat streamlit.pid | xargs ps -p

# systemd approach
systemctl status pulseiq-streamlit
```

### Check if Airflow is running
```bash
ps aux | grep "airflow webserver"
ps aux | grep "airflow scheduler"
# Logs
tail -f ~/airflow/webserver.log
tail -f ~/airflow/scheduler.log
```

### Restart Streamlit after a code change
```bash
# nohup approach
kill $(cat streamlit.pid)
nohup .venv/bin/streamlit run dashboard/app.py \
    --server.port 8501 --server.address 0.0.0.0 --server.headless true \
    > streamlit.log 2>&1 &
echo $! > streamlit.pid

# systemd approach
systemctl restart pulseiq-streamlit
```

### Manually trigger the insight agent
```bash
cd /home/pulseiq/pulseiq
.venv/bin/python -m agents.insight_agent
```

Or via Airflow CLI:
```bash
export AIRFLOW_HOME=~/airflow
.venv/bin/airflow dags trigger pulseiq_daily_insights
```

### Verify insights are being written
```bash
psql $DATABASE_URL -c \
  "SELECT id, insight_type, generated_at, LEFT(summary, 80) FROM insights ORDER BY generated_at DESC LIMIT 5;"
```

### Retrain models after data refresh
```bash
cd /home/pulseiq/pulseiq
.venv/bin/python -m data.generate.run_all
.venv/bin/python -m pipeline.load
.venv/bin/python -m pipeline.transform
.venv/bin/python -m models.lead_scoring.train
.venv/bin/python -m models.deal_risk.train
```

---

## Estimated Monthly Cost

| Item | Cost |
|------|------|
| VM (Digital Ocean 4GB) | $24 |
| Domain (optional, amortised) | ~$1 |
| Anthropic API (insight agent + RAG, light usage) | ~$2–5 |
| **Total** | **~$27–30/month** |

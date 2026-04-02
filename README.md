# PulseIQ — AI Sales Intelligence for Life Sciences

PulseIQ is a portfolio project demonstrating a production-quality B2B SaaS AI sales intelligence platform built for life sciences and biotech sales teams. It shows how modern AI and data engineering tools — XGBoost, Claude, ChromaDB, Airflow, and Streamlit — can be wired together into a coherent product that helps small sales teams prioritise leads, detect at-risk deals, answer product questions, and surface daily AI-generated insights without manual analysis.

> **Note:** This is a portfolio and concept project built to demonstrate data and AI engineering capabilities. All data is synthetically generated.

---

## Live Demo

**[http://64.23.140.104](http://64.23.140.104)**

---

## What It Does

### 🎯 Lead Scoring
An XGBoost classifier trained on historical conversion data scores every inbound lead by conversion probability. Sales reps see a ranked list with colour-coded priority flags, allowing them to focus effort on the leads most likely to close rather than working a flat list.

### ⚠️ Deal Risk Detection
A second XGBoost model scores active deals by the probability of going closed-lost. Deals with a risk score above 0.7 are flagged for intervention. The primary signal is engagement patterns — deals where contact has gone dark close at a significantly lower rate.

### 💬 Knowledge Assistant
A retrieval-augmented generation (RAG) pipeline backed by ChromaDB and Claude answers sales rep questions using internal knowledge base documents (pricing, objection handling, competitor battlecards, product FAQ). Answers are grounded in the documents — out-of-scope questions return a graceful "I don't know" rather than hallucinated content.

### 📊 Autonomous Insight Agent
An Airflow-scheduled agent runs daily, pulls a structured snapshot of business metrics (MRR trend, churn by tier, deal velocity, top acquisition channels, at-risk pipeline), and sends it to Claude to generate three prioritised, actionable insights. Insights are written to PostgreSQL and surfaced on the dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Database | PostgreSQL + SQLAlchemy ORM |
| ML models | XGBoost + MLflow experiment tracking and model registry |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local, free) |
| Vector store | ChromaDB |
| LLM | Claude API (claude-opus-4-6) via Anthropic SDK |
| Orchestration | Apache Airflow (LocalExecutor + SQLite metadata DB) |
| Dashboard | Streamlit + Plotly |
| Data generation | Faker + NumPy (synthetic, reproducible with SEED=42) |

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Lead Scoring** | Ranked lead table with scores, filters by source/industry/size, avg score by channel chart |
| **Deal Risk** | Active deal risk scores, high-risk alerts, scatter plot of risk vs days silent |
| **Knowledge Assistant** | Chat interface backed by RAG — asks questions, gets grounded answers with source attribution |
| **Insights** | AI-generated insight cards, live refresh button, MRR trend line, churn by tier bar chart |

---

## Project Structure

```
pulseiq/
├── data/
│   ├── generate/          # Synthetic data generators (leads, deals, engagement, customers, reps)
│   ├── knowledge_base/    # Markdown docs for RAG (pricing, objection handling, battlecards, FAQ)
│   └── raw/               # Generated CSVs (git-ignored)
├── db/                    # Schema, ORM models, connection, query helpers
├── pipeline/              # Load, transform (feature engineering), validate
├── models/
│   ├── lead_scoring/      # Features, train, predict
│   └── deal_risk/         # Features, train, predict
├── rag/                   # ingest.py (ChromaDB), query.py (Claude RAG)
├── agents/                # insight_agent.py
├── airflow/               # DAG + setup README
├── dashboard/             # Streamlit app.py + 4 pages + components
├── deployment/            # setup.sh, nginx.conf, README.md
└── tests/                 # pytest test suite (9 tests)
```

---

## Run Locally

### Prerequisites
- Python 3.12
- PostgreSQL running locally
- Anthropic API key

### Setup

```bash
# 1. Clone and create virtualenv
git clone https://github.com/<your-org>/pulseiq.git
cd pulseiq
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your DB credentials and ANTHROPIC_API_KEY

# 3. Create the database schema
psql $DATABASE_URL -f db/schema.sql

# 4. Generate synthetic data and load to PostgreSQL
python -m data.generate.run_all
python -m pipeline.load
python -m pipeline.transform

# 5. Train ML models
python -m models.lead_scoring.train
python -m models.deal_risk.train

# 6. Ingest knowledge base into ChromaDB
python rag/ingest.py

# 7. Generate initial insights
python -m agents.insight_agent

# 8. Launch the dashboard
streamlit run dashboard/app.py
# Open http://localhost:8501
```

### Run tests
```bash
pytest tests/ -v
```

---

## Deployment

See [`deployment/README.md`](deployment/README.md) for full step-by-step instructions to deploy on a Linux VM with Nginx and Airflow.

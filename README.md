# Crypto Volatility Monitoring Pipeline

## Overview

Docker-compose based data pipeline that ingests cryptocurrency market data, computes rolling volatility indicators, detects abnormal market conditions 
using statistical thresholds adjusted by sentiment data, generates alerts based on sentiment, volatility and regime changes and visualizes results through a live dashboard. 

---
## Business Problem

Cryptocurrency markets are highly volatile and strongly influenced by market sentiment.
Simple price tracking provides limited insight into risk events or abnormal behavior.

This project addresses the following questions:

- Was is price movement statistically abnormal, not just volatile?
- How does market sentiment (Fear & Greed Index) influence volatility risk?
- Can we detect early signals of extreme market conditions?

---

## Current status (implementation snapshot)

- [x] Extraction: CoinGecko + Fear & Greed fetchers exist (basic)
- [x] Transformation: market -> processed CSVs + analytics functions exist
- [x] Storage: Postgres schema + basic loaders exist
- [x] Alerts: alert generation + Slack notifier (optional) exist
- [x] Dashboard: Streamlit analytics dashboard
- [x] Orchestration: Airflow DAG exists for core flow (needs hardening)
- [ ] Reliability: retry/backoff and DLQ handling (partial / planned)
- [ ] Observability: structured logs and pipeline run metadata (planned)
- [ ] Production readiness: secrets handling, runbooks, and operational monitoring (planned)
- [ ] Monitoring: operational health dashboard (planned)

---

## Architecture
![ArchitectureDiagram.png](ArchitectureDiagram.png)

The pipeline:

1. Ingests real-time crypto market data from CoinGecko API (price, volume, market metrics)
2. Ingests sentiment data (Fear & Greed Index)
3. Engineers volatility and return-based features
4. Detects anomalies using rolling statistics
5. Adjusts anomaly thresholds dynamically based on market sentiment
6. Stores both raw data and analytical outputs in PostgreSQL
7. Creates alerts based on key changes in sentiment, regime or volatility
8. Displays analytics through a live dashboard
9. Orchestration handled by Apache Airflow


This allows downstream use cases such as:
- Risk alerts
- Monitoring dashboards
- Quantitative research
- Model training datasets

### Data Model

![DataModel.png](DataModel.png)

### Features

- Extraction of multiple coins with **dynamic fetch function**
- **Docker, Airflow Orchestration, PostgreSQL and dashboard**
- Historical backfill (90 days hourly data)
- Incremental ingestion
- Rolling volatility calculation
- Z-score anomaly detection
- Sentiment-aware thresholds
- Persistent analytics store
- Interactive analytics dashboard
- Scheduled execution
- Slack notification alerts

### Feature Matrix

| Area | Feature | Status |
|---|---|---:|
| Extraction | CoinGecko market fetcher | Implemented |
| Extraction | Fear & Greed fetcher | Implemented |
| Transformation | Rolling vol & features | Implemented |
| Storage | PostgreSQL loader & schema | Implemented |
| Orchestration | Airflow DAG (scheduled) | Partial |
| Reliability | Retry/backoff + DLQ | Partial/Planned |
| Observability | Structured logs & run metadata | Planned |
| Alerts | Slack notifications | Implemented |
| Dashboard | Streamlit visualizations | Implemented |
| Operational runbook | Runbook & DLQ replay | Planned |


### Data Sources
### Market Data
- CoinGecko API
- Metrics include:
  - coin_id
  - current_price_usd
  - market_cap_usd
  - total_volume_usd 
  - circulating_supply price_change_24h_pct
  - timestamp (UTC)

### Sentiment Data
- Fear & Greed Index API
- Used to:
  - Classify market sentiment
  - Adjust anomaly detection

---

## Analytic Logic
### Volatility Features

For each asset:

- Log or percentage returns
- Rolling standard deviation
- Z-score of returns

### Anomaly Detection

An observation is flagged as anomalous when:

|z_score| > threshold

The threshold is dynamically adjusted:
- Extreme Fear → lower threshold (higher sensitivity)
- Extreme Greed → moderately lower threshold
- Neutral → standard threshold

This reflects real-world risk behavior where sentiment amplifies volatility impact.

---

## Technology Stack
- Python 3.11
- Pandas
- REST APIs (CoinGecko + Fear & Greed Index)
- PostgreSQL (via Docker)  
- Git
- Streamlit + Plotly
- Apache Airflow

---

## Setup Instructions - Manual

### 1. Clone repository
```bash
git clone git@github.com:Jack-McG496/crypto-market-etl.git

cd crypto-market-etl
```
### 2. Create a virtual environment
```bash
python -m venv venv 
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### 3. Config and environment
```bash
# Create local env file
# Windows (PowerShell)
copy .env.example .env
# macOS / Linux
cp .env.example .env
# Then edit .env and fill API keys and secrets.
```

### 4. Local Postgres for integration tests
Start a local PostgreSQL instance and apply the schema before running integration tests.

```bash
# Windows (PowerShell)
docker compose up -d postgres

# Optional: if you want the project database to match the CI defaults
$env:TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/testdb"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "testdb"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "password"

# Apply schema
psql "postgresql://postgres:password@localhost:5432/testdb" -f sql/schema.sql
```

```bash
# macOS / Linux
export TEST_DATABASE_URL="postgresql://postgres:password@localhost:5432/testdb"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="testdb"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="password"

docker compose up -d postgres
psql "$TEST_DATABASE_URL" -f sql/schema.sql
```

### 5. Run integration tests
```bash
# Unit tests
pytest -m "not integration" tests/unit

# Integration tests (requires local Postgres and schema)
pytest -m integration tests/integration

# Smoke test
pytest --no-cov -m smoke tests/integration/test_smoke_pipeline.py -q
```

### 6.1. Run Dockerised Pipeline with Airflow
```bash
docker compose --profile airflow up -d
```
### 6.2. Run Dockerised Pipeline without Airflow
```bash
docker compose up -d postgres backfill pipeline dashboard
```

### Quickstart — Docker Compose (recommended)

1. Copy example env and set minimal values:

```powershell
copy .env.example .env
# Edit .env to set POSTGRES_PASSWORD and any API keys used by extractors
```

2. Start services (Airflow-enabled profile):

```powershell
docker compose --profile airflow up -d
```

3. Verify services are healthy:

```powershell
docker compose ps
```

4. Open Airflow UI at http://localhost:8080 and Streamlit dashboard at the configured port (default 8501).

### Quickstart — No-Airflow (developer / lightweight)

If you want to run the pipeline parts without starting Airflow (useful for development):

1. Start database and dashboard services:

```powershell
docker compose up -d postgres dashboard
```

2. Run the pipeline process container directly (one-shot ingestion + transform + load):

```powershell
docker compose up --no-deps --build pipeline
```

3. Or run the local runner (Python venv active):

```powershell
# from project root
python -m src.main --run-once
```

This runs an incremental fetch -> transform -> load cycle without Airflow.

## Example Dashboard

![Dashboard1.png](Dashboard1.png)

![Dashboard2.png](Dashboard2.png)

---

## Extending the Project
- Real-time streaming (Kafka)
- Machine learning anomaly detection
- Backtesting alert effectiveness
- Cloud Deployment

---

## Runbook — Inspecting failures, replaying DLQ, and re-running DAGs

This section gives short operational steps for common failure scenarios.

- **Inspect a failing run (Airflow)**:
  1. Open Airflow UI (http://localhost:8080) → DAGs → click the DAG → Browse Runs.
  2. Click the failing task, then open "Logs" to inspect the error and stack trace.
  3. Check container logs for the service running the task:

```powershell
docker compose logs --no-color --tail=200 pipeline
docker compose logs --no-color --tail=200 backfill
```

  4. If the failure looks like malformed input, inspect the dead-letter folder: `data/dead_letter/` for saved payloads and timestamps.

- **Replay DLQ (dead-letter files)**:
  1. Review files in `data/dead_letter/` and open to validate contents.
  2. For small batches, re-ingest via the backfill container which supports replaying from a file path:

```powershell
# example: replay a single dead-letter JSON
docker compose run --rm backfill python -m src.backfill --replay data/dead_letter/fear_greed_deadletter_20260919T104843Z.json
```

  3. For many files, use the included replay helper (or a short script) to iterate and re-submit; ensure you set `REPLAY_MODE=true` in `.env` to avoid duplicating alerts.

- **Re-run a DAG / Task**:
  - Via Airflow UI: Find the DAG run and use the "Clear" action on the task(s) to re-trigger downstream runs.
  - CLI (inside the airflow scheduler container):

```powershell
# trigger a DAG run
docker compose exec airflow-scheduler airflow dags trigger crypto_etl_dag

# re-run a single task (example)
docker compose exec airflow-scheduler airflow tasks clear crypto_etl_dag --start-date <date> --end-date <date> --downstream
```

Notes:
- Use the Airflow UI for one-off re-runs during development.
- Ensure database schema is applied before replays to avoid loader errors.

---

## What I Would Improve Next (interview honesty)

Short list of engineering and product improvements I would prioritize if continuing this project:

- Reliability & Observability: implement structured logging, metrics (Prometheus + Grafana), and end-to-end traces for key pipeline stages.
- Robust DLQ & Idempotency: make ingestion idempotent, add per-message retry policies, and a safe replay workflow with deduplication keys.
- Secrets & Deployment: move to a secrets manager (Vault/Cloud KMS) and containerize CI/CD for automated deployments.
- Testing & CI: add contract tests for extractors, integration tests against a managed test DB, and smoke tests that run in CI.
- Scalability: introduce stream processing (Kafka + Faust or Flink) to move from polling to event-driven ingestion where low-latency detection is required.
- Model improvements: evaluate ML-based anomaly detectors and backtest alert precision/recall against historical events.

If you'd like, I can also add a short `runbook.md` file with the above commands and templates for common Airflow CLI invocations.
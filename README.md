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

## Example Dashboard

![Dashboard1.png](Dashboard1.png)

![Dashboard2.png](Dashboard2.png)

---

## Extending the Project
- Real-time streaming (Kafka)
- Machine learning anomaly detection
- Backtesting alert effectiveness
- Cloud Deployment
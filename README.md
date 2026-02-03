# Crypto Market ETL Pipeline

## Overview
This project is a production-style data pipeline that ingests cryptocurrency market data and market sentiment indicators, transforms them into analytical features, and detects abnormal volatility patterns across multiple crypto assets.

The pipeline is designed to simulate a real-world risk monitoring system used by trading, risk, or analytics teams.

---
## Business Problem

Cryptocurrency markets are highly volatile and strongly influenced by market sentiment.
Simple price tracking provides limited insight into risk events or abnormal behavior.

This project addresses the following questions:

- When is price movement statistically abnormal, not just volatile?
- How does market sentiment (Fear & Greed Index) influence volatility risk?
- Can we detect early signals of extreme market conditions?

---

## Architecture
External APIs
   │
Extract Layer
   │
Transform Layer
   │
Analytics Layer
   │
PostgreSQL

The pipeline:

1. Ingests real-time crypto market data (price, volume, market metrics)
2. Ingests sentiment data (Fear & Greed Index)
3. Engineers volatility and return-based features
4. Detects anomalies using rolling statistics
5. Adjusts anomaly thresholds dynamically based on market sentiment
6. Stores both raw data and analytical outputs in PostgreSQL

This allows downstream use cases such as:
- Risk alerts
- Monitoring dashboards
- Quantitative research
- Model training datasets

### Features

- Extraction of multiple coins with **dynamic fetch function**
- Storage of raw JSON for reproducibility
- Data transformation using **pandas**
- Idempotent database inserts with **UPSERTs** on `(coin_id, timestamp)`  
- Fully **Dockerized PostgreSQL** database for portability
- Logging for debugging and pipeline monitoring

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
- REST APIs
- PostgreSQL (via Docker)  
- Git

---

## Setup Instructions

### 1. Clone repository
git clone git@github.com:Jack-McG496/crypto-portfolio.git

cd crypto-market-etl

### 2. Create a virtual environment
1. python -m venv venv 
2. venv\Scripts\activate      # Windows
3. source venv/bin/activate   # Mac/Linux

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Start PostgreSQL with Docker
docker compose up -d

### 5. Apply Schema
Get-Content sql/schema.sql | docker exec -i crypto_postgres psql -U crypto -d crypto_db

### 6. Run pipeline
python -m src.main

#### Expected output:
1. Raw data: data/raw/
2. Processed CSV: data/processed/market_data_<timestamp>.csv
3. Logs: printed to console

---

## Extending the Pipeline
- Add more cryptocurrencies by passing their names to run_transform(["bitcoin", "ethereum", "dogecoin"])
- Add new APIs or data points by creating new extract functions
- Schedule ETL runs with cron or Windows Task Scheduler
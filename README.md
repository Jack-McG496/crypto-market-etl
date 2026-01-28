# Crypto Market ETL Pipeline

## Overview
This project is a **Python-based** end-to-end ETL pipeline that extracts cryptocurrency market data
(price, volume, market cap, sentiment, timestamp) from various API's, transforms it (cleaning, handling error values), loads it into a **PostgreSQL database**.

The pipeline extracts data from:

- **CoinGecko API** (prices, market cap, 24h volume)  
- **Crypto Fear & Greed Index**  

It then transforms the data into a clean format and loads it into a Postgres warehouse with **idempotent upserts**.

---

## Architecture
Extract → Transform → Load

CoinGecko and Fear & Greed Index API's (Raw Data JSON) → panda data frames → PostgreSQL DB

### Features

- Extraction of multiple coins with **dynamic fetch function**
- Storage of raw JSON for reproducibility
- Data transformation using **pandas**
- Idempotent database inserts with **UPSERTs** on `(coin_id, timestamp)`  
- Fully **Dockerized PostgreSQL** database for portability
- Logging for debugging and pipeline monitoring

### Core market fields:
- coin_id 
- current_price_usd
- market_cap_usd
- total_volume_usd 
- circulating_supply price_change_24h_pct
- timestamp (UTC)

---

## Tech Stack
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
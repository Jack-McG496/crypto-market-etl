# Crypto Market ETL & Analysis

## Overview
An end-to-end ETL pipeline that collects cryptocurrency market data
(price, volume, market cap, sentiment) from API's, prepares it (cleaning, handling erronious values), optimises for analysis.

## Data Sources
- CoinGecko API
- Crypto Fear & Greed Index
- Key News

## Architecture
Extract → Transform → Load

## Metrics Collected
- Price (OHLC)
- Trading Volume
- Market Cap
- Fear & Greed Index
- Volatility (derived)
- Headline news
### Core market fields:
- coin_id 
  symbol 
  name timestamp (UTC)
  current_price_usd market_cap_usd 
  total_volume_usd 
  circulating_supply price_change_24h_pct

## Tech Stack
- Python
- Pandas
- SQLite
- REST APIs

## How to Run
Instructions coming soon.

CREATE TABLE IF NOT EXISTS market_data (
    coin_id TEXT NOT NULL,
    price_usd NUMERIC,
    volume_24h NUMERIC,
    market_cap NUMERIC,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (coin_id, timestamp_utc)
);

CREATE TABLE IF NOT EXISTS fear_greed_index (
    value INTEGER,
    classification TEXT,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

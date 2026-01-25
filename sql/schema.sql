CREATE TABLE IF NOT EXISTS market_data (
    coin TEXT NOT NULL,
    price_usd NUMERIC,
    volume_24h NUMERIC,
    market_cap NUMERIC,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fear_greed_index (
    value INTEGER,
    classification TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

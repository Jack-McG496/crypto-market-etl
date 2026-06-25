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

CREATE TABLE IF NOT EXISTS volatility_alerts (
    coin_id TEXT NOT NULL,

    -- Analytics metrics
    z_score NUMERIC NOT NULL,
    threshold NUMERIC NOT NULL,

    -- Sentiment context
    sentiment_score INTEGER NOT NULL,
    sentiment_label TEXT NOT NULL,

    -- Alert decision
    is_anomalous BOOLEAN NOT NULL,
    returns NUMERIC,
    rolling_std NUMERIC;

    -- Metadata
    timestamp_utc TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (coin_id, timestamp_utc)
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    coin_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analytics_timestamp TIMESTAMP NOT NULL
);

-- =========================
-- INDEXES (IMPORTANT)
-- =========================

CREATE INDEX IF NOT EXISTS idx_volatility_alerts_anomalous ON volatility_alerts (is_anomalous, timestamp_utc);



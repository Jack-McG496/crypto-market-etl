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

CREATE TABLE volatility_alerts (
    coin_id TEXT NOT NULL,
    timestamp_utc TIMESTAMP NOT NULL,

    -- features
    returns NUMERIC,
    rolling_std NUMERIC,
    z_score NUMERIC,

    -- model parameters
    threshold NUMERIC,

    -- sentiment context
    sentiment_score INTEGER,
    sentiment_label TEXT,

    -- outputs
    is_anomalous BOOLEAN,
    volatility_regime TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (coin_id, timestamp_utc)
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    coin_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analytics_timestamp TIMESTAMP NOT NULL,
    ADD CONSTRAINT constraint_conflict UNIQUE (coin_id, created_at)
);
ALTER TABLE alerts
ADD COLUMN notified BOOLEAN DEFAULT FALSE;

-- =========================
-- INDEXES (IMPORTANT)
-- =========================

CREATE INDEX IF NOT EXISTS idx_volatility_alerts_anomalous ON volatility_alerts (is_anomalous, timestamp_utc);
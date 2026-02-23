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

CREATE INDEX IF NOT EXISTS idx_volatility_alerts_anomalous
ON volatility_alerts (is_anomalous, timestamp_utc);



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

CREATE INDEX IF NOT EXISTS idx_volatility_alerts_anomalous
ON volatility_alerts (is_anomalous, timestamp_utc);



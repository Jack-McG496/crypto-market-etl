CREATE TABLE IF NOT EXISTS volatility_alerts (
    coin_id TEXT NOT NULL,
    z_score NUMERIC,
    threshold NUMERIC,
    sentiment_score INTEGER,
    sentiment_label TEXT,
    timestamp_utc TIMESTAMP NOT NULL,
    PRIMARY KEY (coin_id, timestamp_utc)
);

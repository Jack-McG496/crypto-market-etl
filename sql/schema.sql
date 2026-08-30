CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    dag_run TEXT NOT NULL,
    start_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_ts TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'running',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market_data (
    coin_id TEXT NOT NULL,
    price_usd NUMERIC,
    volume_24h NUMERIC,
    market_cap NUMERIC,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT,
    run_id INTEGER,
    PRIMARY KEY (coin_id, timestamp_utc),
    CONSTRAINT fk_market_data_run FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

CREATE TABLE IF NOT EXISTS fear_greed_index (
    value INTEGER,
    classification TEXT,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS volatility_alerts (
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
    notified BOOLEAN DEFAULT FALSE,
    CONSTRAINT constraint_conflict UNIQUE (coin_id, created_at)
);

CREATE TABLE IF NOT EXISTS task_runs (
    id SERIAL PRIMARY KEY,
    task_name TEXT NOT NULL,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(run_id),
    start_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_ts TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'running',
    attempts INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE OR REPLACE VIEW run_metadata AS
SELECT
    id,
    task_name,
    run_id,
    start_ts AS start,
    end_ts AS end,
    status,
    attempts
FROM task_runs;

CREATE TABLE IF NOT EXISTS dead_letter_events (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    stage TEXT NOT NULL,
    payload JSONB NOT NULL,
    error TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_id INTEGER REFERENCES pipeline_runs(run_id)
);

-- =========================
-- INDEXES (IMPORTANT)
-- =========================

CREATE INDEX IF NOT EXISTS idx_volatility_alerts_anomalous ON volatility_alerts (is_anomalous, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_market_data_run_id ON market_data (run_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_run_id ON task_runs (run_id, status);
CREATE INDEX IF NOT EXISTS idx_dead_letter_events_run_id ON dead_letter_events (run_id, created_at);
import os
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import psycopg2
import pytest

from src.utils.db import get_connection


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration requiring external services"
    )
    config.addinivalue_line(
        "markers",
        "smoke: mark test as a minimal end-to-end pipeline smoke test using the test database"
    )


def _ensure_test_schema(database_url: str):
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip("/") or "postgres"
    admin_url = database_url.rsplit("/", 1)[0] + "/postgres"

    admin_conn = psycopg2.connect(admin_url)
    try:
        with admin_conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')
        admin_conn.commit()
    finally:
        admin_conn.close()

    conn = get_connection(database_url)
    try:
        schema_sql = (Path(__file__).resolve().parents[1] / "sql" / "schema.sql").read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="function")
def db_transaction(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("BEGIN")
    yield db_connection
    db_connection.rollback()
    cursor.close()


@pytest.fixture(scope="session")
def database_url():
    return os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def db_connection(database_url):
    if not database_url:
        pytest.skip("Skipping integration tests because TEST_DATABASE_URL is not set")

    _ensure_test_schema(database_url)
    conn = get_connection(database_url)
    yield conn
    conn.close()

@pytest.fixture
def sample_market_df():

    return pd.DataFrame({
        "coin_id": ["btc"] * 20,
        "timestamp_utc": pd.date_range("2026-01-01", periods=20, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

@pytest.fixture
def sample_history_df():

    return pd.DataFrame({
        "coin_id": ["btc"] * 60,
        "timestamp_utc": pd.date_range("2026-01-01", periods=60, freq="h"),
        "price_usd": [100, 110, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111,
                      100, 130, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111,
                      100, 140, 120, 118, 130, 101, 111, 121, 119, 131, 110, 120, 150, 138, 160, 121, 151, 141, 129, 111]
    })

@pytest.fixture
def sample_raw_json_coingecko():

    return {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_data": {
            "current_price": {
                "usd": 80445
            },
            "market_cap": {
                "usd": 1805359545455
            },
            "total_volume": {
                "usd": 35347384019
            },
            "circulating_supply": 19974862.0,
            "price_change_percentage_24h": {
                "usd": -0.16067
            }
        }
    }

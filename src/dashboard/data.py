import pandas as pd
import psycopg2
import streamlit as st
from src.config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()

    market_query = """
        SELECT *
        FROM market_data
        ORDER BY timestamp_utc;
    """

    analytics_query = """
        SELECT *
        FROM volatility_alerts
        ORDER BY timestamp_utc;
    """

    alert_query = """
        SELECT *
        FROM alerts
        ORDER BY created_at DESC
        LIMIT 200;
    """

    market_df = pd.read_sql(market_query, conn)
    analytics_df = pd.read_sql(analytics_query, conn)
    alert_df = pd.read_sql(alert_query, conn)

    conn.close()

    if "timestamp_utc" in market_df.columns:
        market_df["timestamp_utc"] = pd.to_datetime(market_df["timestamp_utc"], utc=True)

    if "timestamp_utc" in analytics_df.columns:
        analytics_df["timestamp_utc"] = pd.to_datetime(analytics_df["timestamp_utc"], utc=True)

    if "created_at" in alert_df.columns:
        alert_df["created_at"] = pd.to_datetime(alert_df["created_at"], utc=True)

    return market_df, analytics_df, alert_df


def filter_dashboard_data(
    market_df: pd.DataFrame,
    analytics_df: pd.DataFrame,
    alert_df: pd.DataFrame,
    coin: str,
    time_window: str,
    severities: list[str] | None = None,
):
    if coin:
        market_df = market_df[market_df["coin_id"] == coin]
        analytics_df = analytics_df[analytics_df["coin_id"] == coin]
        alert_df = alert_df[alert_df["coin_id"] == coin]

    if severities:
        alert_df = alert_df[alert_df["severity"].isin(severities)]

    if time_window != "All":
        window_map = {"24h": "24h", "7d": "7d", "30d": "30d"}
        cutoff = pd.Timestamp.utcnow() - pd.Timedelta(window_map[time_window])
        market_df = market_df[market_df["timestamp_utc"] >= cutoff]
        analytics_df = analytics_df[analytics_df["timestamp_utc"] >= cutoff]
        alert_df = alert_df[alert_df["created_at"] >= cutoff]

    return market_df, analytics_df, alert_df
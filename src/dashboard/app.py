import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px
from src.config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
load_dotenv()

st.set_page_config(page_title="Crypto Volatility Monitor", layout="wide")

# -----------------------------
# DB CONNECTION
# -----------------------------
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
        LIMIT 100;
    """

    market_df = pd.read_sql(market_query, conn)
    analytics_df = pd.read_sql(analytics_query, conn)
    alert_df = pd.read_sql(alert_query, conn)

    conn.close()

    market_df["timestamp_utc"] = pd.to_datetime(market_df["timestamp_utc"])
    analytics_df["timestamp_utc"] = pd.to_datetime(analytics_df["timestamp_utc"])

    return market_df, analytics_df, alert_df


market_df, analytics_df, alert_df = load_data()

# -----------------------------
# SIDEBAR
# -----------------------------
coins = market_df["coin_id"].unique()

selected_coin = st.sidebar.selectbox(
    "Select Coin",
    coins
)

# filter data
market = market_df[market_df["coin_id"] == selected_coin]
analytics = analytics_df[analytics_df["coin_id"] == selected_coin]

# -----------------------------
# TITLE
# -----------------------------
st.title("📈 Crypto Volatility Monitoring Dashboard")

# -----------------------------
# PRICE CHART
# -----------------------------
st.subheader("Price (USD)")

fig_price = px.line(
    market,
    x="timestamp_utc",
    y="price_usd",
)

st.plotly_chart(fig_price, use_container_width=True)

# -----------------------------
# Z-SCORE CHART
# -----------------------------
st.subheader("Volatility Z-Score")

fig_z = px.line(
    analytics,
    x="timestamp_utc",
    y="z_score",
)

fig_z.add_hline(
    y=analytics["threshold"].iloc[-1],
    line_dash="dash"
)

fig_z.add_hline(
    y=-analytics["threshold"].iloc[-1],
    line_dash="dash"
)

# highlight anomalies
anomalies = analytics[analytics["is_anomalous"] == True]

fig_z.add_scatter(
    x=anomalies["timestamp_utc"],
    y=anomalies["z_score"],
    mode="markers",
    name="Anomaly",
)

st.plotly_chart(fig_z, use_container_width=True)

# -----------------------------
# Multi-Coin Comparison
# -----------------------------
st.subheader("Comparison")

fig_compare = px.line(
    analytics_df,
    x="timestamp_utc",
    y="z_score",
    color="coin_id"
)

st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# Recent Alerts Panel
# -----------------------------
st.subheader("🚨 Recent Alerts")
st.dataframe(alert_df)

alert_counts = (
    alert_df
    .groupby("severity")
    .size()
    .reset_index(name="count")
)

st.dataframe(alert_counts)

alert_type_counts = (
    alert_df
    .groupby("alert_type")
    .size()
    .reset_index(name="count")
)
st.dataframe(alert_type_counts)

coin_counts = (
    alert_df
    .groupby("coin_id")
    .size()
    .reset_index(name="count")
)
st.dataframe(coin_counts)

alert_summary = (
    alert_df
    .groupby(["coin_id", "severity"])
    .size()
    .reset_index(name="count")
)
st.dataframe(alert_summary)

alert_df["created_at"] = pd.to_datetime(alert_df["created_at"])

trend = (
    alert_df
    .groupby(pd.Grouper(key="created_at", freq="D"))
    .size()
    .reset_index(name="count")
)
st.dataframe(trend)
# -----------------------------
# Regime Timeline Chart
# -----------------------------
fig_regime = px.scatter(
    analytics_df,
    x="timestamp_utc",
    y="coin_id",
    color="volatility_regime",
    title="Volatility Regime Timeline"
)

regime_colors = {
    "CALM": "#d4edda",
    "NORMAL": "#fff3cd",
    "HIGH": "#ffe5b4",
    "EXTREME": "#f8d7da",
}

for i in range(len(analytics_df) - 1):
    regime = analytics_df["volatility_regime"].iloc[i]

    fig_regime.add_vrect(
        x0=analytics_df["timestamp_utc"].iloc[i],
        x1=analytics_df["timestamp_utc"].iloc[i + 1],
        fillcolor=regime_colors.get(regime, "white"),
        opacity=0.25,
        line_width=0,
    )

st.plotly_chart(fig_regime, use_container_width=True)


# -----------------------------
# SENTIMENT PANEL
# -----------------------------
if not analytics.empty:
    latest = analytics.iloc[-1]

    col1, col2, col3 = st.columns(3)

    col1.metric("Sentiment Score", latest["sentiment_score"])
    col2.metric("Sentiment Label", latest["sentiment_label"])
    col3.metric("Threshold Used", latest["threshold"])

    st.subheader("Market Regime")

    regime = latest["volatility_regime"]

    if regime == "Calm":
        st.success("🟢 Calm Market")
    elif regime == "Elevated":
        st.warning("🟡 Elevated Volatility")
    elif regime == "High":
        st.warning("🟠 High Volatility")
    else:
        st.error("🔴 Extreme Volatility")

    latest_z = latest["z_score"]

    if abs(latest_z) > latest["threshold"]:
        st.error("⚠️ Market in abnormal volatility regime")
    else:
        st.success("✅ Market volatility normal")


# -----------------------------
# RAW DATA VIEW
# -----------------------------
with st.expander("View Latest Alerts"):
    st.dataframe(analytics.tail(50))

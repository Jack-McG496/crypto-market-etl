import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

st.set_page_config(page_title="Crypto Volatility Monitor", layout="wide")

# -----------------------------
# DB CONNECTION
# -----------------------------
def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "crypto_db"),
        user=os.getenv("POSTGRES_USER", "crypto"),
        password=os.getenv("POSTGRES_PASSWORD", "crypto"),
    )


@st.cache_data(ttl=60)
def load_data():
    conn = get_connection()

    market_query = """
        SELECT *
        FROM market_data
        ORDER BY timestamp_utc;
    """

    alerts_query = """
        SELECT *
        FROM volatility_alerts
        ORDER BY timestamp_utc;
    """

    market_df = pd.read_sql(market_query, conn)
    alerts_df = pd.read_sql(alerts_query, conn)

    conn.close()

    market_df["timestamp_utc"] = pd.to_datetime(market_df["timestamp_utc"])
    alerts_df["timestamp_utc"] = pd.to_datetime(alerts_df["timestamp_utc"])

    return market_df, alerts_df


market_df, alerts_df = load_data()

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
alerts = alerts_df[alerts_df["coin_id"] == selected_coin]

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
    alerts,
    x="timestamp_utc",
    y="z_score",
)

fig_z.add_hline(
    y=alerts["threshold"].iloc[-1],
    line_dash="dash"
)

fig_z.add_hline(
    y=-alerts["threshold"].iloc[-1],
    line_dash="dash"
)

# highlight anomalies
anomalies = alerts[alerts["is_anomalous"] == True]

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
    alerts_df,
    x="timestamp_utc",
    y="z_score",
    color="coin_id"
)

st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# Recent Alerts Panel
# -----------------------------
recent_alerts = alerts_df[
    alerts_df["is_anomalous"] == True
].sort_values("timestamp_utc", ascending=False).head(10)

st.subheader("🚨 Recent Volatility Alerts")
st.dataframe(recent_alerts)


# -----------------------------
# SENTIMENT PANEL
# -----------------------------
if not alerts.empty:
    latest = alerts.iloc[-1]

    col1, col2, col3 = st.columns(3)

    col1.metric("Sentiment Score", latest["sentiment_score"])
    col2.metric("Sentiment Label", latest["sentiment_label"])
    col3.metric("Threshold Used", latest["threshold"])

    latest_z = latest["z_score"]

    if abs(latest_z) > latest["threshold"]:
        st.error("⚠️ Market in abnormal volatility regime")
    else:
        st.success("✅ Market volatility normal")

# -----------------------------
# RAW DATA VIEW
# -----------------------------
with st.expander("View Latest Alerts"):
    st.dataframe(alerts.tail(50))

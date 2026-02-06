import streamlit as st
import pandas as pd
import psycopg2
import os


# -----------------------
# DB Connection
# -----------------------

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "crypto_db"),
        user=os.getenv("POSTGRES_USER", "crypto"),
        password=os.getenv("POSTGRES_PASSWORD", "crypto"),
    )


# -----------------------
# Load Data
# -----------------------

@st.cache_data(ttl=60)
def load_data():

    query = """
    SELECT
        coin_id,
        z_score,
        threshold,
        sentiment_score,
        sentiment_label,
        is_anomalous,
        timestamp_utc
    FROM volatility_alerts
    ORDER BY timestamp_utc DESC
    LIMIT 5000;
    """

    conn = get_connection()

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# -----------------------
# App UI
# -----------------------

st.set_page_config(
    page_title="Crypto Volatility Monitor",
    layout="wide"
)

st.title("📊 Crypto Volatility Monitoring Dashboard")

df = load_data()


# -----------------------
# Sidebar Filters
# -----------------------

st.sidebar.header("Filters")

coins = st.sidebar.multiselect(
    "Select Coins",
    options=df["coin_id"].unique(),
    default=df["coin_id"].unique()
)

show_anomalies = st.sidebar.checkbox(
    "Show Only Anomalies",
    value=False
)


filtered = df[df["coin_id"].isin(coins)]

if show_anomalies:
    filtered = filtered[filtered["is_anomalous"] == True]


# -----------------------
# Metrics
# -----------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Records",
    len(filtered)
)

col2.metric(
    "Anomalies",
    filtered["is_anomalous"].sum()
)

col3.metric(
    "Avg Z-Score",
    round(filtered["z_score"].mean(), 2)
)


# -----------------------
# Table
# -----------------------

st.subheader("Alert Records")

st.dataframe(
    filtered,
    use_container_width=True
)


# -----------------------
# Charts
# -----------------------

st.subheader("Z-Score Over Time")

for coin in coins:

    coin_df = filtered[filtered["coin_id"] == coin]

    st.line_chart(
        coin_df.set_index("timestamp_utc")["z_score"],
        height=300
    )

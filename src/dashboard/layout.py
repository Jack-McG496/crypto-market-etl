import streamlit as st
import plotly.express as px
import pandas as pd
from src.dashboard.constants import REGIME_COLORS


def render_page_header():
    st.title("📈 Crypto Volatility Monitoring Dashboard")
    st.markdown(
        """
        Monitor crypto price movement, volatility anomalies, regime changes and alerts in a single view.
        The layout is optimized for operational monitoring with a strong focus on status, trend detection and alerts.
        """
    )


def render_status_panel(market: pd.DataFrame, analytics: pd.DataFrame, alert_df: pd.DataFrame):
    last_market = market["timestamp_utc"].max() if not market.empty else None
    last_analytics = analytics["timestamp_utc"].max() if not analytics.empty else None
    active_alerts = len(alert_df)
    anomalies = int(analytics["is_anomalous"].sum()) if "is_anomalous" in analytics.columns and not analytics.empty else 0
    current_regime = analytics["volatility_regime"].iloc[-1] if not analytics.empty else "Unknown"

    col1, col2, col3, col4 = st.columns(4)
    last_market_str = (
        last_market.strftime("%Y-%m-%d %H:%M:%S %Z")
        if last_market is not None else "No data")
    last_analytics_str = (
        last_analytics.strftime("%Y-%m-%d %H:%M:%S %Z")
        if last_analytics is not None else "No data"
    )

    col1.metric("Last market row", last_market_str)
    col2.metric("Last analytics row", last_analytics_str)
    col3.metric("Active alerts", active_alerts)
    col4.metric("Anomalies", anomalies)

    if current_regime == "Extreme":
        st.error("🔴 Market regime: Extreme volatility")
    elif current_regime == "High":
        st.warning("🟠 Market regime: High volatility")
    elif current_regime == "Elevated":
        st.info("🟡 Market regime: Elevated volatility")
    elif current_regime == "Calm":
        st.success("🟢 Market regime: Calm")
    else:
        st.info("⚪ Market regime: Unknown")


def render_price_chart(market: pd.DataFrame):
    st.subheader("Price (USD)")
    if market.empty:
        st.warning("No market data available for the selected coin and timeframe.")
        return

    fig = px.line(
        market,
        x="timestamp_utc",
        y="price_usd",
        title="Price (USD)",
        labels={"timestamp_utc": "Timestamp", "price_usd": "Price (USD)"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def render_zscore_chart(analytics: pd.DataFrame):
    st.subheader("Volatility Z-Score")
    if analytics.empty:
        st.warning("No analytics data available for the selected coin and timeframe.")
        return

    fig = px.line(
        analytics,
        x="timestamp_utc",
        y="z_score",
        title="Volatility Z-Score",
        labels={"timestamp_utc": "Timestamp", "z_score": "Z-Score"},
    )

    threshold = analytics["threshold"].iloc[-1]
    fig.add_hline(y=threshold, line_dash="dash", annotation_text="Threshold", annotation_position="top left")
    fig.add_hline(y=-threshold, line_dash="dash")

    anomalies = analytics[analytics["is_anomalous"] == True]
    if not anomalies.empty:
        fig.add_scatter(
            x=anomalies["timestamp_utc"],
            y=anomalies["z_score"],
            mode="markers",
            marker=dict(color="red", size=8),
            name="Anomaly",
        )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_chart(analytics_df: pd.DataFrame):
    st.subheader("Coin Comparison")
    if analytics_df.empty:
        st.warning("No analytics data available for coin comparison.")
        return

    fig = px.line(
        analytics_df,
        x="timestamp_utc",
        y="z_score",
        color="coin_id",
        title="Volatility Z-Score Comparison",
        labels={"timestamp_utc": "Timestamp", "z_score": "Z-Score", "coin_id": "Coin"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def render_regime_timeline(analytics_df: pd.DataFrame):
    st.subheader("Volatility Regime Timeline")
    if analytics_df.empty:
        st.warning("No analytics data available for regime timeline.")
        return

    fig = px.scatter(
        analytics_df,
        x="timestamp_utc",
        y="coin_id",
        color="volatility_regime",
        title="Volatility Regime Timeline",
        labels={"timestamp_utc": "Timestamp", "coin_id": "Coin", "volatility_regime": "Regime"},
    )

    for i in range(len(analytics_df) - 1):
        regime = analytics_df["volatility_regime"].iloc[i]
        fig.add_vrect(
            x0=analytics_df["timestamp_utc"].iloc[i],
            x1=analytics_df["timestamp_utc"].iloc[i + 1],
            fillcolor=REGIME_COLORS.get(regime, "#ffffff"),
            opacity=0.20,
            line_width=0,
        )

    st.plotly_chart(fig, use_container_width=True)


def render_alert_panel(alert_df: pd.DataFrame):
    st.subheader("🚨 Recent Alerts")
    if alert_df.empty:
        st.info("No recent alerts to display.")
        return

    severity_counts = (
        alert_df.groupby("severity")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    st.markdown("**Alert severity distribution**")
    st.bar_chart(data=severity_counts.set_index("severity")["count"])

    st.markdown("**Latest alerts**")
    alert_table = alert_df.sort_values("created_at", ascending=False).head(20)
    st.dataframe(
        alert_table[["created_at", "coin_id", "alert_type", "severity", "message"]].reset_index(drop=True),
        use_container_width=True,
    )


def render_alert_trend(alert_df: pd.DataFrame):
    if alert_df.empty or "created_at" not in alert_df.columns:
        return

    trend = (
        alert_df.groupby(pd.Grouper(key="created_at", freq="D"))
        .size()
        .reset_index(name="count")
    )
    st.subheader("Alert trend")
    st.line_chart(trend.set_index("created_at")["count"])


def render_raw_data_expanders(
    market: pd.DataFrame, analytics: pd.DataFrame, alert_df: pd.DataFrame
):
    with st.expander("Market data (latest 50 rows)"):
        st.dataframe(market.sort_values("timestamp_utc", ascending=False).head(50))

    with st.expander("Analytics data (latest 50 rows)"):
        st.dataframe(analytics.sort_values("timestamp_utc", ascending=False).head(50))

    with st.expander("Alert data (latest 50 rows)"):
        st.dataframe(alert_df.sort_values("created_at", ascending=False).head(50))
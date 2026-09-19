
import pandas as pd
import plotly.express as px
import streamlit as st

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

    anomalies = analytics[analytics["is_anomalous"]]
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


def render_comparison_chart(
    analytics_df: pd.DataFrame,
    market_df: pd.DataFrame,
    coins: list[str] | None = None,
    metric: str = "Z-score",
    mode: str = "Overlap",
):
    st.subheader("Coin Comparison")
    if analytics_df.empty and market_df.empty:
        st.warning("No data available for comparison.")
        return

    # Filter by selected coins
    if coins:
        analytics = analytics_df[analytics_df["coin_id"].isin(coins)].copy()
        market = market_df[market_df["coin_id"].isin(coins)].copy()
    else:
        analytics = analytics_df.copy()
        market = market_df.copy()

    if metric == "Normalized Price":
    # Use market prices (not analytics). Require price and coin_id columns.
        if market.empty or "price_usd" not in market.columns:
            st.warning("Price data not available in market data for normalized price comparison.")
            return

        # compute normalized price per coin and ensure coin_id column exists
        norm_list = []
        for _coin, g in market.groupby("coin_id"):
            g = g.sort_values("timestamp_utc").copy()
            if g.empty or g["price_usd"].iloc[0] == 0:
                continue
            g = g.assign(norm_price=100.0 * g["price_usd"] / g["price_usd"].iloc[0])
            norm_list.append(g[["coin_id", "timestamp_utc", "norm_price"]])

        if not norm_list:
            st.info("No valid market rows for selected coins/time window.")
            return

        norm_df = pd.concat(norm_list, ignore_index=True)

        fig = px.line(
            norm_df,
            x="timestamp_utc",
            y="norm_price",
            color="coin_id",
            title="Normalized Price (base = 100)",
            labels={"norm_price": "Indexed price (100 = start)", "timestamp_utc": "Timestamp"},
        )
        fig.update_yaxes(title_text="Indexed Price")
    else:
        # Z-score comparison - source from analytics
        if analytics.empty or "z_score" not in analytics.columns:
            st.warning("Z-score not available in analytics for selected coins/time window.")
            return

        if mode == "Facets":
            fig = px.line(
                analytics.sort_values(["coin_id", "timestamp_utc"]),
                x="timestamp_utc",
                y="z_score",
                color="coin_id",
                facet_col="coin_id",
                facet_col_wrap=2,
                title="Z-score comparison (faceted by coin)",
                labels={"z_score": "Z-score", "timestamp_utc": "Timestamp"},
            )
            fig.update_yaxes(matches=None)
        else:  # Overlap
            fig = px.line(
                analytics.sort_values(["coin_id", "timestamp_utc"]),
                x="timestamp_utc",
                y="z_score",
                color="coin_id",
                title="Z-score comparison (overlap)",
                labels={"z_score": "Z-score", "timestamp_utc": "Timestamp"},
            )
            fig.update_yaxes(title_text="Z-score")

    fig.update_layout(hovermode="x unified", legend_title_text="Coin")
    st.plotly_chart(fig, use_container_width=True)


def render_regime_timeline(analytics_df: pd.DataFrame):
    st.subheader("Volatility Regime Timeline")
    if analytics_df.empty or "volatility_regime" not in analytics_df.columns or "timestamp_utc" not in analytics_df.columns:
        st.warning("No analytics data available for regime timeline.")
        return

    # Build contiguous segments per coin: start = current ts, end = next ts (or + small delta)
    df = analytics_df.sort_values(["coin_id", "timestamp_utc"]).reset_index(drop=True)
    segments = []
    for coin, g in df.groupby("coin_id"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            start = g.loc[i, "timestamp_utc"]
            end = g.loc[i + 1, "timestamp_utc"] if i + 1 < len(g) else start + pd.Timedelta(minutes=1)
            segments.append({
                "coin_id": coin,
                "start": start,
                "end": end,
                "volatility_regime": g.loc[i, "volatility_regime"]
            })

    seg_df = pd.DataFrame(segments)
    if seg_df.empty:
        st.info("Not enough analytics rows to build regime timeline.")
        return

    # Use consistent regime order and colors
    regime_order = ["Calm", "Elevated", "High", "Extreme"]
    color_map = REGIME_COLORS

    fig = px.timeline(
        seg_df,
        x_start="start",
        x_end="end",
        y="coin_id",
        color="volatility_regime",
        category_orders={"volatility_regime": regime_order},
        color_discrete_map=color_map,
        title="Volatility Regime Timeline (segments per coin)"
    )
    fig.update_yaxes(autorange="reversed")  # so first coin is on top
    fig.update_layout(showlegend=True, height=300 + 80 * seg_df["coin_id"].nunique())
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


def render_operational_panel(pipeline_df: pd.DataFrame, dlq_df: pd.DataFrame, alert_df: pd.DataFrame):
    st.subheader("Operational / Health")

    now = pd.Timestamp.utcnow()

    if pipeline_df.empty:
        st.info("No pipeline run data available (pipeline_runs table missing or empty).")
        return

    # Last successful run across pipelines
    if "status" in pipeline_df.columns and "ended_at" in pipeline_df.columns:
        success_mask = pipeline_df["status"].str.lower() == "success"
        last_success = pipeline_df.loc[success_mask, "ended_at"].max() if success_mask.any() else None
    else:
        last_success = None

    last_success_str = last_success.strftime("%Y-%m-%d %H:%M:%S %Z") if pd.notna(last_success) else "No successful runs"

    # Freshness lag: time since last successful run
    if pd.notna(last_success):
        lag = now - last_success
        # show in human readable
        lag_str = str(lag).split(".")[0]
    else:
        lag_str = "N/A"

    pending_alerts = len(alert_df) if alert_df is not None else 0

    # Recent failures
    recent_failures = pd.DataFrame()
    if "status" in pipeline_df.columns:
        fail_mask = pipeline_df["status"].str.lower().isin(["failed", "error"]) if not pipeline_df.empty else pd.Series(dtype=bool)
        recent_failures = pipeline_df[fail_mask].sort_values("started_at", ascending=False).head(10)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last successful run", last_success_str)
    c2.metric("Freshness lag", lag_str)
    c3.metric("Pending alerts", pending_alerts)
    c4.metric("Recent failures", len(recent_failures))

    if not recent_failures.empty:
        with st.expander("Recent pipeline failures (latest)"):
            cols = [c for c in ["pipeline_id", "run_id", "status", "started_at", "ended_at", "message"] if c in recent_failures.columns]
            st.dataframe(recent_failures[cols].reset_index(drop=True), use_container_width=True)


def render_dead_letter_view(dlq_df: pd.DataFrame):
    st.subheader("Dead Letter Queue (recent)")
    if dlq_df is None or dlq_df.empty:
        st.info("No dead-letter events found.")
        return

    df = dlq_df.copy()
    # Provide a short payload preview for quick triage
    if "payload" in df.columns:
        df["payload_preview"] = df["payload"].astype(str).str.slice(0, 200)
    elif "data" in df.columns:
        df["payload_preview"] = df["data"].astype(str).str.slice(0, 200)
    else:
        df["payload_preview"] = "(no payload column)"

    display_cols = [c for c in ["created_at", "event_type", "source", "payload_preview"] if c in df.columns]
    st.dataframe(df[display_cols].sort_values("created_at", ascending=False).head(50), use_container_width=True)


def render_replay_section():
    st.subheader("Replay Dead-Letter Events")
    st.markdown(
        """
        Manual replay instructions:

        - Inspect the dead-letter events above and identify the `run_id` or `event id` you want to replay.
        - Use the pipeline's CLI or admin UI to re-submit the payload to the ingestion topic or re-run the failed job.
        - Verify processing by checking `pipeline_runs` for a new successful run and the `market_data` table for expected output.

        For detailed guidance and examples, see the project docs: [Replaying Dead-Letter Events](README.md#replaying-dead-letter-events)
        """
    )

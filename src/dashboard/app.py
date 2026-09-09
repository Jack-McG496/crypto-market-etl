import streamlit as st
from src.dashboard.constants import TIME_WINDOW_OPTIONS
from src.dashboard.data import filter_dashboard_data, load_data
from src.dashboard.layout import (
    render_page_header,
    render_status_panel,
    render_price_chart,
    render_zscore_chart,
    render_comparison_chart,
    render_regime_timeline,
    render_alert_panel,
    render_alert_trend,
    render_raw_data_expanders,
    render_operational_panel,
    render_dead_letter_view,
    render_replay_section,
)

st.set_page_config(page_title="Crypto Volatility Monitor", layout="wide")

market_df, analytics_df, alert_df, pipeline_df, dlq_df = load_data()

if market_df.empty or analytics_df.empty:
    st.error("No market or analytics data available. Confirm that the pipeline is writing to the database.")
    st.stop()

coins = sorted(market_df["coin_id"].unique())
selected_coin = st.sidebar.selectbox("Select coin", coins)

time_window = st.sidebar.selectbox(
    "Time window",
    list(TIME_WINDOW_OPTIONS.keys()),
    index=list(TIME_WINDOW_OPTIONS.keys()).index("7d"),
    format_func=lambda key: TIME_WINDOW_OPTIONS[key],
)

available_severities = sorted(alert_df["severity"].dropna().unique())
selected_severities = st.sidebar.multiselect(
    "Alert severity",
    options=available_severities,
    default=available_severities,
)

market, analytics, alerts = filter_dashboard_data(
    market_df,
    analytics_df,
    alert_df,
    coin=selected_coin,
    time_window=time_window,
    severities=selected_severities,
)

# comparison datasets: same time window & severity filters, but no coin filter
market_cmp, analytics_cmp, alerts_cmp = filter_dashboard_data(
    market_df,
    analytics_df,
    alert_df,
    coin=None,
    time_window=time_window,
    severities=selected_severities,
)

compare_enabled = st.sidebar.checkbox("Enable coin comparison", value=False)
compare_metric = st.sidebar.selectbox("Compare metric", ["Z-score", "Normalized Price"])
compare_mode = st.sidebar.selectbox("Display mode", ["Overlap", "Facets"], index=0)
compare_coins = st.sidebar.multiselect(
    "Coins to compare",
    options=sorted(market_df["coin_id"].unique()),
    default=[selected_coin] if not compare_enabled else sorted(market_df["coin_id"].unique()),
    help="Select coins to include in the comparison (uses current time window)"
)

render_page_header()
render_status_panel(market, analytics, alerts)
render_operational_panel(pipeline_df, dlq_df, alerts)

# Dead-letter queue view (visible by default)
render_dead_letter_view(dlq_df)

# Replay instructions + docs link
render_replay_section()

left_col, right_col = st.columns([2, 1])

with left_col:
    render_price_chart(market)
    render_zscore_chart(analytics)

with right_col:
    render_alert_panel(alerts)
    render_alert_trend(alerts)

if compare_enabled:
    render_comparison_chart(
        analytics_df=analytics_cmp,
        market_df=market_cmp,
        coins=compare_coins,
        metric=compare_metric,
        mode=compare_mode,
    )
else:
    with st.expander("Coin comparison (disabled)"):
        st.write("Enable 'coin comparison' in the sidebar to see multi-coin comparisons (respects the selected timeframe).")

render_regime_timeline(analytics)

render_raw_data_expanders(market, analytics, alerts)
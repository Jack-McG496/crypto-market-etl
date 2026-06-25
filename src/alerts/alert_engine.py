import pandas as pd

def generate_alerts(df):
    filtered_df = df[df["is_anomalous"] == True]
    alert_df = pd.DataFrame()
    for ele in filtered_df:

        alert_df["coin_id"] = ele["coin_id"]
        alert_df["alert_type"] = "VOLATILITY"
        alert_df["severity"] = "WARNING"
        alert_df["message"] = "BTC volatility exceeded threshold" if ele["coin_id"] == "BTC" else "ETH volatility exceeded threshold"
        alert_df["analytics_timestamp"] = ele["timestamp_utc"]

    return alert_df

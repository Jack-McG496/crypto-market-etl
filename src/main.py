from extract.coingecko_api import fetch_coin_market_data, save_raw_json
from extract.fear_greed_api import fetch_fear_greed_index, save_raw_json as save_fg_json
from transform.market_data_transform import run_transform, save_processed_data


def run_coingecko():
    coins = ["bitcoin", "ethereum"]

    for coin in coins:
        data = fetch_coin_market_data(coin)
        save_raw_json(data, source_name=f"coingecko_{coin}")


def run_fear_greed():
    data = fetch_fear_greed_index(limit=1)
    save_fg_json(data)


def main():
    print("Starting ETL pipeline...")

    run_coingecko()
    run_fear_greed()
    df = run_transform(["bitcoin", "ethereum"])
    save_processed_data(df)

    print("ETL pipeline finished successfully.")


if __name__ == "__main__":
    main()

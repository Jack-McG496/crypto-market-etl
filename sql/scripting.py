import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="crypto_db",
    user="crypto",
    password="crypto"
)

df = pd.read_sql("SELECT * FROM market_data", conn)
print(df.head())

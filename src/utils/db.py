import os
import psycopg2


def get_connection():
    """
    Create and return a Postgres connection using env vars.
    """

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "crypto_db"),
        user=os.getenv("POSTGRES_USER", "crypto"),
        password=os.getenv("POSTGRES_PASSWORD", "crypto")
    )

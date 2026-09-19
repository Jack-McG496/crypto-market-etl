import os

import psycopg2

from src.config.settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def get_connection(database_url: str | None = None):
    """
    Create and return a Postgres connection using a DSN override or env vars.
    """
    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def get_db_dsn() -> str | None:
    return os.getenv("TEST_DATABASE_URL") or os.getenv("POSTGRES_DSN")

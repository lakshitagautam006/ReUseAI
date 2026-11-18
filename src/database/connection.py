
import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def get_connection():
    """Create and return a PostgreSQL database connection."""

    database_url = (os.getenv("DATABASE_URL") or "").strip()

    if not database_url or database_url.startswith("your_") or "username:password@" in database_url:
        raise ValueError("DATABASE_URL is not configured in .env")

    connect_kwargs = {}
    if "connect_timeout=" not in database_url:
        try:
            connect_timeout = max(1, int(os.getenv("DB_CONNECT_TIMEOUT", "5")))
        except ValueError:
            connect_timeout = 5
        connect_kwargs["connect_timeout"] = connect_timeout

    return psycopg.connect(database_url, **connect_kwargs)


def test_connection():
    """Test the PostgreSQL connection."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            return cur.fetchone()[0]

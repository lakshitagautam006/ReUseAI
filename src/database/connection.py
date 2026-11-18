
import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def get_connection():
    """Create and return a PostgreSQL database connection."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not configured in .env")

    return psycopg.connect(database_url)


def test_connection():
    """Test the PostgreSQL connection."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            return cur.fetchone()[0]

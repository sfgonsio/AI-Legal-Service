from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg


REPO_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = REPO_ROOT / "casecore-runtime" / ".env"


def load_environment() -> None:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f"Missing environment file: {ENV_PATH}")
    load_dotenv(ENV_PATH)


def get_database_url() -> str:
    load_environment()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is missing from casecore-runtime/.env")
    return db_url


def connect() -> dict:
    db_url = get_database_url()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("select current_database(), current_user, now();")
            row = cur.fetchone()
    return {
        "connected": True,
        "database": row[0],
        "user": row[1],
        "timestamp": str(row[2]),
    }


if __name__ == "__main__":
    print(connect())

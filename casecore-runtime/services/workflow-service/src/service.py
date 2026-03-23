from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row


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


def create_run(run_type: str, status: str, input_reference: str | None = None, output_reference: str | None = None) -> dict:
    db_url = get_database_url()

    run_id = str(uuid4())
    started_at = datetime.now(timezone.utc)

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                insert into workflow_runs (id, run_type, status, started_at, completed_at, input_reference, output_reference)
                values (%s, %s, %s, %s, %s, %s, %s)
                returning id, run_type, status, started_at, completed_at, input_reference, output_reference
                """,
                (
                    run_id,
                    run_type,
                    status,
                    started_at,
                    None,
                    input_reference,
                    output_reference,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return dict(row)


def get_run(run_id: str) -> dict | None:
    db_url = get_database_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select id, run_type, status, started_at, completed_at, input_reference, output_reference
                from workflow_runs
                where id = %s
                """,
                (run_id,),
            )
            row = cur.fetchone()

    return dict(row) if row else None

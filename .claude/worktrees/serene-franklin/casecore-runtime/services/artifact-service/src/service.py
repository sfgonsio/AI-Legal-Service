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


def store_artifact(artifact_type: str, status: str, payload: dict, created_by: str | None = None, source_reference: str | None = None, hash_value: str | None = None) -> dict:
    db_url = get_database_url()

    artifact_id = str(uuid4())
    created_at = datetime.now(timezone.utc)

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                insert into artifacts (id, artifact_type, status, payload, created_at, created_by, source_reference, hash)
                values (%s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                returning id, artifact_type, status, payload, created_at, created_by, source_reference, hash
                """,
                (
                    artifact_id,
                    artifact_type,
                    status,
                    psycopg.types.json.Json(payload),
                    created_at,
                    created_by,
                    source_reference,
                    hash_value,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return dict(row)


def get_artifact(artifact_id: str) -> dict | None:
    db_url = get_database_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select id, artifact_type, status, payload, created_at, created_by, source_reference, hash
                from artifacts
                where id = %s
                """,
                (artifact_id,),
            )
            row = cur.fetchone()

    return dict(row) if row else None

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


def record_audit_event(event_type: str, entity_type: str, entity_id: str | None, payload: dict, actor: str, run_id: str | None) -> dict:
    db_url = get_database_url()

    audit_id = str(uuid4())
    created_at = datetime.now(timezone.utc)

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                insert into audit_log (id, event_type, entity_type, entity_id, payload, created_at, actor, run_id)
                values (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                returning id, event_type, entity_type, entity_id, payload, created_at, actor, run_id
                """,
                (
                    audit_id,
                    event_type,
                    entity_type,
                    entity_id,
                    psycopg.types.json.Json(payload),
                    created_at,
                    actor,
                    run_id,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return dict(row)


def get_audit_for_target(entity_type: str, entity_id: str) -> list[dict]:
    db_url = get_database_url()

    with psycopg.connect(db_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select id, event_type, entity_type, entity_id, payload, created_at, actor, run_id
                from audit_log
                where entity_type = %s and entity_id::text = %s
                order by created_at asc
                """,
                (entity_type, entity_id),
            )
            rows = cur.fetchall()

    return [dict(r) for r in rows]

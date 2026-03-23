from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME_ROOT = HERE.parents[2]

sys.path.insert(0, str(RUNTIME_ROOT / "artifact-service" / "src"))
sys.path.insert(0, str(RUNTIME_ROOT / "audit-service" / "src"))

from service import store_artifact  # type: ignore
from service import record_audit_event  # type: ignore


def request_promotion(artifact_id: str, actor_id: str, reason: str) -> dict:
    review_payload = {
        "artifact_id": artifact_id,
        "actor_id": actor_id,
        "reason": reason,
        "review_status": "pending",
        "request_type": "promotion_request",
    }

    stored = store_artifact(
        artifact_type="REVIEW_REQUEST",
        status="pending",
        payload=review_payload,
        created_by=actor_id,
        source_reference=f"artifact:{artifact_id}",
        hash_value=None,
    )

    audit = record_audit_event(
        event_type="promotion_requested",
        entity_type="artifact",
        entity_id=artifact_id,
        payload={
            "review_request_id": stored["id"],
            "reason": reason,
            "actor_id": actor_id,
        },
        actor=actor_id,
        run_id=None,
    )

    return {
        "accepted": True,
        "review_request": stored,
        "audit_event": audit,
        "status": "pending_review",
    }

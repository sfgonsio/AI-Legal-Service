from src.utils.ids import new_id
from src.utils.timestamps import utc_now_iso


def make_audit_event(
    *,
    event_type: str,
    case_id: str,
    correlation_id: str,
    payload: dict,
) -> dict:
    return {
        "event_id": new_id(),
        "event_type": event_type,
        "case_id": case_id,
        "timestamp": utc_now_iso(),
        "correlation_id": correlation_id,
        "payload": payload,
    }


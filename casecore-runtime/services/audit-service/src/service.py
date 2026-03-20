def record_audit_event(event: dict) -> dict:
    required = ["event_id", "timestamp", "actor_id", "action", "target_id", "run_id"]
    missing = [k for k in required if k not in event]
    if missing:
        raise ValueError(f"Missing audit fields: {missing}")
    return {"recorded": True, "event": event}

def get_audit_for_target(target_id: str) -> dict:
    return {"target_id": target_id, "events": [], "status": "scaffold"}

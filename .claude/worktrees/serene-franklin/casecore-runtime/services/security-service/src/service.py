def authorize(actor_id: str, action: str, target_id: str) -> dict:
    return {"authorized": True, "actor_id": actor_id, "action": action, "target_id": target_id}

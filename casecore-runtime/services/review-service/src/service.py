def request_promotion(artifact_id: str, actor_id: str, reason: str) -> dict:
    return {
        "accepted": False,
        "artifact_id": artifact_id,
        "actor_id": actor_id,
        "reason": reason,
        "status": "scaffold_requires_runtime_enforcement"
    }

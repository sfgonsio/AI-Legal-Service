def get_artifact(artifact_id: str) -> dict:
    return {"artifact_id": artifact_id, "status": "scaffold"}

def store_artifact(payload: dict) -> dict:
    return {"accepted": True, "artifact": payload}

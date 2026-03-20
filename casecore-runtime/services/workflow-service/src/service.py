def create_run(matter_id: str, initiated_by: str) -> dict:
    return {
        "accepted": True,
        "run_id": "RUN-SVC-001",
        "matter_id": matter_id,
        "initiated_by": initiated_by,
        "status": "created"
    }

def get_run(run_id: str) -> dict:
    return {"run_id": run_id, "status": "scaffold"}

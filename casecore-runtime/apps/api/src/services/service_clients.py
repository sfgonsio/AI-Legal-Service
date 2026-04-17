class PersistenceServiceClient:
    def create_case(self, payload: dict) -> dict:
        return payload

    def get_case(self, case_id: str) -> dict:
        return {
            "case_id": case_id,
            "title": "Sample Case",
            "case_type": "Civil",
            "jurisdiction": "CA",
            "perspective": "Plaintiff",
            "status": "OPEN",
        }


class AuditServiceClient:
    def write_event(self, payload: dict) -> dict:
        return payload

    def list_events(self, case_id: str) -> list[dict]:
        return []


class ArtifactServiceClient:
    def list_artifacts(self, case_id: str) -> list[dict]:
        return []

    def get_artifact(self, artifact_id: str) -> dict:
        return {
            "artifact_id": artifact_id,
            "case_id": "unknown",
            "artifact_type": "INTAKE_SUMMARY",
            "truth_class": "PROPOSAL",
            "review_status": "PENDING",
            "title": "Artifact",
        }


class WorkflowServiceClient:
    def get_workflow(self, case_id: str) -> dict:
        return {
            "case_id": case_id,
            "current_state": "INTAKE_RECEIVED",
            "last_transition_at": "2026-03-23T00:00:00Z",
        }


class ReviewServiceClient:
    def list_reviews(self, case_id: str) -> list[dict]:
        return []

    def decide_review(self, review_id: str, decision: dict) -> dict:
        return {
            "review_id": review_id,
            "case_id": "unknown",
            "artifact_id": "unknown",
            "status": "CLOSED",
            "decision": decision["decision"],
        }

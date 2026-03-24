from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "CASECORE API Service"
    api_prefix: str = "/api/v1"

    persistence_service_url: str = os.getenv("PERSISTENCE_SERVICE_URL", "")
    audit_service_url: str = os.getenv("AUDIT_SERVICE_URL", "")
    artifact_service_url: str = os.getenv("ARTIFACT_SERVICE_URL", "")
    workflow_service_url: str = os.getenv("WORKFLOW_SERVICE_URL", "")
    review_service_url: str = os.getenv("REVIEW_SERVICE_URL", "")

    environment: str = os.getenv("ENVIRONMENT", "local")


settings = Settings()

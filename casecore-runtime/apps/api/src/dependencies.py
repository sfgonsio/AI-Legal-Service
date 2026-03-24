from src.services.service_clients import (
    PersistenceServiceClient,
    AuditServiceClient,
    ArtifactServiceClient,
    WorkflowServiceClient,
    ReviewServiceClient,
)
from src.services.retrieval_gateway import RetrievalGateway


def get_persistence_client():
    return PersistenceServiceClient()


def get_audit_client():
    return AuditServiceClient()


def get_artifact_client():
    return ArtifactServiceClient()


def get_workflow_client():
    return WorkflowServiceClient()


def get_review_client():
    return ReviewServiceClient()


def get_retrieval_gateway():
    return RetrievalGateway(audit_client=get_audit_client())


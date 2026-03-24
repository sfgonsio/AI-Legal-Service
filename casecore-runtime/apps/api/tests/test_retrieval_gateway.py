from src.services.retrieval_gateway import RetrievalGateway
from src.services.service_clients import AuditServiceClient


def test_retrieval_gateway_runs():
    gateway = RetrievalGateway(audit_client=AuditServiceClient())
    result = gateway.execute(
        case_id="case-1",
        correlation_id="corr-1",
        request={
            "query": "relevant evidence",
            "mode": "AUTHORITATIVE_ONLY",
            "jurisdiction": "CA",
            "purpose": "LEGAL_ANALYSIS",
            "requesting_component": "UI",
            "filters": {},
        },
    )
    assert "retrieval_audit_id" in result
    assert isinstance(result["results"], list)


from src.audit.events import make_audit_event
from src.governance.knowledge_governance import validate_source_class_allowed
from src.source_adapters.registry import adapters_for_mode
from src.utils.ids import new_id


class RetrievalGateway:
    def __init__(self, audit_client):
        self.audit_client = audit_client

    def execute(self, *, case_id: str, correlation_id: str, request: dict) -> dict:
        mode = request["mode"]
        query = request["query"]
        filters = request.get("filters", {})
        jurisdiction = request["jurisdiction"]

        adapters = adapters_for_mode(mode)
        normalized_results = []

        for adapter in adapters:
            raw_items = adapter.retrieve(query=query, filters=filters, jurisdiction=jurisdiction)
            for raw in raw_items:
                classified = adapter.classify(raw)
                validate_source_class_allowed(mode, classified["source_class"])
                normalized = adapter.normalize(classified)
                normalized_results.append(normalized)

        retrieval_audit_id = new_id()
        audit_event = make_audit_event(
            event_type="RETRIEVAL_EXECUTED",
            case_id=case_id,
            correlation_id=correlation_id,
            payload={
                "retrieval_audit_id": retrieval_audit_id,
                "query": query,
                "mode": mode,
                "requesting_component": request["requesting_component"],
                "results_count": len(normalized_results),
                "sources_used": list({item["source_class"] for item in normalized_results}),
            },
        )
        self.audit_client.write_event(audit_event)

        return {
            "retrieval_audit_id": retrieval_audit_id,
            "results": normalized_results,
        }


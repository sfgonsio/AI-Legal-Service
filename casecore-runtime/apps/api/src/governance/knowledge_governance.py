from src.governance.policy import MODE_ALLOWED_SOURCE_CLASSES


class KnowledgeGovernanceError(Exception):
    pass


def allowed_source_classes_for_mode(mode: str) -> list[str]:
    if mode not in MODE_ALLOWED_SOURCE_CLASSES:
        raise KnowledgeGovernanceError(f"Unsupported retrieval mode: {mode}")
    return MODE_ALLOWED_SOURCE_CLASSES[mode]


def validate_source_class_allowed(mode: str, source_class: str) -> None:
    allowed = allowed_source_classes_for_mode(mode)
    if source_class not in allowed:
        raise KnowledgeGovernanceError(
            f"Source class '{source_class}' is not allowed in mode '{mode}'"
        )


def trust_lane_for_source_class(source_class: str) -> str:
    mapping = {
        "AUTHORITATIVE_PRIMARY": "PRIMARY",
        "AUTHORITATIVE_SECONDARY": "SECONDARY",
        "EXPLORATORY": "EXPLORATORY",
        "UNTRUSTED": "UNTRUSTED",
    }
    return mapping[source_class]


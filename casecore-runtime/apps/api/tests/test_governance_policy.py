from src.governance.knowledge_governance import validate_source_class_allowed
import pytest


def test_authoritative_only_rejects_exploratory():
    with pytest.raises(Exception):
        validate_source_class_allowed("AUTHORITATIVE_ONLY", "EXPLORATORY")


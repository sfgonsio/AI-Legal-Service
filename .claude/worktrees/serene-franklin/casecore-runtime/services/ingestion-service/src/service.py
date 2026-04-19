def register_document(matter_id: str, filename: str) -> dict:
    return {
        "accepted": True,
        "matter_id": matter_id,
        "document_id": "DOC-001",
        "filename": filename
    }

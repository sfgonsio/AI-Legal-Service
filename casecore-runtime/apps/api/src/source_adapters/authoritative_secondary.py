import json
from pathlib import Path
from hashlib import sha256
from src.source_adapters.base import SourceAdapter
from src.utils.timestamps import utc_now_iso


class AuthoritativeSecondaryAdapter(SourceAdapter):
    source_class = "AUTHORITATIVE_SECONDARY"

    def retrieve(self, query: str, filters: dict, jurisdiction: str) -> list[dict]:
        path = Path(__file__).resolve().parents[2] / "data" / "authoritative_secondary_stub.json"
        items = json.loads(path.read_text(encoding="utf-8"))
        query_lower = query.lower()
        return [
            item for item in items
            if jurisdiction.upper() == item["jurisdiction"].upper()
            and query_lower in item["content"].lower()
        ]

    def classify(self, raw_item: dict) -> dict:
        raw_item["source_class"] = self.source_class
        return raw_item

    def normalize(self, classified_item: dict) -> dict:
        content = classified_item["content"]
        return {
            "content": content,
            "source_class": self.source_class,
            "trust_lane": "SECONDARY",
            "citation": classified_item["citation"],
            "jurisdiction": classified_item["jurisdiction"],
            "confidence": "HIGH",
            "metadata": {
                "source_name": classified_item["source_name"],
                "publication_date": classified_item.get("publication_date"),
                "effective_date": classified_item.get("effective_date"),
                "retrieved_at": utc_now_iso(),
                "ingest_hash": sha256(content.encode("utf-8")).hexdigest(),
            },
        }


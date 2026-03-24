from src.source_adapters.authoritative_primary import AuthoritativePrimaryAdapter
from src.source_adapters.authoritative_secondary import AuthoritativeSecondaryAdapter
from src.source_adapters.exploratory import ExploratoryAdapter


def adapters_for_mode(mode: str):
    if mode == "AUTHORITATIVE_ONLY":
        return [AuthoritativePrimaryAdapter()]
    if mode == "AUTHORITATIVE_PLUS_SECONDARY":
        return [AuthoritativePrimaryAdapter(), AuthoritativeSecondaryAdapter()]
    if mode in {"EXPLORATORY_ALLOWED", "COMPARATIVE_RESEARCH"}:
        return [
            AuthoritativePrimaryAdapter(),
            AuthoritativeSecondaryAdapter(),
            ExploratoryAdapter(),
        ]
    if mode == "BROAD_RESEARCH":
        return [
            AuthoritativePrimaryAdapter(),
            AuthoritativeSecondaryAdapter(),
            ExploratoryAdapter(),
        ]
    raise ValueError(f"Unsupported mode: {mode}")


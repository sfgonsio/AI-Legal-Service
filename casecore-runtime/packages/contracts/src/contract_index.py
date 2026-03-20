from __future__ import annotations

from pathlib import Path

from contract_loader import AUTHORITATIVE_ROOT

INDEX = {
    "schemas": AUTHORITATIVE_ROOT / "schemas",
    "apis": AUTHORITATIVE_ROOT / "apis",
    "events": AUTHORITATIVE_ROOT / "events",
    "enums": AUTHORITATIVE_ROOT / "enums",
    "audit": AUTHORITATIVE_ROOT / "audit",
    "workflows": AUTHORITATIVE_ROOT / "workflows",
    "prompts": AUTHORITATIVE_ROOT / "prompts",
    "programs": AUTHORITATIVE_ROOT / "programs",
    "agents": AUTHORITATIVE_ROOT / "agents",
    "taxonomies": AUTHORITATIVE_ROOT / "taxonomies",
    "manifest": AUTHORITATIVE_ROOT / "manifest",
}


def get_contract_dir(name: str) -> Path:
    if name not in INDEX:
        raise KeyError(f"Unknown contract directory: {name}")
    return INDEX[name]

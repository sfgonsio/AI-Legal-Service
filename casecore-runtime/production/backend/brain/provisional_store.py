"""
Read-only accessor for the provisional CACI store.

This is the ONLY module that reads from authority_packs/ca_caci_provisional/.
Resolver calls in here; nothing else should.
"""
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


# Repo-root-relative. The backend is deployed from casecore-runtime/production/backend/.
# The provisional store lives at the repo root authority_packs/ path. We resolve by
# walking up from this file; fall back to an env override for deployment.
_DEFAULT_PACK_REL = "authority_packs/ca_caci_provisional"


class ProvisionalStoreError(Exception):
    pass


def _pack_root() -> Path:
    override = os.getenv("CACI_PROVISIONAL_PACK_PATH")
    if override:
        return Path(override)
    # Walk up from this file looking for authority_packs/ca_caci_provisional
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        candidate = parent / _DEFAULT_PACK_REL
        if candidate.is_dir():
            return candidate
    # Last resort: assume 6 levels up (backend/brain/provisional_store.py -> repo root)
    return here.parents[5] / _DEFAULT_PACK_REL


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ProvisionalStoreError("PyYAML not installed; cannot read provisional store")
    if not path.is_file():
        raise ProvisionalStoreError(f"Provisional record not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def _manifest() -> Dict[str, Any]:
    return _load_yaml(_pack_root() / "manifest.yaml")


def invalidate_cache() -> None:
    """Call after supersession or ingest; resolver should not re-cache stale manifests."""
    _manifest.cache_clear()


def load_active_record(caci_id: str) -> Optional[Dict[str, Any]]:
    """Return the currently active provisional record for a caci_id, or None."""
    manifest = _manifest()
    entry = (manifest.get("records") or {}).get(caci_id)
    if not entry:
        return None
    ref = entry.get("record_ref")
    if not ref:
        return None
    return _load_yaml(_pack_root() / ref)


def load_record_by_id(caci_id: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Load a record by (caci_id, record_id). Checks active first, then superseded/."""
    active = load_active_record(caci_id)
    if active and active.get("record_id") == record_id:
        return active

    superseded_dir = _pack_root() / "superseded"
    if not superseded_dir.is_dir():
        return None
    for candidate in superseded_dir.glob(f"{caci_id}__*.yaml"):
        try:
            doc = _load_yaml(candidate)
        except ProvisionalStoreError:
            continue
        if doc.get("record_id") == record_id:
            return doc
    return None

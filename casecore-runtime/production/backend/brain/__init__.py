"""
Brain — authority resolution and downstream coordination.

Downstream code MUST use `authority_resolver.resolve_authority()` to read CACI
authority. Direct reads of provisional records are forbidden.

See contract/v1/brain/case_authority_resolution.md
"""
from .authority_resolver import resolve_authority, ResolvedAuthority
from .provisional_store import (
    load_active_record,
    load_record_by_id,
    ProvisionalStoreError,
)
from . import state_machine
from .analysis_runner import run_analysis

__all__ = [
    "resolve_authority",
    "ResolvedAuthority",
    "load_active_record",
    "load_record_by_id",
    "ProvisionalStoreError",
    "state_machine",
    "run_analysis",
]

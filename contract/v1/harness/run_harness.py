#!/usr/bin/env python3
"""
contract/v1/harness/run_harness.py

Deterministic JSON "run + audit" harness for Contract v1.
No DB, no network. Emits:
- outputs/run_record.json
- outputs/audit_ledger.json

Canonical JSON:
- UTF-8
- sorted keys
- separators (",", ":")
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]  # .../contract/v1
POLICY_DIR = ROOT / "policy"
TOOLS_DIR = ROOT / "tools"
OUT_DIR = Path(__file__).resolve().parent / "outputs"


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def read_text_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def now_utc_from_arg(s: str | None) -> str:
    if s:
        # Expect ISO8601 UTC time. Normalize to ...Z.
        if s.endswith("Z"):
            return s
        return s + "Z"
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def extract_roles(yaml_text: str) -> List[str]:
    roles: List[str] = []
    for line in yaml_text.splitlines():
        s = line.strip()
        if s.startswith("- role_id:"):
            roles.append(s.split(":", 1)[1].strip())
    return roles


def extract_lanes_allowed_roles(yaml_text: str) -> Dict[str, List[str]]:
    """
    lane_id -> allowed_callers.roles list
    (Minimal YAML pattern extraction; no external deps.)
    """
    lanes: Dict[str, List[str]] = {}
    current_lane: str | None = None
    in_roles_list = False

    for raw in yaml_text.splitlines():
        line = raw.rstrip()

        if line.strip().startswith("- lane_id:"):
            current_lane = line.split(":", 1)[1].strip()
            lanes[current_lane] = []
            in_roles_list = False
            continue

        if current_lane is None:
            continue

        if line.strip().startswith("roles:"):
            # roles: [A, B] OR multiline list
            if "[" in line and "]" in line:
                inside = line.split("[", 1)[1].split("]", 1)[0].strip()
                lanes[current_lane] = [x.strip() for x in inside.split(",")] if inside else []
                in_roles_list = False
            else:
                in_roles_list = True
            continue

        if in_roles_list:
            s = line.strip()
            if s.startswith("- "):
                lanes[current_lane].append(s[2:].strip())
            elif s and not s.startswith("-"):
                in_roles_list = False

    return lanes


def extract_lane_tools(yaml_text: str) -> Dict[str, List[str]]:
    """
    lane_id -> allowed_actions.tools list
    """
    lane_tools: Dict[str, List[str]] = {}
    current_lane: str | None = None
    in_tools = False

    for raw in yaml_text.splitlines():
        line = raw.rstrip()

        if line.strip().startswith("- lane_id:"):
            current_lane = line.split(":", 1)[1].strip()
            lane_tools[current_lane] = []
            in_tools = False
            continue

        if current_lane is None:
            continue

        if line.strip() == "tools:":
            in_tools = True
            continue

        if in_tools:
            s = line.strip()
            if s.startswith("- "):
                lane_tools[current_lane].append(s[2:].strip())
            elif s and not s.startswith("-"):
                in_tools = False

    return lane_tools


def extract_tool_registry(yaml_text: str) -> Dict[str, Dict[str, Any]]:
    """
    tool_name -> { enabled: bool|None, implementation_status: str|None }
    Minimal extractor (no YAML dependency).
    """
    tools: Dict[str, Dict[str, Any]] = {}
    current: str | None = None

    for raw in yaml_text.splitlines():
        s = raw.strip()

        if s.startswith("- tool_name:"):
            current = s.split(":", 1)[1].strip()
            tools[current] = {"enabled": None, "implementation_status": None}
            continue

        if current is None:
            continue

        if s.startswith("enabled:"):
            val = s.split(":", 1)[1].strip().lower()
            tools[current]["enabled"] = (val == "true")
            continue

        if s.startswith("implementation_status:"):
            tools[current]["implementation_status"] = s.split(":", 1)[1].strip()
            continue

    return tools


def build_run_record(
    run_id: str,
    request: Dict[str, Any],
    now_utc: str,
    policy_versions: Tuple[str, str],
) -> Dict[str, Any]:
    lanes_ver, roles_ver = policy_versions
    return {
        "run_id": run_id,
        "parent_run_id": None,
        "root_run_id": run_id,
        "correlation_id": None,
        "run_kind": request.get("run_kind", "unspecified"),
        "status": "running",
        "contract_version": "v1",
        "policy_versions_lanes": lanes_ver,
        "policy_versions_roles": roles_ver,
        "taxonomy_versions_coa": None,
        "taxonomy_versions_tags": None,
        "taxonomy_versions_entities": None,
        "case_id": request.get("scope", {}).get("case_id"),
        "lane_id": request.get("lane_id"),
        "actor_type": "agent",
        "actor_id": "harness_actor",
        "role_id": request.get("agent_role"),
        "created_at_utc": now_utc,
        "started_at_utc": now_utc,
        "completed_at_utc": None,
        "error_code": None,
        "error_message_bounded": None,
        "retryable": None,
        "metadata_json": {
            "harness": True,
            "idempotency_key": request.get("idempotency_key"),
        },
        "inputs_artifacts_json": [],
        "outputs_artifacts_json": [],
    }


def audit_event(
    *,
    event_id: str,
    ts: str,
    action_type: str,
    outcome: str,
    run_id: str,
    lane_id: str | None,
    case_id: str | None,
    role_id: str | None,
    tool_name: str | None = None,
    policy_versions: Tuple[str, str] = ("v1", "v1"),
    request_obj: Any | None = None,
    response_obj: Any | None = None,
    outcome_reason: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    retryable: bool | None = None,
) -> Dict[str, Any]:
    lanes_ver, roles_ver = policy_versions
    return {
        "event_id": event_id,
        "timestamp_utc": ts,
        "action_type": action_type,
        "outcome": outcome,
        "outcome_reason_bounded": outcome_reason,
        "contract_version": "v1",
        "policy_versions_lanes": lanes_ver,
        "policy_versions_roles": roles_ver,
        "case_id": case_id,
        "lane_id": lane_id,
        "run_id": run_id,
        "parent_run_id": None,
        "root_run_id": run_id,
        "actor_type": "agent",
        "actor_id": "harness_actor",
        "role_id": role_id,
        "target_json": {},
        "request_hash_sha256": sha256_hex(request_obj) if request_obj is not None else None,
        "response_hash_sha256": sha256_hex(response_obj) if response_obj is not None else None,
        "input_artifacts_json": [],
        "output_artifacts_json": [],
        "error_code": error_code,
        "error_message_bounded": error_message,
        "retryable": retryable,
        "metadata_json": {"tool_name": tool_name} if tool_name else {},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default=str(Path(__file__).resolve().parent / "sample_payloads" / "tool_request.json"))
    ap.add_argument("--run_id", default=None)
    ap.add_argument("--now_utc", default=None, help="ISO8601 UTC time, e.g. 2026-02-23T18:00:00Z (recommended for acceptance)")
    ap.add_argument("--policy_lanes_version", default="v1")
    ap.add_argument("--policy_roles_version", default="v1")
    args = ap.parse_args()

    request_path = Path(args.request)
    request = json.loads(request_path.read_text(encoding="utf-8"))

    now_utc = now_utc_from_arg(args.now_utc)
    policy_versions = (args.policy_lanes_version, args.policy_roles_version)

    req_hash = sha256_hex(request)
    run_id = args.run_id or f"RUN_{req_hash[:12]}"

    roles_txt = read_text_utf8(POLICY_DIR / "roles.yaml")
    lanes_txt = read_text_utf8(POLICY_DIR / "lanes.yaml")
    tools_txt = read_text_utf8(TOOLS_DIR / "tool_registry.yaml")

    roles = set(extract_roles(roles_txt))
    lanes_allowed = extract_lanes_allowed_roles(lanes_txt)
    lane_tools = extract_lane_tools(lanes_txt)
    tool_registry = extract_tool_registry(tools_txt)

    role_id = request.get("agent_role")
    lane_id = request.get("lane_id")
    tool_name = request.get("tool_name")
    case_id = request.get("scope", {}).get("case_id")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    run_record = build_run_record(run_id, request, now_utc, policy_versions)
    events: List[Dict[str, Any]] = []

    # 1) run_created
    events.append(
        audit_event(
            event_id=f"EVT_{run_id}_001",
            ts=now_utc,
            action_type="run_created",
            outcome="success",
            run_id=run_id,
            lane_id=lane_id,
            case_id=case_id,
            role_id=role_id,
            policy_versions=policy_versions,
            request_obj={"run_record": run_record},
            response_obj={"created": True},
        )
    )

    # 2) lane_authorized
    lane_ok = True
    lane_reason = None

    if role_id not in roles:
        lane_ok = False
        lane_reason = "role_not_defined"
    elif lane_id not in lanes_allowed:
        lane_ok = False
        lane_reason = "lane_not_defined"
    elif role_id not in lanes_allowed.get(lane_id, []):
        lane_ok = False
        lane_reason = "role_not_allowed_for_lane"

    events.append(
        audit_event(
            event_id=f"EVT_{run_id}_002",
            ts=now_utc,
            action_type="lane_authorized",
            outcome="success" if lane_ok else "denied",
            outcome_reason=lane_reason,
            run_id=run_id,
            lane_id=lane_id,
            case_id=case_id,
            role_id=role_id,
            policy_versions=policy_versions,
            request_obj={"role_id": role_id, "lane_id": lane_id},
            response_obj={"authorized": lane_ok, "reason": lane_reason},
        )
    )

    # 3) tool_requested (always recorded)
    events.append(
        audit_event(
            event_id=f"EVT_{run_id}_003",
            ts=now_utc,
            action_type="tool_requested",
            outcome="success",
            run_id=run_id,
            lane_id=lane_id,
            case_id=case_id,
            role_id=role_id,
            tool_name=tool_name,
            policy_versions=policy_versions,
            request_obj=request,
            response_obj={"received": True},
        )
    )

    # 4) tool_allowed (policy + registry check)
    allowed = True
    deny_reason = None

    if not lane_ok:
        allowed = False
        deny_reason = "lane_not_authorized"
    elif tool_name not in tool_registry:
        allowed = False
        deny_reason = "tool_not_registered"
    elif tool_name not in lane_tools.get(lane_id, []):
        allowed = False
        deny_reason = "tool_not_allowed_in_lane"
    else:
        enabled = tool_registry[tool_name].get("enabled")
        impl = tool_registry[tool_name].get("implementation_status")
        if enabled is False:
            allowed = False
            deny_reason = "tool_disabled"
        elif impl != "implemented":
            allowed = False
            deny_reason = "tool_not_implemented"

    events.append(
        audit_event(
            event_id=f"EVT_{run_id}_004",
            ts=now_utc,
            action_type="tool_allowed",
            outcome="success" if allowed else "denied",
            outcome_reason=deny_reason,
            run_id=run_id,
            lane_id=lane_id,
            case_id=case_id,
            role_id=role_id,
            tool_name=tool_name,
            policy_versions=policy_versions,
            request_obj={"tool_name": tool_name, "lane_id": lane_id},
            response_obj={"allowed": allowed, "reason": deny_reason},
        )
    )

    # 5) tool_denied OR tool_executed (v1 default: denied)
    if not allowed:
        denial_response = {
            "status": "denied",
            "error_code": "TOOL_DENIED",
            "diagnostic": {
                "category": "policy",
                "message": "Tool execution denied by Tool Gateway policy.",
                "likely_cause": deny_reason,
                "suggested_fix": "Enable and implement tool OR adjust lane permissions under attorney-approved contract change.",
                "retryable": False,
                "severity": "high",
            },
        }

        events.append(
            audit_event(
                event_id=f"EVT_{run_id}_005",
                ts=now_utc,
                action_type="tool_denied",
                outcome="denied",
                outcome_reason=deny_reason,
                run_id=run_id,
                lane_id=lane_id,
                case_id=case_id,
                role_id=role_id,
                tool_name=tool_name,
                policy_versions=policy_versions,
                request_obj=request,
                response_obj=denial_response,
                error_code="TOOL_DENIED",
                error_message=f"Denied: {deny_reason}",
                retryable=False,
            )
        )

        run_record["status"] = "completed"
        run_record["completed_at_utc"] = now_utc
    else:
        # reserved for future when tools become enabled+implemented
        run_record["status"] = "failed"
        run_record["completed_at_utc"] = now_utc
        run_record["error_code"] = "TOOL_NOT_IMPLEMENTED"
        run_record["error_message_bounded"] = "Harness does not execute tools."

        events.append(
            audit_event(
                event_id=f"EVT_{run_id}_005",
                ts=now_utc,
                action_type="tool_executed",
                outcome="failed",
                outcome_reason="harness_no_execution",
                run_id=run_id,
                lane_id=lane_id,
                case_id=case_id,
                role_id=role_id,
                tool_name=tool_name,
                policy_versions=policy_versions,
                request_obj=request,
                response_obj={"status": "failed", "error_code": "TOOL_NOT_IMPLEMENTED"},
                error_code="TOOL_NOT_IMPLEMENTED",
                error_message="Harness does not execute tools.",
                retryable=False,
            )
        )

    # 6) run_completed
    events.append(
        audit_event(
            event_id=f"EVT_{run_id}_006",
            ts=now_utc,
            action_type="run_completed",
            outcome="success" if run_record["status"] == "completed" else "failed",
            outcome_reason="completed" if run_record["status"] == "completed" else "failed",
            run_id=run_id,
            lane_id=lane_id,
            case_id=case_id,
            role_id=role_id,
            policy_versions=policy_versions,
            request_obj={"final_status": run_record["status"]},
            response_obj={"completed": True, "status": run_record["status"]},
        )
    )

    (OUT_DIR / "run_record.json").write_text(
        json.dumps(run_record, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (OUT_DIR / "audit_ledger.json").write_text(
        json.dumps(events, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    print("OK: wrote contract/v1/harness/outputs/run_record.json and audit_ledger.json")
    print(f"run_id={run_id}")
    print(f"request_hash_sha256={req_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
# Semantic Contract Validation Checklist (v1)

This checklist defines "done" for Semantic Contract Validation.

## SSOT Integrity
- [ ] No duplicate authoritative documents exist in contract/v1 (all duplicates removed or replaced with explicit stub pointers).
- [ ] contract_manifest.yaml enumerates all authoritative v1 artifacts.
- [ ] All contract references are relative paths and resolve correctly.

## Policy Alignment
- [ ] roles.yaml defines authority boundaries for: taxonomy writes, run approval, export approval.
- [ ] lanes.yaml maps roles to allowed actions and gating requirements.
- [ ] policy_versioning.md defines: version bumps, approvals, audit events.

## Orchestration Determinism
- [ ] orchestrator_contract.md references run_lifecycle.md and run_status_model.md.
- [ ] Rerun policy is explicit: partial rerun vs COA remap vs full regeneration; requires attorney action.
- [ ] Validation gates are explicit: what blocks progress and what produces audit events.

## Tool Mediation
- [ ] tool_registry.yaml enumerates all tools used by agents.
- [ ] tool_gateway_contract.md enforces: mediated access, allowlists, logging, error normalization.
- [ ] Agents do not call external tools directly (only via gateway).

## Schemas & Auditability
- [ ] audit_event schema covers: tool_call, taxonomy_change, run_state_change, export_created.
- [ ] run_record schema captures: inputs, policy versions, taxonomy versions, tool registry version, artifacts produced.
- [ ] export_bundle schema includes: provenance pointers, case scope, attorney approval status.

## Taxonomies Exist + Are Governed
- [ ] base_coa_v1.yaml exists and defines governance + entry schema.
- [ ] entity_schema_v1.yaml exists and defines canonical fields + overlay rules.
- [ ] tag_schema_v1.yaml exists and defines governance + entry schema.
- [ ] taxonomy_versioning.md defines promotion/locking rules.

## Data Layer Coherence
- [ ] postgres_ddl.sql supports run_record + audit_event + artifact_ref + export_bundle persistence.
- [ ] data_model_mappings.md ties schemas to DB tables/columns without ambiguity.

## Deferred Items (Tracked)
- [ ] Define SYSTEM lanes for platform-only behaviors (audit logging, run state transitions, schedulers) once execution wiring begins.
  - Owner: SystemOwner
  - Trigger: Implement tool gateway + orchestrator runtime
  - Exit: SYSTEM role has only platform lanes; never content-authority lanes

## Outcome
Semantic Contract Validation is complete when all items are checked and a commit is made that includes only contract/v1 changes.
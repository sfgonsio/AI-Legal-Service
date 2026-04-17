# 1. Runtime Identity

**Runtime Name:** PLATFORM_RUNTIME  
**Runtime Type:** Deterministic AI Legal Platform Runtime  
**Contract Version:** v1  
**Lifecycle Authority:** Contract v1 SSOT  
**Primary Function:** Governed execution of agents, deterministic programs, workflow orchestration, evidence graph construction, legal tagging, cause-of-action assembly, audit logging, replay validation, and attorney review routing

The PLATFORM_RUNTIME is the authoritative runtime contract for the AI Legal platform. It defines how all governed platform components execute together as a single deterministic system.

The runtime contract binds together:

- governed AI agents
- deterministic execution programs
- orchestration state control
- evidence graph schemas
- legal taxonomies and mapping rules
- tool gateway enforcement
- replay harness requirements
- audit and provenance controls

# 2. Runtime Purpose

The purpose of the PLATFORM_RUNTIME is to ensure that the platform operates as a single governed system rather than a collection of disconnected AI and software components.

The runtime must guarantee:

- deterministic execution
- governed module interaction
- controlled state transitions
- attorney review gating
- replay-safe reruns
- supersession preservation
- complete auditability
- build-readiness for implementation platforms

# 3. Runtime Components

The runtime includes the following component classes:

## 3.1 Agents

- INTERVIEW_AGENT
- MAPPING_AGENT
- COA_REASONER

## 3.2 Deterministic Programs

- FACT_NORMALIZATION
- COMPOSITE_ENGINE
- TAGGING_ENGINE
- COA_ENGINE
- WORKFLOW_ORCHESTRATOR

## 3.3 Orchestration Assets

- state_model.yaml
- workflow_rules.yaml
- rerun_governance.yaml
- approval_gates.yaml

## 3.4 Legal Intelligence Assets

- coa_taxonomy.yaml
- tagging_rules.yaml
- coa_mapping_rules.yaml

## 3.5 Data / Graph Assets

- evidence_graph_schema.yaml

## 3.6 Runtime Enforcement Assets

- tool_registry.yaml
- tool_gateway_contract.yaml
- replay_contract.yaml
- run_identity_contract.yaml
- output_fingerprint_contract.yaml
- platform_build_index.yaml

# 4. Runtime Execution Order

The runtime must support the following governed workflow order:

1. Case intake opens
2. INTERVIEW_AGENT executes
3. FACT_NORMALIZATION executes
4. MAPPING_AGENT executes
5. COMPOSITE_ENGINE executes
6. TAGGING_ENGINE executes
7. COA_ENGINE executes
8. Attorney review gate is reached
9. Rerun or closure path proceeds according to governed decision

No module may execute outside approved workflow order unless a governed rerun rule explicitly permits it.

# 5. Runtime Determinism

The runtime must enforce deterministic behavior across all governed modules.

Determinism requirements:

- identical governed inputs must produce identical governed outputs
- canonical identifiers must be deterministically generated
- workflow order must be reproducible
- reruns must preserve lineage
- replay mismatch must be detectable
- no silent state drift is permitted

# 6. Runtime State Governance

The runtime must enforce the governed state model as the sole authority for workflow progression.

Core state families include:

- CASE_STATE
- PROGRAM_STATE
- AGENT_STATE
- APPROVAL_STATE
- RERUN_STATE
- SUPERSESSION_STATE
- REVIEW_STATE

The WORKFLOW_ORCHESTRATOR is the official state transition authority within the runtime.

# 7. Runtime Read / Write Boundaries

The runtime must enforce strict module boundaries.

Rules:

- agents and programs may read only governed inputs defined in their contracts
- agents and programs may write only governed outputs defined in their contracts
- no module may directly rewrite upstream canonical evidence without governed rerun logic
- all runtime tool execution must pass through the Tool Gateway

# 8. Runtime Tool Gateway Enforcement

All module-to-tool interactions must be mediated through the governed Tool Gateway.

The runtime must enforce:

- registered tool lookup
- caller validation
- request structure validation
- audit logging of tool calls
- deterministic tool execution constraints
- prohibition of unregistered tools

# 9. Runtime Evidence Graph Obligations

The runtime must maintain a governed Evidence Graph composed of:

- documents
- facts
- events
- tags
- cause-of-action records
- governed relationship links

The Evidence Graph must remain traceable from claim-level output back to source evidence.

# 10. Runtime Legal Intelligence Obligations

The runtime must apply governed legal intelligence assets only.

This includes:

- legal tags from deterministic tagging rules
- cause-of-action definitions from governed taxonomy
- element mapping from governed COA mapping rules

No freeform legal conclusion may override governed rule structures in the deterministic layer.

# 11. Runtime Approval and Review Obligations

The runtime must support attorney review checkpoints.

Requirements:

- attorney review must occur after COA generation
- rejection must route to governed rerun logic
- approval history must be preserved
- attorney decisions must never be silently overwritten

# 12. Runtime Rerun and Replay Obligations

The runtime must support reruns and replay under governed rules.

Requirements:

- each rerun receives a new run_id
- rerun scope must be bounded
- prior run history must be preserved
- replay comparisons must detect unexplained drift
- superseded outputs must remain historically visible

# 13. Runtime Provenance and Audit Obligations

The runtime must preserve complete provenance across all governed components.

Minimum obligations:

- run identity tracking
- module execution records
- workflow transition records
- tool call records
- approval records
- rerun records
- supersession records
- output fingerprints

# 14. Runtime Failure Handling

The runtime must fail safely and visibly.

Requirements:

- invalid state transitions must be blocked
- missing prerequisites must halt execution
- failed tool calls must be auditable
- replay mismatches must fail validation
- no silent recovery is permitted where governed execution is required

# 15. Runtime Build Expectations

Any implementation platform must build the runtime in conformance with this contract.

Required implementation capabilities:

- agent runtime execution
- deterministic program runtime execution
- governed workflow orchestration
- evidence graph persistence
- tool gateway enforcement
- audit ledger persistence
- replay harness support
- approval and rerun controls

# 16. Runtime Compliance Requirement

A platform implementation is Contract v1 compliant only if it enforces:

- governed component structure
- deterministic execution
- state-model-controlled workflow
- tool-gateway-restricted runtime behavior
- replay-safe auditability
- evidence-to-claim traceability
- attorney review control

# 17. Runtime Authority

This document is the authoritative runtime contract for the AI Legal platform.

It defines the system-level execution expectations that bind all governed components into a single build-ready runtime.

Any implementation claiming Contract v1 runtime conformance must comply with this specification.
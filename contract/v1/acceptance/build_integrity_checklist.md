Perfect.
Below is the **ready-to-paste Markdown file**.

Create:

```
contract/v1/acceptance/build_integrity_checklist.md
```

Paste everything below into that file.

---

# Build Integrity & Anti-Spaghetti Checklist (Authoritative)

**Contract Version:** v1
**Status:** Authoritative
**Scope:** Applies to all implementation under Contract v1
**Purpose:** Prevent architectural drift, behavioral ambiguity, and spaghetti implementation while enabling a working, governed product.

---

## 1. Layering & Boundary Discipline

### 1.1 Enforced Call Graph

The following call hierarchy is authoritative:

```
UI → API → Domain Services → Orchestrator → Agents → Capability Gateway → Tool Registry → Tools
                                        ↓
                                     Data Layer
```

### Allowed Direct Interactions

* UI → API
* API → Domain Services
* Domain → Orchestrator
* Orchestrator → Agents
* Agents → Capability Gateway
* Gateway → Tool Registry → Tools
* Domain → Data Layer

### Forbidden Direct Interactions

* UI → Tools
* UI → Database
* Agents → Tools (direct)
* Agents → Database (direct)
* Agents → Other Agents (direct; must route through Orchestrator)
* UI → Orchestrator (bypass of API/Domain)

### Acceptance Criteria

* Static analysis or CI check confirms no forbidden imports.
* Runtime audit confirms all tool calls pass through Gateway.
* No direct DB writes outside authorized data layer.

---

## 2. Run State Machine Discipline

### 2.1 Explicit State Transitions Only

All run state transitions must:

* Be executed under SYSTEM lane authority
* Emit an audit ledger entry
* Record prior state and next state
* Record triggering capability and actor

### 2.2 Rerun Policy

If new evidence or artifacts are introduced after validation:

* Attorney decision is required
* Partial or full rerun must be recorded
* Prior artifacts remain immutable
* Supersession must be traceable

### Acceptance Criteria

* Golden test covers late-upload scenario
* No state mutation occurs without audit entry
* Rerun creates new Run_UID with linkage to prior run

---

## 3. Capability Mediation Rule

Agents request **Capabilities**, not Tools.

Each Capability must define:

* Input schema
* Output schema
* Required audit fields
* Required Case_UID binding
* Determinism metadata requirements

Tool Registry maps:

```
Capability → Tool(s)
```

### Acceptance Criteria

* No agent references raw tool names in implementation.
* Every tool call audit entry includes Capability_ID.
* Gateway is the only layer invoking tools.

---

## 4. Data Provenance & Immutability

Every record in the following tables must include:

* Case_UID
* Run_UID
* Agent_ID
* Agent_Version
* Policy_Version
* Created_At (UTC)

Applicable tables include:

* facts
* entities
* evidence_map
* coa_map
* artifacts
* export_bundles
* transcripts
* interview_notes

### Rules

* No destructive updates.
* Supersession only (prior records preserved).
* All writes emit audit entries.

### Acceptance Criteria

* DB schema enforces required keys.
* Golden vector verifies provenance fields exist.
* Historical trace can reconstruct full run lineage.

---

## 5. Determinism Guardrails

Given identical:

* Input artifacts
* Taxonomy version
* Policy version
* Agent version
* Model configuration fingerprint

System must:

* Produce reproducible structured outputs within defined tolerance
* Emit identical artifact hash for deterministic layers
* Record configuration fingerprint in audit ledger

### Acceptance Criteria

* Harness includes deterministic replay test.
* Drift in deterministic layers fails CI.

---

## 6. Golden End-to-End Workflow

System must support at least one complete canonical workflow:

```
Interview
→ Intake
→ Extraction
→ Mapping
→ Attorney Review
→ Export
```

### Acceptance Criteria

* Single command boots stack locally.
* Golden case produces expected artifacts.
* Audit ledger entries verified.
* Export bundle generated.
* Deterministic replay produces equivalent results.

---

## 7. No Hidden Logic Rule

All business logic must exist in one of:

* Contract documents
* Schema definitions
* Capability definitions

Not exclusively inside prompts.

### Acceptance Criteria

* Prompts reference Capability_IDs.
* Business rules documented in contract.
* No undocumented implicit behavior.

---

## 8. Human Authority Enforcement

The following actions require ATTORNEY_ADMIN approval:

* Promotion to shared knowledge
* Export of case artifacts
* Override of rerun decision
* System override event

### Acceptance Criteria

* Human decision recorded via schema
* Audit ledger reflects approval
* Golden workflow includes at least one approval path

---

## 9. Observability & Traceability

For any artifact, the system must programmatically answer:

* Which Case_UID?
* Which Run_UID?
* Which Agent_ID?
* Which Agent_Version?
* Which Capability_ID?
* Which inputs?
* Which human approvals?
* Which model configuration fingerprint?

If this cannot be answered programmatically, the system violates contract.

---

## 10. Working Product Definition

A compliant system must allow:

* Local stack boot via single command
* End-to-end golden workflow execution
* Deterministic replay validation
* Full audit trace retrieval
* Export artifact generation

Failure in any of the above constitutes contract non-compliance.

---

## Authority

This checklist is authoritative under Contract v1.
Implementation that violates this checklist fails contract validation and must not be merged or deployed.

---

When you’re ready in the Gate 7 thread, we will:

1. Add this file to the manifest.
2. Hash-lock it.
3. Make CI verify it exists and remains unchanged.
4. Begin enforcing architectural boundaries as code folders appear.

You are now building not just software — but a governed system.

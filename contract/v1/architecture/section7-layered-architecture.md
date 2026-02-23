# Section 7 — Layered Architecture (SSOT)

**Contract Version:** v1 (locked)  
**Authority:** This document is the authoritative architecture SSOT for Section 7.  
**Derived artifacts:** Any diagrams, docs pages, code comments, or presentations MUST conform to this SSOT.  
**Policy bindings (authoritative inputs):**
- `contract/v1/policy/lanes.yaml` (lane definitions + permissions)
- `contract/v1/policy/roles.yaml` (role definitions + lane access)

**Conflict rule:** If any conflict exists between any derived artifact and this SSOT, **this SSOT governs**.

---

## 7.1 Authority Model

### 7.1.1 Human Authority (Supreme)
Human authority (attorney-admin and approved delegates) is the supreme governance authority for:
- accepting/rejecting cases
- defining and approving controlled vocabularies (COA, taxonomy)
- approving promotions from case knowledge to shared knowledge
- approving exports and external sharing
- approving policy changes (lanes/roles) and contract evolution

### 7.1.2 Contract Authority (Deterministic Governance)
The Contract v1 repository is the authoritative source of:
- architecture constraints
- lane and role policy
- schemas and taxonomy artifacts
- deterministic run rules

### 7.1.3 System Authority (Enforced Execution)
The platform enforces authority through choke points:
- **Tool Gateway**: all tool invocations MUST be mediated, scoped, and audited
- **Write Broker (Persistence Service)**: all persistence writes MUST be mediated, validated, scoped, and audited
- **Audit Ledger**: append-only, authoritative log of all privileged actions

No agent may bypass the choke points.

---

## 7.2 Architectural Goals (Non-Negotiable)

1. **Case Isolation:** Case data is strictly isolated by case_id; no cross-case reads/writes of case data are permitted.
2. **Shared Learning Without Leakage:** The system may improve over time only via governed promotion into shared knowledge, with explicit controls preventing client-identifying or privileged content leakage.
3. **Determinism:** Runs must be reproducible given the same inputs, versions, and policies, within defined tolerances.
4. **Auditability:** All privileged actions are logged with sufficient provenance to reconstruct what happened, when, by whom, and under which contract version.
5. **Least Privilege:** Agents only receive the minimum lane access needed for their role.
6. **Drift Control:** Derived diagrams/docs must not introduce new services, flows, persistence zones, or authority semantics.

---

## 7.3 Layer Model (Authoritative)

### Layer A — Presentation & Human Interaction
- Client self-sign-up, attorney/admin UI, staff UI
- Captures inputs and displays outputs
- Does not directly access storage or tools except via governed backend APIs

### Layer B — Orchestration & Workflow Control
- Schedules and sequences agent runs
- Establishes `case_id`, `run_id`, `workflow_state`
- Enforces state transitions (if implemented)
- Requests tool calls and writes only through choke points

### Layer C — Agent Execution Layer
- Agents perform bounded tasks (Interview, Intake, Mapping, Governance)
- Agents MUST declare a `lane_id` for privileged actions
- Agents cannot directly access persistence or tools outside choke points

### Layer D — Tool Gateway (Choke Point)
- Mediates all tool invocations (dictation, transcription, parsing, OCR, etc.)
- Enforces:
  - lane policy (`lanes.yaml`)
  - role bindings (`roles.yaml`)
  - case scoping
  - rate limits (optional)
  - redaction rules (as needed)
- Emits audit ledger events for every privileged tool call

### Layer E — Write Broker / Persistence Service (Choke Point)
- Mediates all writes to any storage (DB/files/object store)
- Enforces:
  - lane policy (`lanes.yaml`)
  - schema constraints (contract schemas)
  - case scoping
  - append-only vs upsert semantics
  - provenance stamping
- Emits audit ledger events for every privileged write

### Layer F — Storage Plane (Split by Trust Zone)
**F1: Case Data Plane (Isolated)**
- Stores case-scoped artifacts: uploads, transcripts, extracted entities, evidence, mappings
- Partitioned by `case_id` (logical and/or physical)
- No cross-case reads/writes allowed

**F2: Shared Knowledge Plane (Governed)**
- Stores *sanitized, non-identifying* generalized insights:
  - playbooks, heuristics, patterns, generic prompts, evaluation results
- Only written via governed promotion lane(s)
- Must not contain raw case content or client identity or privileged notes

### Layer G — Audit & Provenance Plane (Authoritative)
- Append-only audit ledger (system-of-record for “what happened”)
- Stores immutable events about privileged actions across all layers
- Correlates: `case_id`, `run_id`, `actor_id`, `role_id`, `lane_id`, `contract_version`, timestamps

---

## 7.4 Trust Boundaries (Authoritative)

### Boundary 1 — Human ↔ System
- All human actions are authenticated and authorized
- Attorney-admin is the top-level human authority

### Boundary 2 — Agent ↔ Tools
- Agents cannot call tools without Tool Gateway mediation
- Tool Gateway enforces policy + audit

### Boundary 3 — Agent ↔ Storage
- Agents cannot write/read storage directly (no bypass)
- All writes mediated by Write Broker; reads must be case-scoped APIs

### Boundary 4 — Case Data ↔ Shared Knowledge
- No automatic mixing
- Only promotion via governed lanes with sanitation requirements
- Promotions MUST be auditable and reversible in policy terms (disable future use), though ledger remains immutable

---

## 7.5 Data Movement Rules (Allowed/Disallowed)

### 7.5.1 Allowed flows (High-level)
1. Human UI → Orchestrator (case intake events)
2. Orchestrator → Agent (bounded tasks + inputs)
3. Agent → Tool Gateway (tool calls) → results back to Agent/Orchestrator
4. Agent/Orchestrator → Write Broker → Case Data Plane (case-scoped persistence)
5. Governance lane → Write Broker → Shared Knowledge Plane (sanitized promotion only)
6. All privileged actions → Audit Ledger (append-only)

### 7.5.2 Disallowed flows (Non-negotiable)
- Agent → Tool direct (no gateway)  
- Agent → Storage direct (no broker)  
- Case Data Plane → Shared Knowledge Plane without promotion lane  
- Shared Knowledge Plane → Case Data Plane as if it were case evidence  
- Export of raw case content without explicit attorney-approved authorization and audit event

---

## 7.6 Lanes (Policy-Governed Execution Paths)

### 7.6.1 Lane registry (authoritative)
All lanes, access rules, and action scopes are defined in:
- `contract/v1/policy/lanes.yaml`
- `contract/v1/policy/roles.yaml`

### 7.6.2 Lane enforcement (authoritative)
- Every privileged action MUST include `lane_id`
- Tool Gateway and Write Broker MUST deny actions when:
  - lane_id is missing
  - caller role lacks lane access
  - requested action/resource is not allowed for the lane
  - case scoping attributes are missing or invalid

### 7.6.3 Provenance stamping (required)
Every write MUST include:
- `case_id`
- `run_id`
- `actor_id` (agent id or human id)
- `role_id`
- `lane_id`
- `contract_version`
- `timestamp`

---

## 7.7 Persistence Rules (Authoritative)

1. Case Data Plane is **append-first** for evidentiary artifacts:
   - transcripts, facts, evidence links, mapping outputs should be append-only where feasible
2. Upserts are allowed only for:
   - derived indexes
   - de-duplication tables
   - non-evidentiary convenience views
3. Shared Knowledge Plane writes are permitted only via promotion lanes.
4. Deletions of stored records should be avoided; if necessary, use tombstones while audit ledger remains immutable.

---

## 7.8 Audit Ledger Requirements (Authoritative)

### 7.8.1 Ledger is append-only
The audit ledger MUST be append-only and treated as the authoritative record.

### 7.8.2 Minimum event fields
Each event MUST include:
- event_id (unique)
- timestamp_utc
- case_id (nullable only for non-case system events)
- run_id (nullable only for non-run actions)
- actor_id
- role_id
- lane_id
- action_type (tool_call, db_write, policy_change, promotion, export, override)
- target (tool name, table name, artifact id)
- outcome (allow/deny)
- contract_version
- policy_version (lanes/roles version)
- input_hashes and/or artifact_hashes where applicable

### 7.8.3 Audit coverage
Audit events MUST be emitted for:
- every tool invocation
- every persistence write
- every promotion to shared knowledge
- every export operation
- every policy change (lanes/roles)
- every override action

---

## 7.9 Knowledge Promotion (Shared Learning Without Leakage)

### 7.9.1 Promotion principle
The system improves over time through promotion of **sanitized insights** only.

### 7.9.2 Promotion classes
**Auto-promotable (system-approved)**
- performance metrics (latency, error rates)
- generic prompt refinements not derived from raw client text
- tool reliability findings
- non-identifying workflow heuristics

**Human-approved (attorney-admin required)**
- anything derived from case content, even if anonymized
- any new reusable templates informed by a case
- any cross-case knowledge intended to guide decisions

### 7.9.3 Prohibitions
Promotions MUST NOT include:
- raw case text
- client identity
- privileged notes or legal strategy
- unique identifiers that allow re-identification

All promotions MUST be logged in the audit ledger with promotion_ticket_id.

---

## 7.10 Determinism Guarantees (Authoritative)

### 7.10.1 Version locking
A run is defined by:
- input artifacts + hashes
- contract_version
- policy versions (lanes/roles)
- taxonomy versions (COA, tag schemes)
- tool versions (where applicable)

### 7.10.2 Reproducibility
Given the same run definition, the platform MUST be capable of reproducing outputs within defined tolerances.

### 7.10.3 Explicit nondeterminism
Any nondeterministic tool calls (external APIs, web retrieval, random sampling) MUST:
- be explicitly labeled as nondeterministic
- record inputs/outputs sufficient for replay (when possible)
- be logged in audit ledger

---

## 7.11 Prohibited Patterns (Non-Negotiable)

- Cross-case joins of case data
- Unscoped reads (missing case_id)
- Unmediated tool access (no Tool Gateway)
- Unmediated writes (no Write Broker)
- Policy stored only in code without contract traceability
- Silent edits to evidentiary artifacts without provenance

---

## 7.12 Drift Control & Update Protocol

### 7.12.1 Drift control
Derived visuals and docs MUST NOT introduce:
- new layers or services
- new data paths or persistence zones
- new authority flows or trust boundaries
- new tool access patterns
- new logging/audit semantics

### 7.12.2 Update protocol
If drift or change is required:
1. Update this SSOT file first
2. Update contract policy (roles/lanes) second (if needed)
3. Regenerate visuals and derived docs last
4. Commit changes with clear messages referencing contract version impact


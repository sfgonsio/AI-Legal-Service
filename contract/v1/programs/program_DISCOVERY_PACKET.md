# PROGRAM CONTRACT — DISCOVERY_PACKET

## 1. Program Identity

- **Program Name:** DISCOVERY_PACKET
- **Program Type:** Deterministic assembly and packaging program
- **Contract Version:** v1
- **Status:** Draft for Contract v1 governance
- **Owner:** AI Legal Service
- **Canonical Program ID:** `DISCOVERY_PACKET`

---

## 2. Purpose

The `DISCOVERY_PACKET` program assembles attorney-usable discovery support packets from governed repository data. It converts approved and provenance-linked facts, evidence references, event mappings, and issue-aligned materials into deterministic packet outputs suitable for attorney review and downstream litigation work such as interrogatories, requests for production, requests for admission, deposition preparation, meet-and-confer support, and discovery planning.

This program does not make legal decisions, does not determine final attorney strategy, and does not invent evidence. Its role is to package already-governed material into structured discovery-ready outputs with clear provenance, repeatable assembly rules, and auditability.

---

## 3. Business Objective

The business objective of `DISCOVERY_PACKET` is to reduce attorney and litigation support effort required to collect, organize, and present discovery-relevant material by:

- assembling issue-specific evidence packets from governed repository records;
- preserving traceability back to source documents, chunks, facts, and composites;
- standardizing packet structure across matters and work products;
- reducing omissions, duplication, and inconsistent packet construction;
- enabling repeatable packet regeneration under deterministic rerun rules.

---

## 4. In-Scope Responsibilities

`DISCOVERY_PACKET` is responsible for:

- receiving a governed packet request;
- resolving packet scope, issue scope, or request scope from approved inputs;
- retrieving only approved, contract-compliant source references through authorized interfaces;
- assembling packet sections according to deterministic ordering rules;
- organizing packet contents around discovery need, issue, event, entity, or request grouping;
- preserving provenance for every included item;
- generating packet metadata and assembly logs;
- producing structured outputs suitable for attorney review or downstream export.

---

## 5. Out-of-Scope Responsibilities

`DISCOVERY_PACKET` is not responsible for:

- making final legal judgments or strategic attorney recommendations;
- drafting final signed discovery responses for service;
- deciding relevance beyond governed selection rules and approved mappings;
- modifying source evidence or normalized facts;
- creating new facts not supported by provenance-linked material;
- changing legal theories, claims, defenses, or burden positions;
- directly calling tools outside the governed tool gateway;
- overriding attorney decisions, privilege calls, or work-product restrictions.

---

## 6. Trigger Conditions

The program may execute when one or more of the following occur:

- an attorney or authorized human requests assembly of a discovery support packet;
- a workflow requests a packet for a defined issue, claim, defense, witness, event cluster, or discovery demand;
- a downstream program requires a discovery-ready evidence package;
- a rerun is requested under approved rerun governance;
- a matter-specific milestone requires packet generation for review.

Execution must occur only within approved workflow state and with a valid `run_id`.

---

## 7. Required Inputs

The program requires a governed request payload that may include:

- `matter_id`
- `run_id`
- `packet_request_id`
- `packet_type`
- `packet_scope`
- `issue_ids`
- `claim_ids`
- `defense_ids`
- `event_ids`
- `entity_ids`
- `witness_ids`
- `request_ids`
- `attorney_instructions`
- `approval_context`
- `rerun_level`

The program may also require access to approved repository records such as:

- normalized facts
- fact-to-source links
- source document metadata
- `Doc_UID`
- `Chunk_UID`
- composite events
- entity mappings
- chronology segments
- burden mappings
- coverage mappings
- complaint parses
- discovery request mappings
- prior packet manifests when rerunning or updating

All inputs must be governed, schema-compliant, and provenance-preserving.

---

## 8. Input Preconditions

Before execution, the following must be true:

- the matter exists in governed state;
- the request is authorized for the matter and workflow state;
- referenced IDs are valid and resolvable;
- source materials referenced by the packet are available through governed interfaces;
- privilege and access controls have already been applied upstream or are available as governed filters;
- packet scope is sufficiently defined for deterministic assembly;
- required schemas and manifest references are present and hash-valid.

If preconditions are not met, the program must fail safely and emit an auditable error outcome.

---

## 9. Core Processing Logic

The `DISCOVERY_PACKET` program performs the following deterministic sequence:

1. validate the request payload and execution context;
2. resolve packet purpose, scope, and grouping rules;
3. retrieve only authorized records through approved interfaces;
4. apply governed inclusion and exclusion rules;
5. assemble materials into ordered packet sections;
6. attach provenance for each included fact, document, chunk, event, or entity reference;
7. build packet metadata, manifest, and audit references;
8. emit structured packet outputs and execution ledger entries.

Assembly logic must be deterministic given the same approved inputs, same contract version, and same repository state.

---

## 10. Deterministic Ordering Rules

To prevent drift, packet construction must follow deterministic ordering rules such as:

- packet sections ordered by contract-defined section sequence;
- issues ordered by canonical identifier or approved matter order;
- events ordered chronologically using governed event dates and tie-break rules;
- evidence items ordered by ranking rules defined in the request or default contract order;
- documents ordered by canonical identifiers when no higher-priority order is defined;
- duplicate references suppressed using canonical provenance keys.

Where ranking or grouping is configurable, the configuration must be part of governed input and logged in the run context.

---

## 11. Output Artifacts

The program may produce one or more of the following governed outputs:

- discovery packet manifest
- discovery packet summary
- issue-based evidence packet
- request-specific support packet
- witness/event packet
- attorney review packet
- packet assembly log
- packet provenance map
- structured export payload for downstream drafting or review programs

Outputs must be structured, reproducible, and tied to the originating `run_id`.

---

## 12. Output Requirements

Every output must:

- identify the matter and packet request;
- include packet type and scope;
- preserve provenance for included records;
- identify assembly timestamp and `run_id`;
- identify contract version and program version context;
- distinguish source-derived content from generated organization;
- support downstream audit and review;
- avoid unsupported narrative claims;
- exclude records blocked by access, privilege, or policy filters.

---

## 13. Provenance and Traceability

For every included item, the program must preserve traceability to applicable governed keys, which may include:

- `Doc_UID`
- `Chunk_UID`
- fact identifiers
- composite event identifiers
- entity identifiers
- request identifiers
- source repository references
- prior program output identifiers where applicable

No evidence item may appear in a packet without a recoverable provenance path.

---

## 14. Tool and Interface Policy

`DISCOVERY_PACKET` may only use tools and data access methods exposed through the governed tool gateway and approved program interfaces.

The program must not:

- call tools directly;
- access unregistered external systems;
- write around the audit ledger;
- bypass access control, privilege filters, or approval gates;
- mutate source-of-truth records unless explicitly authorized by another governed program and schema.

All tool usage must be logged under the active `run_id`.

---

## 15. Data Governance Rules

The program shall operate under the following governance constraints:

- single source of truth records remain authoritative;
- packet generation is derivative, not authoritative over source evidence;
- no silent rewriting of normalized facts;
- no unsupported extrapolation presented as fact;
- no deletion or concealment of provenance;
- no inclusion of blocked or excluded records;
- no schema drift outside manifest-governed change control.

---

## 16. Human Review Boundary

Attorney or authorized human review remains required for:

- final legal use of any packet;
- service-ready discovery responses;
- privilege determinations;
- work-product judgments;
- strategic use of included or excluded materials;
- decisions about whether packet contents are sufficient for filing, response, or production.

This program supports attorney work; it does not replace attorney judgment.

---

## 17. Failure Modes

The program must fail safely when any of the following occur:

- invalid or incomplete packet request;
- unresolved issue, event, entity, or request identifiers;
- missing provenance for candidate materials;
- unauthorized access attempt;
- schema mismatch or manifest drift;
- unavailable required inputs;
- deterministic ordering ambiguity not resolved by contract rules;
- gateway/tool failure.

Failure outputs must be auditable and must not silently emit partial packets as complete unless explicitly marked as partial under governed rules.

---

## 18. Observability and Audit Requirements

Each execution must record auditable information including:

- program name
- `run_id`
- request identifier
- packet type
- packet scope
- input validation result
- included/excluded counts
- output artifact identifiers
- failure codes where applicable
- rerun context where applicable
- contract and manifest references

Audit entries must support reconstruction of how the packet was assembled.

---

## 19. Rerun and Replay Governance

Reruns are permitted only under governed rerun policy.

A rerun must:

- preserve linkage to the prior run where applicable;
- identify rerun reason;
- respect rerun level rules;
- produce deterministic output when inputs and repository state are unchanged;
- clearly distinguish regenerated outputs from prior versions.

No silent replacement of prior packet outputs is allowed outside governed retention rules.

---

## 20. Security and Access Controls

The program must respect:

- matter-level authorization;
- role-based access rules;
- privilege and confidentiality constraints;
- approved document visibility rules;
- auditability of all read and write activity through governed interfaces.

Restricted content must not be exposed in output artifacts to unauthorized users or workflows.

---

## 21. Dependencies

`DISCOVERY_PACKET` may depend on governed outputs or repositories associated with programs such as:

- `FACT_NORMALIZATION`
- `COMPLAINT_PARSE`
- `COVERAGE_ANALYSIS`
- `BURDEN_MAP_BUILDER`
- `MTC_READINESS_EVALUATOR`
- governed entity, event, chronology, and evidence repositories
- workflow control and audit ledger services

Dependencies must be resolved through manifest-approved references and interfaces only.

---

## 22. Acceptance Criteria

The contract is acceptable when:

- program scope is clearly defined;
- required inputs and outputs are governed and traceable;
- deterministic packet assembly rules are documented;
- provenance requirements are explicit;
- tool usage is gateway-only;
- human review boundaries are preserved;
- failure, audit, and rerun behavior are documented;
- no unauthorized mutation or legal decision-making is implied.

---

## 23. Human Presentation Lens

### Business View

`DISCOVERY_PACKET` is the packaging layer that turns governed litigation data into attorney-usable discovery bundles. It helps legal teams move from “the repository contains the right material” to “the right material is organized for the right discovery purpose.”

### Operational View

This program reduces manual hunting, sorting, and re-packaging of evidence by consistently assembling issue-focused and request-focused support packets using governed IDs, approved mappings, and deterministic ordering.

### Technical View

Technically, `DISCOVERY_PACKET` is a deterministic assembly program. It does not create new evidence or legal reasoning. It reads approved records through governed interfaces, organizes them by contract rules, preserves provenance, and emits auditable packet artifacts.

### Human Trust Message

An attorney should be able to trust that every packet assembled by this program can be traced back to governed source material, rerun consistently, and reviewed without hidden logic or unexplained evidence movement.
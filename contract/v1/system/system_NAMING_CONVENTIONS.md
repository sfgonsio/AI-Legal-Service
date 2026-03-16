# system_NAMING_CONVENTIONS
(Authoritative System Contract — v1 | Naming, Identity, and Reference Discipline)

---

## 1. Purpose

This document defines the authoritative naming conventions for Contract v1 of the AI Legal Service Platform.

Its purpose is to ensure that all governed artifacts are:

- uniquely identifiable
- machine-discoverable
- CI-validatable
- orchestration-safe
- readable by humans
- stable across replay, rerun, audit, and future implementation work

Naming is not cosmetic in this platform. Naming is part of system integrity.

If artifact names drift, then contract resolution, manifest validation, orchestration routing, and audit traceability become unreliable.

This contract exists to prevent that drift.

---

## 2. Scope

This naming contract governs all versioned artifacts within `contract/v1`, including but not limited to:

- system contracts
- program contracts
- agent contracts
- schemas
- tools
- taxonomies
- templates
- orchestration artifacts
- test fixtures
- manifests
- acceptance artifacts
- documentation that is contract-addressable by the platform

This contract does not govern casual working notes, scratch files, or temporary local-only drafts that are not part of the governed contract surface.

Once an artifact is referenced by the manifest, validator, CI, orchestration logic, or platform build instructions, this naming contract applies.

---

## 3. Naming Design Principles

All governed names must follow these principles:

1. **Deterministic**
   - A component’s type should be inferable from its name.

2. **Prefix-resolved**
   - The artifact class must be visible from the leading token.

3. **Stable**
   - Names must not be changed casually once referenced by other governed artifacts.

4. **Readable**
   - Humans must be able to understand the artifact’s role from its name.

5. **Machine-enforceable**
   - CI and validators must be able to test compliance using deterministic rules.

6. **Non-ambiguous**
   - A name must not leave doubt as to whether an artifact is an agent, program, schema, or system contract.

---

## 4. Core Prefix Rules

All governed artifacts MUST use a layer/type prefix.

### Canonical prefixes

- `system_` — system-level contracts and platform-wide governing documents
- `program_` — deterministic execution modules
- `agent_` — reasoning or workflow agents
- `schema_` — formal schema definitions
- `tool_` — tool contracts or governed tool definitions
- `taxonomy_` — controlled vocabularies, legal structures, or classification authorities
- `template_` — reusable authoring templates not themselves executable contracts

These prefixes are mandatory unless an exception is explicitly defined in this contract.

---

## 5. Canonical Artifact Naming Patterns

### 5.1 System contracts

Pattern:

`system_<NAME>.md`

Examples:

- `system_STACK_ARCHITECTURE.md`
- `system_REASONING_MODEL.md`
- `system_STATE_MODEL.md`
- `system_TOOL_GATEWAY.md`
- `system_NAMING_CONVENTIONS.md`

### 5.2 Program contracts

Pattern:

`program_<NAME>.md`

Examples:

- `program_FACT_NORMALIZATION.md`
- `program_COMPOSITE_ENGINE.md`
- `program_COA_ENGINE.md`

Programs are deterministic modules and must always use the `program_` prefix.

### 5.3 Agent contracts

Pattern:

`agent_<NAME>.md`

Examples:

- `agent_INTERVIEW_AGENT.md`
- `agent_MAPPING_AGENT.md`
- `agent_COA_REASONER.md`

Agents must always use the `agent_` prefix even when the semantic name already contains the word `AGENT`.

Correct:
- `agent_INTERVIEW_AGENT`

Incorrect:
- `INTERVIEW_AGENT`

Correct:
- `agent_MAPPING_AGENT`

Incorrect:
- `MAPPING_AGENT`

### 5.4 Schema artifacts

Pattern:

`schema_<NAME>.<ext>`

Examples:

- `schema_EVIDENCE_FACT.json`
- `schema_EVENT_CANDIDATE.json`
- `schema_COA_ELEMENT_COVERAGE_MATRIX.json`

### 5.5 Tool contracts

Pattern:

`tool_<NAME>.md`

Examples:

- `tool_OCR_PARSER.md`
- `tool_TEXT_EXTRACTION.md`

### 5.6 Taxonomies

Pattern:

`taxonomy_<NAME>.<ext>`

Examples:

- `taxonomy_COA.json`
- `taxonomy_TAGS.yaml`

### 5.7 Templates

Pattern:

`template_<NAME>.md`

Examples:

- `template_AGENT_CONTRACT.md`
- `template_PROGRAM_CONTRACT.md`

Templates are not executable platform units and must never be named as if they are live agents or live programs.

---

## 6. Naming Format Rules

Unless a specific exception is defined, governed artifact names must follow these rules:

- use ASCII characters only
- use underscore separators, not spaces
- do not use hyphens inside governed artifact names
- do not use camelCase
- do not use mixed separator styles
- use uppercase semantic tokens after the prefix where that style is already established in Contract v1
- preserve exact prefix casing as lowercase
- preserve file extension consistency

### Required pattern form

`<lowercase_prefix>_<UPPERCASE_OR_STABLE_NAME>.<extension>`

Examples:

- `program_FACT_NORMALIZATION.md`
- `agent_MAPPING_AGENT.md`
- `system_STATE_MODEL.md`

---

## 7. Identity Rules

The artifact filename, declared artifact identity inside the document, and manifest reference must match.

### Example rule

If the file is:

`program_FACT_NORMALIZATION.md`

then the declared identity inside the contract must also be:

`program_FACT_NORMALIZATION`

The same applies to agents, systems, schemas, tools, taxonomies, and templates where internal identity is declared.

### Identity mismatch is non-compliant

The following are invalid:

- filename says `agent_MAPPING_AGENT.md` but document says `MAPPING_AGENT`
- manifest says `./agents/agent_INTERVIEW_AGENT.md` but contract declares `INTERVIEW_AGENT`
- file says `program_COA_ENGINE.md` but internal name says `COA_ENGINE`

---

## 8. Reference Rules

All governed references between artifacts must use canonical names.

References in contracts, manifests, schemas, orchestration files, validators, and acceptance artifacts must not use shorthand aliases unless those aliases are explicitly defined in a controlled alias map.

### Required behavior

Use:

- `agent_INTERVIEW_AGENT`
- `agent_MAPPING_AGENT`
- `program_FACT_NORMALIZATION`
- `program_COMPOSITE_ENGINE`
- `program_COA_ENGINE`

Do not use:

- `INTERVIEW_AGENT`
- `MAPPING_AGENT`
- `FACT_NORMALIZATION`
- `COMPOSITE_ENGINE`
- `COA_ENGINE`

except in explanatory prose where no machine interpretation is implied.

---

## 9. Path and Directory Alignment

Artifact names must align with their governed directory location.

Examples:

- `contract/v1/agents/agent_INTERVIEW_AGENT.md`
- `contract/v1/programs/program_FACT_NORMALIZATION.md`
- `contract/v1/system/system_NAMING_CONVENTIONS.md`
- `contract/v1/templates/template_AGENT_CONTRACT.md`

A valid governed artifact must not have a name that conflicts with its directory class.

### Invalid examples

- `contract/v1/agents/MAPPING_AGENT.md`
- `contract/v1/programs/COA_ENGINE.md`
- `contract/v1/system/STATE_MODEL.md`

---

## 10. Reserved Meanings

The following prefixes are reserved and may not be repurposed:

- `system_`
- `program_`
- `agent_`
- `schema_`
- `tool_`
- `taxonomy_`
- `template_`

No governed artifact may introduce a new top-level executable prefix without explicit approval and revision to this contract.

Examples of disallowed ungoverned prefixes unless formally added later:

- `engine_`
- `service_`
- `module_`
- `worker_`
- `processor_`

If a deterministic executable unit exists, it must currently be modeled as a `program_`.

If a reasoning or workflow unit exists, it must currently be modeled as an `agent_`.

---

## 11. Human-Readable Labels vs Canonical Names

The platform may display friendly labels in presentation materials, UI text, or attorney-facing documentation.

Examples:

- “Interview Agent”
- “Mapping Agent”
- “Fact Normalization Engine”
- “COA Coverage Engine”

These are human-readable labels only.

They do not replace canonical governed names.

### Canonical-to-label examples

- `agent_INTERVIEW_AGENT` → “Interview Agent”
- `agent_MAPPING_AGENT` → “Mapping Agent”
- `program_FACT_NORMALIZATION` → “Fact Normalization Engine”
- `program_COA_ENGINE` → “COA Coverage Engine”

All manifests, contracts, validators, schemas, orchestration logic, and build instructions must continue using canonical names.

---

## 12. Alias Policy

Aliases are discouraged.

A governed alias may exist only if:

- it is explicitly documented
- it is non-authoritative
- it is presentation-only or migration-only
- it cannot be mistaken for the canonical identifier

No alias may appear in place of the canonical name inside:

- manifest references
- validator logic
- orchestration routing
- schema bindings
- audit records
- execution ledgers
- authoritative write paths

---

## 13. Migration Rule for Existing Drift

Where naming drift already exists, the platform must normalize to canonical prefix-based names.

### Current normalization requirements

Normalize:

- `INTERVIEW_AGENT` → `agent_INTERVIEW_AGENT`
- `MAPPING_AGENT` → `agent_MAPPING_AGENT`

Retain:

- `program_FACT_NORMALIZATION`
- `program_COMPOSITE_ENGINE`
- `program_COA_ENGINE`

No new artifact may perpetuate old shorthand naming once this contract is active.

If older shorthand names appear in notes or legacy drafts, they must be treated as non-canonical.

---

## 14. Manifest and Validator Enforcement

This contract is intended to be enforced by:

- `contract_manifest.yaml`
- validation scripts
- CI checks
- future orchestration loading rules

Minimum validator expectations should include:

- filename prefix compliance
- directory-to-prefix compliance
- internal declared identity match
- manifest reference match
- rejection of known shorthand drift for governed artifacts

---

## 15. Audit and Replay Implications

Canonical names are part of platform auditability.

Audit events, run records, supersession logs, replay artifacts, and provenance fields must use canonical governed names.

This ensures:

- replay comparability
- deterministic routing
- stable lineage
- human traceability
- implementation portability

If artifact names change without governance, audit continuity breaks.

For that reason, renaming a governed artifact is a controlled architectural event, not a casual refactor.

---

## 16. Exceptions Policy

Exceptions are not allowed by default.

Any naming exception must:

- be explicitly documented
- state why the standard naming rule is insufficient
- identify all affected artifacts
- define enforcement behavior
- be approved through governed contract change control

Until such approval exists, standard naming rules remain mandatory.

---

## 17. Compliance Criteria

This contract is satisfied when all of the following are true:

- every governed artifact uses an approved prefix
- file names match artifact class
- internal identities match file names
- manifest references match canonical names
- shorthand executable names are absent from governed references
- existing drifted agent names are normalized
- validator and CI enforcement can be added without renaming the architecture again

---

## 18. Human Presentation Lens

This contract ensures the platform has one stable naming language.

To attorneys and stakeholders, that may seem like a small technical detail.

It is not.

Stable naming is what allows the system to:

- know what each component is
- validate the architecture automatically
- route execution safely
- preserve audit lineage
- scale without confusion

This is one of the controls that keeps the platform from turning into an ungoverned tangle of files and labels.

---

## 19. Authority Statement

This document is authoritative for Contract v1 naming discipline.

Where naming conflicts exist, this contract governs unless superseded through approved change control.

All future governed artifacts added to Contract v1 must comply with this naming standard.
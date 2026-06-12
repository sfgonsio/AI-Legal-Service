# CASECORE — CW Directive: Modular Legal Library Agent Control Plane

## Discovery: Contract v1 Authority Spine Already Exists

`contract/v1/knowledge/authority_catalog.yaml` is present in the repository and contains structured authority records. It is treated as an **existing Contract v1 legal-spine scaffold / authority-index** that the legal-library program must reconcile with — not replace, not mutate, not treat as complete canonical law.

Observed shape per entry (example `CACI_1900`):

```yaml
CACI_1900:
  title: "Intentional Misrepresentation"
  elements:
    - element_id: misrepresentation
      proof_types: [communications, documents]
    - element_id: knowledge_of_falsity
      proof_types: [internal_records, testimony]
    - element_id: intent_to_induce_reliance
      proof_types: [context_evidence]
    - element_id: justifiable_reliance
      proof_types: [reliance_actions]
    - element_id: damages
      proof_types: [financial_records]
```

Interpretation:

- Top-level key is the authority ID (e.g., `CACI_1900`).
- `title` is a short authority title.
- `elements` is an ordered list of element records, each with a stable `element_id` and a list of `proof_types`.
- `proof_types` are evidence-mapping hints (e.g., `communications`, `documents`, `internal_records`, `testimony`, `context_evidence`, `reliance_actions`, `financial_records`) — they are **not** legal authority.

## Boundaries on the Existing Catalog

- The file `contract/v1/knowledge/authority_catalog.yaml` **must not be replaced** by any legal-library workflow.
- The file **must not be mutated** by any agent, skill, or ingestion path until a reconciliation plan is approved.
- `proof_types` are evidence-mapping hints, not legal authority. They may inform mapping logic but may not be cited as law and may not be used to overwrite canonical text.
- Authority IDs in this catalog are **spine indices**; canonical source text must come from official/legal authoritative sources stored separately.
- Catalog (spine-index) and canonical authority files (source text + provenance) are separate layers; neither may overwrite the other implicitly.

---

## MANDATORY PREFLIGHT: CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

**Mode:** INSPECT / RECONCILE / REPORT ONLY
**Status gate:** Must complete and be reviewed before any legal-library agent, skill, ingestion path, canonical authority file, or human-readable library file is created or modified.

**Required report (all twelve items, in order):**

1. Does `contract/v1/knowledge/authority_catalog.yaml` exist? (path, size, last-modified, commit of last touch)
2. What top-level authority IDs are present? (full enumerated list)
3. Which authority families are represented? (e.g., CACI jury instructions, California Evidence Code, statutes, regulations, rules of court — grouped by prefix/namespace)
4. What fields exist per record? (full field inventory across all records, noting which fields are universal vs. partial)
5. What element structures exist? (shape of `elements`, presence/absence of element ordering, sub-element nesting, optional/required markers)
6. What `proof_types` are used? (full enumerated list of distinct values with frequency)
7. What canonical / source / provenance fields are **missing**? (e.g., `canonical_text`, `source_url`, `source_publisher`, `effective_date`, `version`, `retrieved_at`, `checksum`)
8. What review / promotion fields are **missing**? (e.g., `review_status`, `reviewer`, `reviewed_at`, `promotion_state`, `supersedes`, `superseded_by`)
9. How should this catalog relate to canonical JSON authority files? (proposed boundary: catalog is index/spine; canonical JSON holds authoritative text + provenance; catalog references canonical JSON by ID, never inlines authority text)
10. How should this catalog relate to human-readable library files? (proposed boundary: human-readable library is rendered from canonical JSON, not from the catalog; catalog informs structure, not content)
11. How should agents use this catalog without mutating canonical law? (proposed boundary: read-only consumption of the catalog and canonical JSON; any proposed change goes through a review/promotion gate, never direct write)
12. What changes are recommended to the control-plane file before any agent/skill creation? (delta proposal listing each control-plane section that must be added/revised based on findings 1–11)

**Output of preflight:** A single structured report — no file mutations, no DB writes, no agent invocations beyond read-only inspection. Report is reviewed and approved before any downstream legal-library work proceeds.

**Until this preflight is completed and explicitly approved, no agent creation, no skill creation, no law ingestion, no canonical mutation, no catalog mutation, no Render DB writes, no commits, and no pushes are authorized.**

---

**Document status:** Integrated control-plane directive for CW.
**Execution mode requested:** Create the modular agent/skill control-plane files only.
**Do not ingest law yet. Do not mutate canonical authority yet. Do not write to Render DB yet.**
**Do not proceed past the CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION preflight without explicit approval.**

---

## 0. Executive Instruction to CW

CW, build the CaseCore legal-library AI agent control plane as a **modular agent + skill system**, not as one giant agent file or one giant skill file.

The legal library already exists, but it is incomplete. The immediate work is to create the governed agent/skill structure that will later allow expert agents to complete the legal library by identifying legally authoritative sources, capturing and normalizing authority, validating correctness, promoting only verified authority into the canonical spine, storing approved authority in the Render database, and generating the human-readable library.

**This execution is limited to creating the control-plane files.**

### Authorized in this execution

Create or update the following control-plane/documentation files:

```text
LEGAL_SPINE_DOCTRINE.md
LEGAL_SOURCE_HIERARCHY.md
AUTHORITY_INTAKE_MANIFEST_SCHEMA.md
AUTHORITY_PACK_FORMAT.md
HUMAN_READABLE_LIBRARY_FORMAT.md
CANONICAL_PROMOTION_GATE.md
REJECTION_QUARANTINE_PROTOCOL.md
RENDER_DB_AUTHORITY_MODEL.md
contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md

.claude/agents/AGENT_LEGAL_LIBRARY_PROGRAM_CONTROLLER.md
.claude/agents/AGENT_CANONICAL_SPINE_GOVERNOR.md
.claude/agents/AGENT_LEGAL_SOURCE_VERIFIER.md
.claude/agents/AGENT_AUTHORITY_NORMALIZER.md
.claude/agents/AGENT_EXPERT_JUDGE_AUTHORITY_REVIEWER.md
.claude/agents/AGENT_EXPERT_ATTORNEY_COA_REVIEWER.md
.claude/agents/AGENT_HUMAN_LIBRARY_WRITER.md
.claude/agents/AGENT_NO_DRIFT_GOVERNOR.md

.claude/skills/legal-library/SKILL_SOURCE_DISCOVERY.md
.claude/skills/legal-library/SKILL_SOURCE_VERIFICATION.md
.claude/skills/legal-library/SKILL_AUTHORITY_CAPTURE.md
.claude/skills/legal-library/SKILL_AUTHORITY_NORMALIZATION.md
.claude/skills/legal-library/SKILL_PROVENANCE_HASHING.md
.claude/skills/legal-library/SKILL_CANONICAL_BOUNDARY_CHECK.md
.claude/skills/legal-library/SKILL_COMPLETENESS_SCORING.md
.claude/skills/legal-library/SKILL_PROMOTION_PACKET.md
.claude/skills/legal-library/SKILL_REJECTION_QUARANTINE.md
.claude/skills/legal-library/SKILL_HUMAN_READABLE_RENDERING.md
.claude/skills/legal-library/SKILL_JUDGE_REVIEW.md
.claude/skills/legal-library/SKILL_ATTORNEY_COA_REVIEW.md
```

### Not authorized in this execution

```text
No law ingestion.
No Render DB writes.
No canonical authority mutation.
No schema migration.
No source scraping.
No authority-pack promotion.
No case evidence use.
No UI work.
No commits or pushes until Steve reviews staged diff and explicitly authorizes.
```

---

## 1. Non-Negotiable Canonical Spine Doctrine

The **spine is canonical legal authority**.

Evidence is **not** the spine.  
Actors are **not** the spine.  
Timeline is **not** the spine.  
Triangulation is **not** the spine.  
AI proposals are **not** the spine.  
Attorney strategy is **not** the spine.

The entire case is viewed through the lens of legal authority.

```text
LEGAL LIBRARY / AUTHORITY PACKS
        ↓
CANONICAL SPINE
        ↓
Case-specific analysis
Evidence mapping
COA proposals
Burden mapping
Remedy mapping
Complaint drafting
War Room strategy
Attorney directives / interpretation overlays
AI proposals
```

One-way boundary:

```text
Canonical authority may flow outward into non-canonical analysis.

Non-canonical, commingled, inferred, evidence-derived, AI-generated,
attorney-strategy, timeline, actor, triangulation, or case-specific material
may NEVER flow back into canonical authority.
```

Hard controls:

```text
No drift.
No hallucination.
No fabrication.
No evidence-driven mutation of law.
No AI-created authority.
No case facts modifying canonical law.
Legal authority governs.
Evidence is mapped to the spine.
AI proposes mappings.
Attorney approves case-specific use.
Canonical authority remains pristine.
```

### 1.A Layer Separation Doctrine — Spine Index vs Canonical Authority vs Human-Readable Library

Three distinct layers exist and may not be conflated:

```text
Layer 1 — Spine Index (authority catalog)
  contract/v1/knowledge/authority_catalog.yaml
  Holds: authority IDs, titles, element structure, proof_type hints.
  Does NOT hold: canonical text, provenance, official citation, version metadata.
  Mutation rule: read-only from agents; structural changes require explicit reconciliation approval.

Layer 2 — Canonical Authority Files (machine-readable structured law)
  /legal/canonical/
  Holds: official_text, normalized_text, citation, source provenance, version, hashes, review state.
  Mutation rule: only via approved canonical promotion gate.

Layer 3 — Human-Readable Library
  Human-readable pages rendered downstream from Layer 2.
  Holds: plain-English explanation, legal use notes, COA/burden/remedy connections.
  Mutation rule: regenerated from Layer 2; never edited as upstream source.
```

Direction-of-flow rules:

```text
Spine Index (Layer 1) ──references──▶ Canonical Authority (Layer 2)
Canonical Authority (Layer 2) ──rendered as──▶ Human-Readable Library (Layer 3)

Layer 3 may NEVER write back to Layer 2.
Layer 2 may NEVER write back to Layer 1 implicitly.
Layer 1 entries may NEVER inline authoritative text — they reference canonical entries by ID.
```

Additional invariants:

- `proof_types` in the spine index are evidence-mapping hints, not legal authority. They inform mapping logic; they do not establish or modify law.
- Canonical source text must come from official/legal authoritative sources (see Section 5).
- Non-canonical metadata (proof_types, mapping hints, review notes) may not mutate canonical law under any circumstance.

---

## 2. Architectural Placement: Stage-Gate Agents vs Utility / Canonical Spine Agents

CaseCore previously established a stage-gate agent architecture:

```text
Layer A — Build / Governance agents
Layer B — Runtime agents
```

Layer B includes stage-gate agents:

```text
INTAKE_AGENT
CASE_BUILD_AGENT
DISCOVERY_AGENT
TRIAL_AGENT
DECISION_AGENT
CLOSURE_AGENT
```

And cross-cutting agents:

```text
WAR_ROOM_AGENT
UTILITY_AGENT
```

### Legal-library agents are not normal stage-gate runtime agents

The legal-library completion program belongs under the **canonical-spine / utility-governance layer**, not beneath any single stage gate.

```text
Layer A / Build-Governance:
  AGENT_CANONICAL_SPINE_GOVERNOR
  AGENT_NO_DRIFT_GOVERNOR
  AGENT_LEGAL_LIBRARY_PROGRAM_CONTROLLER

Layer B Cross-Cutting / Utility:
  UTILITY_AGENT
    └─ LEGAL_LIBRARY_SUB
    └─ AUTHORITY_PACK_SUB
    └─ SOURCE_VERIFICATION_SUB
    └─ NORMALIZATION_SUB
    └─ HUMAN_LIBRARY_SUB
```

Stage-gate agents consume the canonical spine, but they never mutate it.

```text
CASE_BUILD_AGENT uses the spine to form COA / burden / remedy mappings.
DISCOVERY_AGENT uses the spine to identify discovery gaps and evidentiary burdens.
TRIAL_AGENT uses the spine for admissibility, exhibit, burden, and jury-instruction work.
DECISION_AGENT uses the spine for standards, burdens, and judgment analysis.
```

But no stage-gate agent owns or rewrites legal authority.

---

## 3. Thin Agents, Discrete Skills

Do **not** create one huge agent file.  
Do **not** create one huge skill file.

Use:

```text
Thin agents
+ small discrete skills
+ explicit skill-use conditions
+ mandatory output contracts
+ promotion gates
```

### Agent files should contain

```text
mission
allowed actions
forbidden actions
skills it may invoke
when to stop
required output contract
```

### Skill files should contain

```text
use when
do not use when
inputs
procedure
outputs
validation rules
failure modes
test fixture expectations
```

Agents are role controllers. Skills hold reusable procedures.

---

## 4. Authority Coverage Requirement

The canonical legal library must support:

```text
Federal law
State law
County law
City law
Industry-specific law
GAAP / authoritative accounting standards
Internal Revenue Code / Federal Tax Code
Treasury Regulations
IRS guidance
```

Known current state:

```text
Some California Jury Instructions exist.
Some California Evidence Code exists.
These are incomplete and must be completed.
```

The first inventory must determine what exists, what is complete, what is authoritative, what is only reference, and what is missing.

---

## 5. Authoritative Source Hierarchy

Use official or legally authoritative sources first. Secondary sources may assist research but may never become canonical authority.

| Authority type | Accepted source priority |
|---|---|
| Federal statutes | Official U.S. Code / official government source |
| Federal regulations | eCFR, CFR, agency official sources, GovInfo where appropriate |
| State statutes | Official state legislative source |
| State jury instructions | Official judicial council / official court source |
| County law | Official county code, county court, county agency, or official code publisher under county authority |
| City law | Official municipal code, city agency, or official code publisher under city authority |
| Industry law | Official regulator, licensing body, statutory scheme, rulemaking authority, agency guidance |
| GAAP | FASB Accounting Standards Codification / official FASB materials or authorized access pathway |
| Internal Revenue Code / Federal Tax Code | Official IRC / U.S. Code Title 26 / official federal tax source |
| Treasury Regulations | Code of Federal Regulations Title 26, eCFR, Treasury official materials |
| IRS guidance | IRS official guidance, Revenue Rulings, Revenue Procedures, Notices, Announcements, Internal Revenue Bulletin |

Source verifier must document source authority, access date, version/effective date, jurisdiction, and citation completeness.

---

## 6. Proposal Space vs Canonical Space

Agents may write only into proposal/review/draft space until explicit promotion.

Allowed proposal/review locations:

```text
/proposals/legal_authority/
/drafts/authority_normalization/
/review/legal_source_verification/
/review/judge_review/
/review/attorney_review/
/review/no_drift_review/
/quarantine/legal_authority/
```

Restricted canonical location:

```text
/legal/canonical/
```

No agent may write directly into `/legal/canonical/` without an explicit canonical promotion gate approval.

---

## 7. Authority Intake Manifest Schema

Every authority item must have a manifest before review or promotion.

```json
{
  "authority_id": "CACI_1900",
  "jurisdiction": "California",
  "authority_level": "state",
  "authority_type": "jury_instruction",
  "source_name": "Judicial Council of California Civil Jury Instructions",
  "source_url": "...",
  "source_accessed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "effective_date": "YYYY-MM-DD|null",
  "version": "...|null",
  "citation": "...",
  "official_status": "official|authorized|secondary|rejected",
  "source_format": "html|pdf|xml|json|txt|other",
  "capture_method": "manual|api|download|other",
  "provenance_hash": "sha256:...",
  "normalization_status": "not_started|draft|validated|rejected",
  "judge_review_status": "pending|pass|fail|needs_revision",
  "attorney_review_status": "pending|pass|fail|needs_revision",
  "no_drift_review_status": "pending|pass|fail|quarantine",
  "canonical_promotion_decision": "pending|approved|rejected",
  "canonical_promotion_approved_by": null,
  "canonical_promoted_at": null,
  "notes": []
}
```

---

## 8. Canonical Authority Structured Format

Canonical authority must be machine-readable and preserve the original legal meaning.

Required JSON shape:

```json
{
  "authority_id": "EVID_500",
  "authority_type": "statute",
  "jurisdiction": {
    "country": "US",
    "state": "CA",
    "county": null,
    "city": null
  },
  "legal_domain": ["evidence", "burden_of_proof"],
  "citation": {
    "official_citation": "Cal. Evid. Code § 500",
    "short_citation": "EVID 500",
    "source_url": "...",
    "source_name": "California Legislative Information"
  },
  "versioning": {
    "effective_date": "YYYY-MM-DD|null",
    "accessed_at": "YYYY-MM-DDTHH:MM:SSZ",
    "version_label": "...|null",
    "provenance_hash": "sha256:..."
  },
  "text": {
    "official_text": "...",
    "normalized_text": "...",
    "section_title": "...|null"
  },
  "structure": {
    "elements": [],
    "burdens": [],
    "remedies": [],
    "definitions": [],
    "exceptions": [],
    "procedural_requirements": [],
    "admissibility_requirements": []
  },
  "relationships": {
    "supersedes": [],
    "superseded_by": [],
    "references": [],
    "related_authorities": []
  },
  "review": {
    "source_verified": false,
    "normalized": false,
    "judge_reviewed": false,
    "attorney_reviewed": false,
    "no_drift_passed": false,
    "canonical_promoted": false
  }
}
```

---

## 9. Human-Readable Library Format

Human-readable library is downstream from canonical authority.

```text
canonical structured law
        ↓
human-readable markdown / library page
```

Never the reverse.

Required human-readable page sections:

```text
Title
Jurisdiction
Authority Type
Official Citation
Source / Accessed Date
Effective Date / Version
Official Text
Plain-English Explanation
Legal Use
COA / Burden / Remedy Connections
Related Authorities
Review Status
Canonical Status
Warnings / Limitations
```

Human-readable text is not canonical authority.

---

## 10. Render DB Authority Model — Proposed Target, Not Yet Authorized

Do not write to Render DB in this execution. Define the target model for later approval.

Proposed tables:

```text
legal_authority_sources
legal_authority_manifests
legal_authority_items
legal_authority_versions
legal_authority_relationships
legal_authority_reviews
legal_authority_promotion_packets
legal_authority_human_pages
legal_authority_quarantine
```

Minimum fields:

```text
id
authority_id
jurisdiction
authority_level
authority_type
citation
source_url
source_name
source_accessed_at
effective_date
version_label
provenance_hash
canonical_status
review_status
created_at
updated_at
```

Render DB writes require separate schema proposal, approval, migration, staging validation, and deployment validation.

---

## 11. Agent Roster

### AGENT_LEGAL_LIBRARY_PROGRAM_CONTROLLER

Mission: coordinate the legal-library completion workflow across source discovery, verification, normalization, review, promotion, and human-readable rendering.

May invoke: all legal-library skills by condition.

May not: promote canonical authority, write to Render DB, ingest new law without authorization, mutate canonical files.

Output: PROGRAM_PLAN, WORK_QUEUE, AGENT_ASSIGNMENT_PLAN, STOP_REPORT.

### AGENT_LEGAL_SOURCE_VERIFIER

Mission: determine whether a source is legally authoritative enough for intake.

May invoke:

```text
SKILL_SOURCE_DISCOVERY
SKILL_SOURCE_VERIFICATION
SKILL_PROVENANCE_HASHING
SKILL_REJECTION_QUARANTINE
```

May not normalize, rewrite, or promote law.

Output: SOURCE_VERIFICATION_REPORT.

### AGENT_AUTHORITY_NORMALIZER

Mission: transform verified authority into structured machine-readable draft form.

May invoke:

```text
SKILL_AUTHORITY_CAPTURE
SKILL_AUTHORITY_NORMALIZATION
SKILL_PROVENANCE_HASHING
```

May not promote canonical authority or invent missing law.

Output: NORMALIZATION_DRAFT_PACKET.

### AGENT_EXPERT_JUDGE_AUTHORITY_REVIEWER

Mission: review normalized authority for legal correctness, neutrality, completeness, and faithful preservation of official meaning.

May invoke:

```text
SKILL_JUDGE_REVIEW
SKILL_CANONICAL_BOUNDARY_CHECK
```

May not rewrite canonical law, promote authority, or use case evidence.

Output: JUDGE_REVIEW_REPORT.

### AGENT_EXPERT_ATTORNEY_COA_REVIEWER

Mission: review how authority supports COA, burden, remedy, and complaint structures.

May invoke:

```text
SKILL_ATTORNEY_COA_REVIEW
SKILL_CANONICAL_BOUNDARY_CHECK
```

May not mutate official authority or replace law with strategy.

Output: ATTORNEY_REVIEW_REPORT.

### AGENT_CANONICAL_SPINE_GOVERNOR

Mission: enforce canonical promotion rules and protect the spine.

May invoke:

```text
SKILL_CANONICAL_BOUNDARY_CHECK
SKILL_COMPLETENESS_SCORING
SKILL_PROMOTION_PACKET
```

May recommend promotion but may not promote without explicit approval.

Output: CANONICAL_PROMOTION_RECOMMENDATION.

### AGENT_HUMAN_LIBRARY_WRITER

Mission: generate human-readable library pages from approved structured authority.

May invoke:

```text
SKILL_HUMAN_READABLE_RENDERING
```

May not write canonical law or summarize unsupported authority.

Output: HUMAN_LIBRARY_PAGE_DRAFT.

### AGENT_NO_DRIFT_GOVERNOR

Mission: detect hallucination, contamination, unsupported claims, reverse-flow attempts, and canonical boundary violations.

May invoke:

```text
SKILL_CANONICAL_BOUNDARY_CHECK
SKILL_PROVENANCE_HASHING
SKILL_REJECTION_QUARANTINE
```

Output: NO_DRIFT_REVIEW_REPORT.

---

## 12. Skill Registry with Use Conditions

### SKILL_SOURCE_DISCOVERY

Use when no accepted source candidate exists.  
Do not use to normalize or promote authority.  
Output: SOURCE_CANDIDATE_LIST.

### SKILL_SOURCE_VERIFICATION

Use when a candidate source must be accepted, rejected, or quarantined.  
Output: SOURCE_VERIFICATION_REPORT.

### SKILL_AUTHORITY_CAPTURE

Use after source verification passes.  
Output: RAW_AUTHORITY_CAPTURE_PACKET.

### SKILL_AUTHORITY_NORMALIZATION

Use after authority capture.  
Output: NORMALIZED_AUTHORITY_DRAFT.

### SKILL_PROVENANCE_HASHING

Use whenever raw source text or normalized authority is captured.  
Output: HASH_RECORD.

### SKILL_CANONICAL_BOUNDARY_CHECK

Use before review, promotion, or any proposed canonical write.  
Output: BOUNDARY_CHECK_REPORT.

### SKILL_COMPLETENESS_SCORING

Use to score authority pack completeness against expected coverage.  
Output: COMPLETENESS_SCORECARD.

### SKILL_PROMOTION_PACKET

Use only after source verification, normalization, judge review, attorney review, and no-drift review are complete.  
Output: PROMOTION_PACKET.

### SKILL_REJECTION_QUARANTINE

Use when authority fails source, review, or boundary checks.  
Output: QUARANTINE_RECORD.

### SKILL_HUMAN_READABLE_RENDERING

Use only after canonical or approved structured authority exists.  
Output: HUMAN_READABLE_LIBRARY_PAGE.

### SKILL_JUDGE_REVIEW

Use when legal correctness / neutrality / faithful authority preservation must be reviewed.  
Output: JUDGE_REVIEW_REPORT.

### SKILL_ATTORNEY_COA_REVIEW

Use when COA, burden, remedy, pleading, or practical legal application must be reviewed.  
Output: ATTORNEY_COA_REVIEW_REPORT.

---

## 13. Agent-to-Skill Matrix

| Agent | Primary skills |
|---|---|
| AGENT_LEGAL_LIBRARY_PROGRAM_CONTROLLER | all skills by condition |
| AGENT_LEGAL_SOURCE_VERIFIER | discovery, verification, provenance, quarantine |
| AGENT_AUTHORITY_NORMALIZER | capture, normalization, provenance |
| AGENT_EXPERT_JUDGE_AUTHORITY_REVIEWER | judge review, boundary check |
| AGENT_EXPERT_ATTORNEY_COA_REVIEWER | attorney COA review, boundary check |
| AGENT_CANONICAL_SPINE_GOVERNOR | boundary check, completeness scoring, promotion packet |
| AGENT_HUMAN_LIBRARY_WRITER | human-readable rendering |
| AGENT_NO_DRIFT_GOVERNOR | boundary check, provenance, quarantine |

---

## 14. Canonical Promotion Gate

Canonical promotion requires all of the following:

```text
Source verified as official or legally authoritative.
Official text captured accurately.
Jurisdiction confirmed.
Authority type confirmed.
Effective/version date recorded or explicitly unavailable.
Citation complete.
Provenance hash created.
Normalization preserves original meaning.
Judge review passed.
Attorney review passed.
No-drift review passed.
No evidence/case fact influenced authority.
No AI invented authority.
No non-canonical material contaminated the canonical item.
Promotion packet approved by Steve / authorized reviewer.
```

Canonical promotion is not automatic.

---

## 15. Rejection / Quarantine Protocol

Quarantine authority if:

```text
source is unofficial and unsupported
source is outdated and cannot be versioned
citation is incomplete
text cannot be verified
normalization changes legal meaning
AI filled gaps from memory
evidence or case facts influenced authority
jurisdiction is wrong or ambiguous
review agents disagree without resolution
```

Quarantined items may not be used by the canonical spine.

---

## 16. First Executable Slice After Control-Plane Creation

After this control plane is created and reviewed, the first executable slice should be:

```text
LEGAL_LIBRARY_INVENTORY_AND_COMPLETENESS_MAP
```

Purpose:

```text
What exists?
Where did it come from?
Is it canonical or reference?
Is it complete?
Is provenance sufficient?
What is missing?
What first authority pack should be completed?
```

Likely first packs to evaluate:

```text
California Evidence Code complete pack
CACI complete pack
California cannabis / BPC Division 10 pack
```

But CW must confirm by inventory, not assumption.

---

## 17. Execution Requirements for CW

Use small, safe, reviewable steps.

```text
No giant heredocs.
No brittle terminal paste.
No one-file kitchen-sink agent.
No one-file kitchen-sink skill.
No branch creation unless explicitly approved.
Use explicit file paths only.
Stage only authorized files.
Stop before commit.
Stop before push.
```

After creating the modular files, CW must provide:

```text
git status --short
file list created/modified
diff stat
name-only diff
boundary check proving no canonical law mutated
full diff for review
halt before commit
```

---

## 18. Single Execution Prompt for CW

```text
CW — execute the LEGAL_LIBRARY_AGENT_CONTROL_PLANE modularization.

Mode:
WRITE CONTROL-PLANE FILES ONLY.

Objective:
Create the modular CaseCore legal-library agent/skill control plane for completing the canonical legal authority library.

Critical doctrine:
Legal authority is the spine.
Evidence is mapped to the spine.
Canonical authority may flow outward.
Non-canonical, commingled, inferred, evidence-derived, AI-generated, attorney-strategy, timeline, actor, triangulation, or case-specific material may never flow back into canonical authority.
No drift. No hallucination. No fabrication. No evidence-driven mutation of law.

Architecture:
Use the prior stage-gate agent model.
Legal-library agents are cross-cutting canonical-spine / utility-governance agents, not stage-gate runtime agents.
Stage-gate agents consume the canonical spine but never mutate it.

Design:
Thin agents + discrete skills.
Do not create one massive agent file.
Do not create one massive skill file.

Create/update the file set listed in this directive:
- shared doctrine / schema / gate documents
- .claude/agents/*.md files
- .claude/skills/legal-library/*.md files

Each agent file must include:
mission, allowed actions, forbidden actions, skills it may invoke, stop conditions, output contract.

Each skill file must include:
use when, do not use when, inputs, procedure, outputs, validation rules, failure modes.

Do NOT:
- ingest law
- mutate /legal/canonical
- mutate contract/v1/knowledge/authority_catalog.yaml
- write to Render DB
- create or run DB migrations
- promote authority
- use case evidence
- modify application runtime code
- create branches
- commit
- push

After file creation:
provide git status, file list, diff stat, name-only diff, boundary check, and full diff.
Stop before commit.
```

---

## 19. Standing Gates — Reaffirmed

Until the `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` preflight is completed and explicitly approved:

```text
Do not create agents.
Do not create skills.
Do not ingest law.
Do not mutate canonical files.
Do not mutate contract/v1/knowledge/authority_catalog.yaml.
Do not write to Render DB.
Do not commit.
Do not push.
```

These gates are independent of any execution prompt elsewhere in this document. Where Section 0 or Section 18 authorizes control-plane file creation, that authorization is **suspended** until the preflight report has been completed, reviewed, and approved. The preflight gate takes precedence.

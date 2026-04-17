# Legal Reasoning Architecture (Spine + Brain) — Contract v1

**Status:** SSOT (authoritative)  
**Scope:** Civil litigation workflows (initial intake → discovery readiness)  
**Jurisdiction v1:** California  
**Core Principle:** Authority defines structure. Cases provide signals. Deterministic evaluation produces auditable coverage.

---

## 1. Purpose

This document defines the platform’s legally-grounded reasoning architecture. It prevents drift by separating:

- **Spine**: The stable operating system and governance contracts (SSOT, audit, determinism, manifests).
- **Brain**: The legal reasoning machinery built on top of the spine (authority → burdens → signals → coverage).

---

## 2. Design Commitments (Non-Negotiable)

1. **Authority is not case-tailored**
   - CACI / Evidence Code are treated as jurisdiction-bound truth sources.
   - They define what must be proven and admissible evidence constraints.

2. **Cases provide signals, not legal conclusions**
   - Client interviews and documents are treated as raw inputs.
   - Signals are normalized, versioned, and cited.

3. **Deterministic evaluation is required**
   - Coverage scoring must be reproducible and auditable.
   - LLMs may propose drafts, but promotion to SSOT requires human approval.

4. **No silent drift**
   - All authoritative inventories are manifest-listed and hash-locked (where enabled).
   - Fail-fast gates stop missing authority or mismatched bindings.

---

## 3. Layer Model

### 3.1 Authority Layer (Jurisdiction Truth)
**Defines:** Burdens, elements, and evidence constraints.  
**Sources:** CA Jury Instructions (CACI), CA Evidence Code.  
**Artifacts:**
- `knowledge/authority_catalog.yaml` (elements inventory; v1 focuses on CACI)
- `knowledge/evidence_code_catalog.yaml` (future)
- `taxonomies/pattern_packs/archetypes.yaml` (archetype → authority refs)

### 3.2 Mapping Layer (Strict Signal Grammar)
**Defines:** What signals count for which elements and how to assess strength.  
**Artifacts:**
- `pattern_modules/<jurisdiction>/<module>.yaml` (deterministic rules)
- schemas for modules and bundles

### 3.3 Case Layer (Normalized Signals)
**Defines:** Structured signals extracted from interviews and documents, with citations.  
**Artifacts:**
- `case_signal_profile.json` (schema-validated)

### 3.4 Coverage Layer (Burden vs Signals)
**Defines:** Deterministic assessment of signal sufficiency per element, plus gap prompts and evidence asks.  
**Artifacts:**
- `coverage_report.json` (schema-validated)

---

## 4. Canonical Flow

1. **Intake**
   - Client provides narrative via interview; optionally uploads documents.

2. **Normalization**
   - Deterministic programs convert raw inputs → `case_signal_profile.json`.

3. **Archetype Triaging**
   - Deterministic scoring proposes top candidate archetypes (hypotheses).
   - System remains transparent about confidence; asks disambiguation questions.

4. **Burden Map**
   - Deterministic builder uses selected archetype + authority catalog → `burden_map`.

5. **Coverage**
   - Deterministic coverage engine compares burden map → case signals → `coverage_report`.

6. **Outputs**
   - Attorney receives structured understanding + gaps + evidence asks + discovery themes (no advocacy).

---

## 5. Governance Boundaries

### 5.1 LLM Role (Student)
LLMs may:
- draft pattern modules, interview prompts, and archetype proposals
- summarize signals in plain language for clients
- propose missing information questions

LLMs may NOT:
- change authority inventories
- assign definitive legal conclusions
- generate advocacy outputs (motions, arguments) inside deterministic scoring

### 5.2 Attorney Role (Teacher)
Attorney may:
- accept/reject/promote module drafts into SSOT
- validate authority mappings and archetype definitions
- approve progression to higher-stakes outputs

---

## 6. Safety & Credibility Positioning

- System provides **structured understanding** and **gap analysis**, not legal advice.
- All outputs include:
  - scope boundaries
  - confidence statements
  - citations to sources (interview turns / documents)

---

## 7. Acceptance Criteria

A v1 system is correct when:
- authority is complete enough for selected archetypes
- signals are schema-valid with citations
- coverage report is reproducible, element-by-element, with explicit gaps
- attorneys can audit and disagree without the system “arguing”
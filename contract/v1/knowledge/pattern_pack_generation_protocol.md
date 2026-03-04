# Pattern Pack Generation Protocol v1
**Layer:** Brain (Design Protocol / Offline Drafting)  
**Purpose:** Define a repeatable instruction set for using GPT to draft “Pattern Packs” safely (no runtime drift).  
**Key Rule:** GPT may draft; attorneys approve; system promotes/version-controls.

---

## 1) Overview
A Pattern Pack is a constrained composition bundle for a case archetype:

1) **Archetype Definition** (case type + jurisdiction + posture)  
2) **Burden Map** (elements to prove, defenses, burdens)  
3) **Pattern Modules** (questioning behaviors / capture modules)  
4) **Evidence Hygiene Rules** (authentication, custody, privilege, witness sourcing)  
5) **Discovery Triggers** (what to request when gaps exist; M&C/MTC escalation hooks)

This protocol describes how to use GPT to generate first-draft packs from:
- Jury instructions (elements/burdens/defenses)
- Evidence code references (hygiene)
- A known module library (reusable modules)
- Optional: case filing frequency data (to prioritize top archetypes)

---

## 2) Safety Boundary (No Drift)
Pattern Packs MUST NOT be generated live at runtime.
Instead:
- GPT drafts offline artifacts (candidate)
- Attorney reviews (teacher gate)
- Approved packs are promoted into trusted knowledge inventory
- Packs become versioned (and optionally hash-locked)

---

## 3) Inputs Required
### 3.1 Source Materials (authoritative excerpts)
- Jury instruction text for a target set (or curated list)
- Evidence code excerpts or pointers (as needed)

### 3.2 Pattern Module Library (internal)
A canonical library of reusable modules, e.g.:
- timeline_integrity
- container_chain_capture
- agreement_terms_capture
- representation_reliance_capture
- damages_quantification
- authentication_chain_of_custody
- privilege_risk
- credibility_impeachment
- authority_control
- discovery_targeting

Each module includes triggers, required fields, and question clusters.

### 3.3 Optional Priority Inputs
- Case filing frequency by category (if available)
- Firm practice focus weights (employment, PI, business torts, etc.)

---

## 4) Outputs (Candidate Drafts)
GPT must output candidate artifacts in a deterministic structure:

### 4.1 Top Archetypes List (candidate)
A ranked list of top N archetypes with:
- archetype_id
- rationale for inclusion
- target jurisdiction
- likely COA families
- expected pattern modules

### 4.2 Pattern Pack YAML (candidate)
For each archetype:
- burden_map (elements + defenses)
- module_set (default + conditional)
- evidence_hygiene (base + archetype extensions)
- discovery_triggers (gap-driven)
- priority weights (critical fields)

---

## 5) Archetype Identification (Instruction Set for GPT)
### 5.1 Step A — Build Archetype Candidates
From jury instruction corpus:
- Cluster instructions by COA families and recurring element structures
- Produce archetype candidates like:
  - employment_wrongful_termination
  - wage_and_hour
  - breach_of_contract
  - fraud_misrepresentation
  - personal_injury_negligence
  - conversion_trespass_to_chattels
  - real_property_dispute
  - professional_negligence

### 5.2 Step B — Rank to Top 10
Ranking can be done by:
- If filing frequency stats exist: weight by frequency
- Else: use a heuristic score:
  - breadth (how often it appears across clients)
  - element complexity (value of structured capture)
  - evidence intensity (value of hygiene)
  - discovery intensity (value of triggers)
  - firm focus weight (if provided)

GPT must report ranking rationale and uncertainty.

---

## 6) Burden Map Extraction (Instruction Set for GPT)
For each archetype:
- Identify the core jury instruction(s)
- Extract:
  - elements (numbered, plain language)
  - burden of proof notes
  - common defenses (if included)
  - required proof types (documents, testimony, intent, damages)

Output format:
- element_id
- element_name
- element_plain_language
- proof_types
- common_failure_modes (where cases usually fail)

---

## 7) Module Selection Logic (Constrained Composition)
Modules are not random cards. Use constrained mapping:

**Rule 1: Burden Map anchors selection**
- Each element must map to ≥1 module that captures required facts.
- Some modules support many elements (timeline, credibility).

**Rule 2: Narrative triggers add conditional modules**
- If the narrative triggers “access/entry/opening,” add container_chain_capture.
- If the narrative triggers “promised/relied,” add representation_reliance_capture.

**Rule 3: Completeness matrix enforces closure**
- If a critical field is missing, generate follow-up questions.

GPT must output:
- default_modules (always on)
- conditional_modules (triggered by narrative)
- element_to_module_map

---

## 8) Evidence Hygiene Construction (Instruction Set for GPT)
Start with universal hygiene:
- who observed what
- authentication basics (who created it, where stored)
- chain-of-custody
- privilege risk capture

Then add archetype extensions:
- employment → HR file provenance, comparator records, complaint trail
- fraud → financial trace, bank records provenance, reliance proof artifacts
- PI → medical records, treatment timeline, causation documentation

GPT must output hygiene rules as:
- rule_id
- trigger
- required_fields
- sample_questions
- failure_risk (why missing it hurts)

---

## 9) Discovery Triggers Construction (Instruction Set for GPT)
Discovery triggers are gap-driven.

For each burden element:
- define “minimum evidence set”
- if missing, define:
  - interrogatory themes
  - RFP themes
  - deposition objectives
  - meet & confer escalation thresholds
  - MTC readiness prerequisites

Output:
- gap_condition
- discovery_action
- target_custodian_hypothesis
- escalation_gate (M&C required before MTC)

---

## 10) Attorney Review Gate (Teacher Workflow)
GPT outputs remain candidate until attorney review.

Attorney actions:
- Accept (promote)
- Modify (edit module set, wording, weights)
- Reject (discard)
- Add firm style preferences (tone, sequence, sensitivity)

Promotion creates:
- trusted pattern pack version v1
- optional hash-lock for governance

---

## 11) GPT Prompt Templates (Copy/Paste)
### 11.1 Archetype Ranking Prompt
“You are drafting candidate Pattern Packs for jurisdiction: CA.
Using the provided jury instruction corpus (text below) and the module library list (below), propose the Top 10 civil case archetypes to prioritize.
For each archetype:
- archetype_id
- COA families
- why it’s common/valuable (no fabricated stats; cite if stats are provided)
- default modules (from library)
- conditional modules (trigger-based)
Return as structured YAML.”

### 11.2 Burden Map Extraction Prompt
“Extract the burden map from these jury instructions for archetype X.
Output:
- elements (id, name, plain language)
- proof types
- common failure modes
- common defenses (only if present in source text; otherwise mark unknown)
Return as JSON.”

### 11.3 Full Pattern Pack Draft Prompt
“Using:
(A) this burden map JSON
(B) module library catalog
(C) evidence code hygiene checklist
Draft pattern_pack YAML including:
- default_modules
- conditional_modules with triggers
- evidence_hygiene rules
- discovery_triggers by element gap
No legal advice; produce candidate pack for attorney review.”

---

## 12) Acceptance Checklist (For Internal QA)
A candidate Pattern Pack is valid if:
- Every burden element maps to ≥1 module
- Completeness critical fields exist for each element
- Hygiene includes authentication + witness sourcing + privilege risk
- Discovery triggers exist for missing proof types
- Escalation gates include M&C prerequisite before MTC
- No claims of frequency without provided stats
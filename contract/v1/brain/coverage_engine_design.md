# Coverage Engine Design — Contract v1

**Status:** SSOT (authoritative)  
**Purpose:** Define deterministic coverage scoring: burden map elements vs case signals.

---

## 1. Definition of Coverage

Coverage answers:
> For each required element in the burden map, do we have sufficient signals, with citations, to support it?

Coverage does not answer:
- who wins
- legal conclusions
- drafting strategy

---

## 2. Inputs

1. `burden_map` (authority-derived)
2. `case_signal_profile` (normalized case layer)
3. `pattern_modules` (deterministic signal requirements per element)

---

## 3. Element-Level Outputs

For each element:
- `coverage_level`: covered_strong | covered_weak | not_covered | unknown
- `score`: numeric (v1 scale may be simple)
- `signal_citations[]`: which signals support the element
- `missing_information_prompts[]`: what to ask next
- `requested_evidence_types[]`: evidence to request (from proof types + module)
- `discovery_themes[]`: tagged themes (no drafting)
- `notes`: transparent explanation

---

## 4. Deterministic Scoring Logic (v1)

### 4.1 Required vs Supporting Signals
- Required signals must be present to exceed weak coverage.
- Supporting signals improve strength and reduce uncertainty.

### 4.2 Specificity Thresholds
Strong coverage requires:
- actor + action + time window (and location where relevant)
- non-conclusory detail (not just “they breached”)

Weak coverage applies when:
- allegation exists but lacks specifics
- single-source unverified statements exist without corroboration

Not covered when:
- no matching signals exist

Unknown reserved for:
- incomplete parsing state, or schema mismatch

---

## 5. Governance

- Pattern modules are SSOT after attorney promotion.
- LLMs may draft module proposals, but scoring uses promoted deterministic rules only.

---

## 6. Acceptance Criteria

Coverage engine is correct when:
- it is reproducible for identical inputs
- it provides element-by-element citations
- attorneys can override by adjusting module rules (not by hidden model weights)
- it produces gap-driven interview prompts and evidence asks
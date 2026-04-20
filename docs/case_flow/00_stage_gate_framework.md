# CASECORE — STAGE GATE FRAMEWORK
## Governing UI Gates and Subordinate Stage Specifications

---

## PURPOSE

This document defines the controlling stage-gate framework for CaseCore.

The purpose of this document is to make clear that:

- CaseCore has one governing stage-gate structure
- the UI is designed to those stage gates
- all detailed stage `.md` documents are subordinate to those gates
- no separate top-level workflow layer should be invented outside the stage gates

This document exists to prevent drift in design, implementation, and platform language.

---

# CORE RULE

There is **one stage-gate framework** for CaseCore.

The controlling structure is the set of stage gates already defined for the platform UI.

Everything else is subordinate to that framework.

---

# GOVERNING STAGE GATES

The CaseCore UI and top-level workflow are governed by these stage gates:

1. **INTAKE**
2. **CASE BUILD**
3. **DISCOVERY**
4. **TRIAL**
5. **RESOLUTION**
6. **CLOSURE**

These are the top-level gates of the platform.

They are not optional labels, temporary placeholders, or alternate naming conventions.

They are the governing structure that the UI and workflow must follow.

---

# WHAT THE INTERNAL STAGE SPECS ARE

The `.md` files being created for stages are **not new gates**.

They are detailed internal stage specifications that belong under the governing stage gates.

Examples:

- `Fact Normalization` is not a top-level gate
- `Authority Stack Construction` is not a top-level gate
- `COA Determination` is not a top-level gate

These are all governed work stages that live under a stage gate, most often under **CASE BUILD**.

---

# PLATFORM STRUCTURE

## Layer 1 — Stage Gates

The stage gates are the controlling workflow structure for the UI and the platform.

They answer:

- where the case is
- what gate the user is in
- what broad type of work is occurring

## Layer 2 — Internal Stage Specifications

The internal stage specifications define the governed work that occurs inside a gate.

They answer:

- what happens inside the gate
- what inputs are required
- what outputs are produced
- what canonical artifacts are created
- when the gate can truly be considered complete

This is the correct CaseCore structure.

---

# STAGE GATE DEFINITIONS

## 1. INTAKE

INTAKE contains the work required to establish the case and receive the first core materials.

Typical work inside INTAKE includes:

- client interview
- initial evidence upload
- case initialization
- venue/jurisdiction capture
- initial case metadata

INTAKE establishes the case as a governed matter in the platform.

---

## 2. CASE BUILD

CASE BUILD contains the legal and factual construction work that transforms raw matter inputs into a governed case structure.

Typical work inside CASE BUILD includes:

- Fact Normalization
- Authority Stack Construction
- COA Determination
- Evidence-to-Element Mapping
- Burden Analysis
- early strategy formation

CASE BUILD is where the platform determines what the case legally is and what must be proven.

---

## 3. DISCOVERY

DISCOVERY contains the work required to close proof gaps, obtain evidence, and drive fact development against the governing authority structure.

Typical work inside DISCOVERY includes:

- discovery planning
- deposition planning
- evidence expansion
- burden gap closure
- compliance escalation using procedural authority

DISCOVERY exists to gather and force the proof required by the case.

---

## 4. TRIAL

TRIAL contains the work required to prepare and present the case through the authority and burden framework already established.

Typical work inside TRIAL includes:

- trial readiness
- witness preparation
- exhibit preparation
- motion and trial framing
- impeachment preparation
- authority-grounded proof presentation

TRIAL is where the case is presented through the governing stack already established in earlier gates.

---

## 5. RESOLUTION

RESOLUTION contains the work required to conclude the matter through settlement, verdict handling, remedy execution, or enforcement posture.

Typical work inside RESOLUTION includes:

- settlement posture
- verdict handling
- remedy execution
- collection or compliance follow-through
- outcome analysis under the governing authority structure

RESOLUTION handles how the case is concluded in practical and legal terms.

---

## 6. CLOSURE

CLOSURE contains the final governed wrap-up of the matter.

Typical work inside CLOSURE includes:

- final archive
- sealed or immutable record posture
- final closure of the matter
- lessons captured if governed and desired
- preserved authority-to-fact-to-outcome traceability

CLOSURE marks the matter as complete in the platform.

---

# RULE FOR ALL STAGE SPEC DOCUMENTS

Every internal stage specification document must explicitly state which stage gate it belongs to.

This should appear near the top of the file.

Required pattern:

## Stage Gate Alignment

**Primary Stage Gate:** [INTAKE / CASE BUILD / DISCOVERY / TRIAL / RESOLUTION / CLOSURE]

If the stage is reused later, it may also include:

## Reused In Later Stage Gates

- [Gate Name]
- [Gate Name]

This is sufficient.
A separate top-level mapping artifact is not required.

---

# REQUIRED LANGUAGE DISCIPLINE

The platform should not say:

> create a separate mapping spec

The platform should say:

> for each stage spec, explicitly state which stage gate it belongs to

This keeps the structure clean and prevents creation of parallel workflow models.

---

# CURRENT EXAMPLES

The following stage specs belong under **CASE BUILD**:

- Fact Normalization
- Authority Stack Construction
- COA Determination
- Evidence-to-Element Mapping
- Burden Analysis
- early strategy formation

These are not top-level gates.
They are governed work stages inside the CASE BUILD gate.

---

# IMPLEMENTATION RULE

The UI must be designed to the governing stage gates.

The internal stage specs must support the gates, not replace them.

This means:

- dashboard progression should reflect the stage gates
- case progression should reflect the stage gates
- drill-down logic may reveal internal stages
- but the top-level platform structure remains the stage-gate framework

---

# CANONICAL PRINCIPLE

CaseCore has one governing stage-gate framework.

All internal stage specifications are subordinate to that framework.

No parallel top-level workflow taxonomy should be introduced.

---

# ONE-SENTENCE SUMMARY

**CaseCore’s UI is governed by the stage gates, and all stage `.md` files are detailed internal specifications that live under those gates rather than replacing them.**

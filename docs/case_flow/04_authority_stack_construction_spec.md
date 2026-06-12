# CASECORE — STAGE 04 AUTHORITY STACK CONSTRUCTION SPEC
## Governed Legal Authority Selection, Resolution, and Binding Model

---

## PURPOSE

This document defines how CaseCore constructs the **Authority Stack** for a case.

Authority Stack Construction is the deliberate, ordered assembly of **binding legal authorities** that govern:

- how facts are evaluated
- how burdens are satisfied
- how remedies are determined
- how a decision may lawfully be reached in a specific case

This stage answers the governing question **before** facts are argued, discovery is planned, or strategy is formed:

> **By which legal rules will the court decide whether these facts matter and what they mean?**

Without an explicit Authority Stack:

- facts float without legal relevance
- discovery becomes unfocused
- arguments drift into impermissible conclusions
- burden analysis becomes unstable
- verdict posture becomes vulnerable on appeal

Authority Stack Construction is therefore a required governed stage in the deterministic spine of the platform.

---

# STAGE GATE ALIGNMENT

## Primary UI Stage Gate
**CASE BUILD**

## Secondary Reuse in Later UI Stage Gates
- **DISCOVERY**
- **TRIAL**
- **RESOLUTION**

## Relationship to UI Flow

CaseCore’s UI is designed around these stage gates:

1. **INTAKE**
2. **CASE BUILD**
3. **DISCOVERY**
4. **TRIAL**
5. **RESOLUTION**
6. **CLOSURE**

Authority Stack Construction belongs primarily to **CASE BUILD** because this is the stage where the platform must explicitly determine what law governs:

- materiality of facts
- element structure
- burden of proof
- burden of producing evidence
- admissibility boundaries
- remedy availability
- discovery scope
- trial framing

This stage is then reused downstream in **DISCOVERY**, **TRIAL**, and **RESOLUTION** as the legal framework for all later work.

---

# WHAT “AUTHORITY” MEANS HERE

In this platform, **authority** does not mean commentary, summaries, or opinion.

It means **binding legal instruction** that controls decision-making in the case.

Authoritative sources include:

- **Jury Instructions**  
  Example: CACI in California  
  These define the elements, burdens, and the framework through which jurors evaluate facts.

- **Statutes and Codes**  
  These define rights, duties, causes of action, defenses, and remedies.

- **Rules of Evidence**  
  These determine what evidence may be considered at all, and under what conditions.

- **Procedural Rules**  
  These govern how facts enter the record, what discovery is permitted, and how proof may be presented or excluded.

- **Case-Specific Orders, Rulings, and Stipulations**  
  These may further constrain what is admissible, established, excluded, or precluded.

- **Case-Specific Subject Matter Authorities**  
  Such as cannabis statutes and regulations in a cannabis matter, or contract clauses in a contract-driven dispute.

Authority Stack Construction must be grounded in these sources and in no others.

---

# FORMAL DEFINITION

**Authority Stack Construction** is the process of identifying, ordering, resolving, and binding the controlling legal authorities that govern:

1. which facts are legally material,
2. how those facts must be proven,
3. what evidence may be considered,
4. what procedural pathways constrain the record, and
5. what remedies are available if proof succeeds or fails.

The Authority Stack is:

- **case-specific**
- **jurisdiction-specific**
- **stage-aware**
- **hierarchy-aware**
- **canonical when properly validated**

---

# THE CANONICAL AUTHORITY STACK

A properly constructed Authority Stack follows a strict hierarchy.

---

## 1. Jury Instructions — Decision Layer

Jury instructions define:

- the elements of claims and defenses
- the burden of proof
- the standard of persuasion
- the lens through which facts are evaluated for verdict purposes

For California civil matters, CACI is a primary decision-layer authority.

This is the final legal framework through which the factfinder decides whether proof is sufficient.

---

## 2. Substantive Law — Rights, Duties, Remedies

Substantive law defines:

- what conduct is unlawful
- what constitutes breach, fraud, negligence, misrepresentation, etc.
- what remedies are legally available
- what duties and obligations exist

Examples may include:

- California Civil Code
- California Business & Professions Code
- industry-specific statutes
- controlling common-law doctrines
- contract clauses where private law governs the parties’ relationship

---

## 3. Evidence Law — Admissibility and Fact Filters

Evidence law governs:

- relevance
- authenticity
- hearsay and exceptions
- reliability
- exclusion
- presumptions and inferences
- burden of producing evidence
- burden-shifting logic where applicable

If evidence fails here, it does not become an operative fact for legal decision-making.

### Example
If the issue is burden of producing evidence in a California civil case, the stack may resolve to:

California Evidence Code  
→ Division 5  
→ Chapter 2  
→ Section 550

That is a proper authority resolution for that issue.

---

## 4. Procedural Law — Workflow and Record Constraints

Procedural law governs:

- how facts enter the record
- scope of discovery
- motions to compel
- exclusion and sanctions
- timing and process constraints
- preservation and use of materials in litigation

These authorities determine not whether a fact is true, but whether and how it can be introduced, challenged, or considered.

---

## 5. Case-Specific Orders, Rulings, and Stipulations

This layer includes:

- rulings on admissibility
- deemed established facts
- excluded issues
- stipulations
- case management orders
- protective orders
- discovery rulings

These authorities can materially alter how the case proceeds and what may be used.

---

# AUTHORITY LAYERS THE PLATFORM MUST EVALUATE

Authority Stack Construction must evaluate law through the following case-selection layers.

---

## 1. General Baseline Law

These authorities apply broadly and form the baseline framework for the platform.

Examples:
- U.S. law where applicable
- California law
- California Evidence Code
- CACI
- California procedural and substantive statutes

These usually anchor nearly every California civil matter in the system.

---

## 2. Jurisdiction-Specific Law

These authorities apply based on:

- county
- city
- venue
- forum
- local regulatory environment

Examples:
- county ordinances
- municipal code
- local licensing restrictions
- local court rules where relevant

These authorities may materially change what facts matter and what conduct is compliant or unlawful.

---

## 3. Case-Specific Law

These authorities apply because of the specific subject matter, industry, dispute type, or operative facts of the case.

Examples:
- cannabis statutes and regulations
- employment law
- insurance law
- landlord-tenant law
- permit or licensing requirements
- case-specific contracts
- controlling case law for the issue

### Example
For a cannabis case such as Mills vs. Polley, the Authority Stack may include:

- California Evidence Code
- CACI
- California cannabis statutes
- cannabis regulations
- county/city cannabis restrictions
- relevant contract clauses
- case law interpreting the dispute context

---

# WHAT “APPLY” MEANS IN THIS PLATFORM

To **apply** authority means two things:

## A. Select the Correct Authority Layer and Source

The system must determine whether the issue requires:

- federal law
- state law
- county law
- city law
- case-specific regulatory law
- contract authority
- case law
- jury instructions
- evidence law
- procedural law

## B. Resolve the Correct Internal Authority Unit

The system must then resolve the source to the correct internal legal unit, such as:

- title
- division
- chapter
- article
- section
- instruction number
- case citation and holding
- contract clause

The system must never stop at broad labels like:

- “Evidence Code”
- “Cannabis law”
- “Case law”

It must resolve to the actual controlling unit.

---

# BRAIN, AGENT, AND PROGRAM RESPONSIBILITIES

Authority Stack Construction operates through the Brain, Agent, and Program model.

---

## THE BRAIN

### Definition
The Brain is the platform’s legal authority intelligence layer.

### Responsibilities
The Brain must:

- maintain the inventory of authoritative legal sources
- organize sources by jurisdiction and hierarchy
- provide structured retrieval by issue and case context
- resolve authority to the proper legal level
- preserve traceability to legal source material
- support Authority Stack assembly for the case

### The Brain must know or readily access:
- jury instructions
- statutes and codes
- evidence rules
- procedural rules
- local ordinances where applicable
- regulations
- case law
- contract authorities when relevant to the matter

### The Brain must not:
- learn law from strategy content
- treat notes or commentary as authority
- infer authority from non-authoritative exploratory materials

---

## THE AGENT

### Definition
The Agent is the contextual legal selector and applier.

### Responsibilities
The Agent must:

- inspect case context
- identify governing legal issues
- determine which layers of authority apply
- query the Brain for the relevant authority set
- resolve from source family to exact legal unit
- bind selected authority to downstream tasks

### The Agent must determine:
- what baseline law applies
- what jurisdiction-specific law applies
- what case-specific law applies
- which sections, instructions, holdings, rulings, or clauses govern the issue

### Example
If the issue is burden of producing evidence in a California civil matter, the Agent should resolve:

California Evidence Code  
→ Division 5  
→ Chapter 2  
→ Section 550

If the issue is cannabis compliance, the Agent should also retrieve and bind the relevant cannabis statutes and regulations.

---

## PROGRAMS

### Definition
Programs are deterministic execution pipelines.

### Programs in this stage may include:
- Authority Inventory Retrieval Program
- Jurisdiction Resolution Program
- Subject Matter Authority Detection Program
- Authority Resolution Program
- Authority Binding Program
- Authority Validation Program
- Authority Stack Assembly Program

Programs execute structured retrieval, validation, and assembly logic.  
They do not independently interpret law outside governed patterns.

---

# INPUTS

Authority Stack Construction begins when sufficient legal and case context is available.

## Upstream Inputs
- case metadata
- venue and jurisdiction
- intake narrative
- fact normalization outputs
- identified legal issue signals
- subject matter indicators
- contract documents if present
- known regulatory context
- prior authority packs available to the platform

## Required Context Signals
At minimum, the system should know:

- governing state
- county/city if relevant
- matter type
- dispute domain
- evidentiary issues
- burden issues
- procedural posture where known
- contractual or regulatory context where present

---

# OUTPUTS

Authority Stack Construction must produce a governed, canonical output set.

## Required Outputs

### 1. Authority Stack Record
A structured case-level record of all applicable authority families and units.

### 2. Authority Hierarchy Paths
The precise hierarchy path for each selected authority.

### 3. Authority Bindings
Links between case issues and their governing legal authorities.

### 4. Applicability Rationale
A concise, traceable explanation of why each authority applies.

### 5. Downstream Readiness Flags
Signals that the stack is ready for:
- Fact Normalization
- COA Determination
- Evidence-to-Element Mapping
- Burden Analysis
- Discovery Planning
- Trial Readiness
- Dashboard rendering
- War Room consumption

---

# CANONICAL STATUS

Authority Stack output is **canonical** when:

- derived from authoritative legal sources
- validated through governed selection rules
- resolved to the proper hierarchy level
- bound to the case with traceable rationale

This output becomes part of the canonical case stream because it governs how later stages evaluate:

- facts
- elements
- burdens
- admissibility
- discovery scope
- remedies

---

# DATA GOVERNANCE

## Canonical Data in this Stage
- authority families
- hierarchy paths
- section references
- instruction references
- case citations and holdings
- procedural rule references
- order/ruling references
- contract clause references
- authority applicability rationales
- authority-to-issue bindings

## Non-Canonical Data in this Stage
- attorney brainstorming about possible authorities
- exploratory theories
- tentative issue framing not yet validated
- strategy notes
- unpromoted legal argument drafts

## Rule
Non-canonical content may be visible to attorneys, but it must not silently become part of the Authority Stack unless explicitly promoted through governed review.

---

# STAGE WORKFLOW

Authority Stack Construction should follow this sequence.

## Step 1 — Read Case Context
Read:
- jurisdiction
- venue
- issue signals
- domain indicators
- procedural signals
- contract or regulatory indicators

## Step 2 — Retrieve Baseline Authorities
Pull the legal authorities that broadly govern the matter.

## Step 3 — Retrieve Jurisdiction Authorities
Pull county, city, venue, forum, or local regulatory authorities where relevant.

## Step 4 — Retrieve Case-Specific Authorities
Pull subject-matter authorities such as cannabis law, contract provisions, regulations, and controlling case law.

## Step 5 — Resolve to Precise Internal Units
Move from broad authority family to exact section, instruction, holding, order, or clause.

## Step 6 — Validate Authority Set
Confirm:
- source is authoritative
- jurisdiction is correct
- hierarchy path is complete
- applicability is established
- non-authoritative contamination is absent

## Step 7 — Assemble Authority Stack
Produce the canonical Authority Stack for the case.

## Step 8 — Bind to Downstream Use
Mark which authorities govern:
- facts
- COAs
- elements
- burdens
- discovery
- trial readiness
- remedies
- closure posture if relevant

---

# HOW THIS STAGE OPERATES ACROSS THE CASE WORKFLOW

---

## INTAKE

At Intake, the platform must:

- identify jurisdiction, venue, and governing law
- identify the likely legal domain
- establish the initial authoritative sources that may govern the case

At this point, the platform is not yet evaluating facts on the merits.  
It is setting the governing rules.

---

## CASE BUILD

In Case Build, the platform must:

- map Causes of Action directly to jury instruction elements
- bind those elements to statutes, evidence requirements, and procedural constraints
- reject facts that cannot become legally relevant under the stack
- identify the legal framework for burden and admissibility analysis

This stage prevents over-collection and weak claim drift.

---

## DISCOVERY

In Discovery, the platform must:

- design discovery against authority-defined elements
- determine what documents, testimony, and admissions matter
- escalate non-compliance using procedural authority
- target proof gaps that matter under the stack

Discovery serves burden satisfaction, not curiosity.

---

## TRIAL

In Trial, the platform must:

- present facts through the authority stack already constructed
- align exhibits and testimony to instruction language
- prepare evidentiary and procedural arguments under the governing stack
- prevent unsupported argument drift

No trial theory should survive if it is not anchored to the stack.

---

## VERDICT, RESOLUTION, AND CLOSURE

At Resolution and Closure, the platform must:

- evaluate outcome posture against the same governing authorities
- preserve authority-to-fact mappings
- retain appeal posture and traceability
- archive the authority framework used to decide and resolve the case

---

# COMPLETION CRITERIA

This stage is complete only when:

- applicable authority families are identified
- jurisdiction-specific authority is resolved
- case-specific authority is resolved
- controlling sections/instructions/holdings/clauses are identified where needed
- applicability rationale is recorded
- downstream stages can consume the stack
- canonical integrity is preserved

---

# FAILURE CONDITIONS

This stage is incomplete or invalid if:

- law remains only at broad source level
- the wrong jurisdiction is used
- local jurisdiction authority is ignored where relevant
- case-specific law is omitted
- exact controlling legal units are not resolved
- authority applicability is unexplained
- non-authoritative material contaminates the stack

---

# DASHBOARD INTEGRATION

The dashboard should ultimately display signals such as:

- Authority Stack constructed: Yes / No
- Jury instruction layer complete
- substantive law layer complete
- evidence law layer complete
- procedural law layer complete
- jurisdiction authority complete
- case-specific authority complete
- number of bound authorities
- unresolved authority gaps

This stage should support drill-down into:
- authority family
- hierarchy path
- why it applies
- which stage depends on it

---

# DOWNSTREAM DEPENDENCIES

Authority Stack Construction feeds:

## Fact Normalization
Facts are normalized under the governing law.

## COA Determination
COAs are selected against the controlling authority framework.

## Evidence-to-Element Mapping
Facts are mapped under the correct legal regime.

## Burden Analysis
Burden is evaluated against the correct law.

## Discovery
Discovery targets are selected against legally material proof gaps.

## Trial
Trial readiness depends on authority-grounded proof theory.

## Resolution
Remedies and closure posture depend on the governing legal structure.

---

# SAMPLE CASE EXAMPLE

## Example Matter
Mills vs. Polley

## Context
- California case
- local jurisdiction may matter
- cannabis subject matter
- burden and evidence issues present

## Possible Authority Stack

### Jury Instructions
- relevant CACI instructions

### Substantive Law
- California cannabis statutes
- related code provisions
- relevant contract clauses

### Evidence Law
- California Evidence Code
- burden and admissibility sections as implicated

### Procedural Law
- California procedural rules
- case-specific motions and discovery rules as relevant

### Jurisdiction Layer
- county/city restrictions if cannabis operations or local restrictions matter

### Example Specific Resolution
Issue:
Burden of producing evidence

Authority:
California Evidence Code  
→ Division 5  
→ Chapter 2  
→ Section 550

---

# CANONICAL RULE

> **No fact, discovery request, analytic result, or strategic signal may exist outside the Authority Stack that governs its legal meaning.**

If something cannot be justified by:

- a jury instruction
- a statute or code section
- an evidence rule
- a procedural rule
- or a case-specific controlling authority

…it cannot lawfully influence the case.

---

# ONE-SENTENCE SUMMARY

**Authority Stack Construction is the act of deciding—first and explicitly—what law controls the interpretation of facts, before any fact is allowed to matter.**

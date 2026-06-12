\# CASECORE — STAGE 05 COA DETERMINATION SPEC

\## Deterministic, Authority-Bound, Traceable Cause of Action Construction



\---



\## STAGE GATE ALIGNMENT



\*\*Primary Stage Gate:\*\* CASE BUILD



\## Reused In Later Stage Gates

\- DISCOVERY

\- TRIAL

\- RESOLUTION



\---



\## PURPOSE



This document defines how CaseCore constructs and governs \*\*Causes of Action (COAs)\*\* inside the platform.



A COA is not a narrative, a memo, or a draft argument.



In CaseCore, a COA is a \*\*structured, deterministic, authority-bound legal claim object\*\* built from:



\- normalized facts

\- the governing Authority Stack

\- authoritative legal sources

\- traceable mappings to raw intake evidence



This stage exists to ensure that legal claims are:



\- grounded in authoritative law

\- tied to provable elements

\- traceable to evidence

\- bounded by burden logic

\- connected to legally available remedies



\---



\# DEFINITION (CANONICAL)



A \*\*Cause of Action (COA)\*\* is a formally defined legal claim structure that specifies:



1\. the \*\*legal theory\*\* asserted  

2\. the \*\*authoritative elements\*\* that must be proven  

3\. the \*\*burden and standard of proof\*\* for each element  

4\. the \*\*remedies\*\* made available upon satisfaction  

5\. the \*\*factual predicates\*\* required to support each element  



In the platform, a COA is \*\*not prose\*\*.



It is a \*\*structured object\*\* derived from evidence and validated against authority.



\---



\# WHY THIS STAGE EXISTS



This stage is where the platform determines what legal claims are actually available in the case.



Without a disciplined COA stage:



\- facts remain unconnected to legal claims  

\- discovery becomes broad and unfocused  

\- burden analysis becomes unstable  

\- remedies are guessed rather than derived  

\- complaints drift into unsupported allegations  

\- trial preparation loses element-level rigor  



COA Determination is therefore a required governed stage inside \*\*CASE BUILD\*\*.



\---



\# POSITION IN CASE FLOW



The governed progression is:



Intake Evidence  

→ Fact Normalization  

→ Authority Stack Construction  

→ \*\*COA Determination\*\*  

→ Burden Construction  

→ Remedy Construction  

→ Mappings Stored \& Hashed  

→ Complaint Drafting  

→ Pursuit Decision (Value + Risk)



No step is optional.  

No step may be skipped.



\---



\# PRE-CONDITIONS (FAIL CLOSED)



Before COA construction begins, the system must have:



1\. \*\*Jurisdiction identified\*\*  

2\. \*\*Authority Stack constructed\*\*, including:  

&#x20;  - Jury instructions (e.g., CACI)  

&#x20;  - Governing statutes  

&#x20;  - Evidence rules  

&#x20;  - Procedural rules where relevant  

3\. \*\*Normalized Facts available\*\*  



If any are missing:



→ \*\*FAIL CLOSED\*\*



COA Determination must not proceed.



\---



\# INPUTS



\## Raw Inputs (Ingest Layer)



These are upstream inputs but are never treated as facts by this stage:



\- client interview transcript  

\- uploaded files  

\- audio  

\- video  

\- metadata  

\- timestamps  

\- provenance records  



These inputs must already have passed through Fact Normalization and Authority Stack Construction.



\---



\## Required Inputs to This Stage



COA Determination operates on:



\- normalized facts  

\- authority stack  

\- case metadata  

\- jurisdiction  

\- case domain  

\- legal issue signals  

\- fact-to-authority bindings already available upstream  



\---



\# COA IDENTIFICATION (AUTHORITY-DRIVEN)



\## Process



1\. The system examines \*\*normalized facts\*\*  

2\. Facts are evaluated solely through the \*\*Authority Stack\*\*  

3\. The system identifies \*\*candidate COAs\*\* whose elements could potentially be satisfied by the available facts  



This is \*\*matching\*\*, not legal conclusion-drawing.



\---



\## COA Identification Rules



A COA may be identified \*\*only\*\* if:



\- every element is defined by an authoritative source  

\- at least one normalized fact potentially supports each element  

\- the COA is valid in the governing jurisdiction  

\- the authority references are complete and traceable  



Weak or partial support is allowed at this stage.



Missing authority reference:



→ \*\*INVALID COA\*\*



\---



\# AUTHORITY SOURCES



A valid COA must be grounded in authoritative law.



Authoritative sources may include:



\- CACI jury instructions  

\- California statutes and codes  

\- California Evidence Code  

\- California Code of Civil Procedure  

\- controlling common-law authority  

\- case-specific subject matter authorities  

\- contract clauses  

\- procedural rulings or court orders  



Authority is mandatory.  

A COA without authority is void.



\---



\# COA STRUCTURE (DATA MODEL)



Each COA stored in the system must include:



```yaml

COA:

&#x20; id: COA-UUID

&#x20; name: Fraud (Intentional Misrepresentation)

&#x20; jurisdiction: CA

&#x20; authority\_sources:

&#x20;   - CACI 1900

&#x20;   - Civil Code §1709

&#x20; elements:

&#x20;   - element\_id

&#x20;   - element\_text

&#x20;   - burden\_of\_proof

&#x20;   - standard

&#x20; status: CANDIDATE | SUPPORTED | WEAK | REJECTED


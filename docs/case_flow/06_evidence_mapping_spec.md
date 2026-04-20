\# CASECORE — STAGE 06 EVIDENCE-TO-ELEMENT MAPPING SPEC

\## Deterministic · Authority-Bound · Traceable · Measurable



\---



\## STAGE GATE ALIGNMENT



\*\*Primary Stage Gate:\*\* CASE BUILD



\## Reused In Later Stage Gates

\- DISCOVERY

\- TRIAL



\---



\## PURPOSE



Evidence-to-Element Mapping connects:



\- raw intake evidence  

\- normalized facts  

\- COA elements  



into a \*\*deterministic, measurable proof system\*\*.



This stage determines:



\- what is provable  

\- what is partially provable  

\- what is missing  



\---



\# SYSTEM MODEL (SPINE / BRAIN / AGENT / PROGRAM / DATA)



\## SPINE (Governance)



The Spine enforces:



\- fail-closed execution  

\- append-only mapping records  

\- hash-based traceability  

\- canonical data discipline  

\- prohibition of evidence → element shortcuts  



\---



\## BRAIN (Legal Structure)



The Brain provides:



\- element definitions  

\- authority bindings  

\- admissibility frameworks  



The Brain defines:



> What must be proven.



\---



\## AGENT (Execution Layer)



The Agent performs:



\- fact → element mapping  

\- support classification  

\- gap detection  

\- coverage scoring  



The Agent determines:



> What is provable now.



\---



\## PROGRAMS (Deterministic Engine)



Programs enforce:



\- mapping structure  

\- scoring calculations  

\- validation rules  

\- audit integrity  



Programs ensure deterministic execution.



\---



\## DATA (Canonical Discipline)



\### Canonical Data

\- facts  

\- mappings  

\- coverage scores  

\- traceability  



\### Non-Canonical Data

\- strategy  

\- notes  

\- hypotheses  



Non-canonical data cannot modify mapping state.



\---



\# PRE-CONDITIONS (FAIL CLOSED)



Must exist:



\- Authority Stack  

\- Normalized Facts  

\- COA objects with elements  



If missing → FAIL CLOSED



\---



\# CORE MODEL



Each COA element must map to:



\- supporting facts  

\- supporting evidence  

\- support strength  

\- coverage score  



\---



\# CANONICAL MAPPING OBJECT



```yaml

EvidenceElementMapping:

&#x20; mapping\_id: UUID

&#x20; coa\_id: UUID

&#x20; element\_id: UUID



&#x20; supporting\_facts:

&#x20;   - fact\_id



&#x20; evidence\_sources:

&#x20;   - file\_hash

&#x20;   - locator:

&#x20;       type: page | timestamp | paragraph | clip\_range

&#x20;       value: string



&#x20; authority\_reference:

&#x20;   citation: string



&#x20; support\_strength:

&#x20;   value: DIRECT | INFERENTIAL | WEAK | NONE



&#x20; coverage\_score: 0.0 - 1.0



&#x20; admissibility\_flags:

&#x20;   - hearsay

&#x20;   - relevance

&#x20;   - foundation\_required



&#x20; created\_by: AGENT | HUMAN

&#x20; created\_at: timestamp


\# CASECORE — STAGE 09 DEPOSITION EXECUTION ENGINE SPEC

\## Real-Time · Structured · Traceable · Admissible



\---



\## STAGE GATE ALIGNMENT



\*\*Primary Stage Gate:\*\* DISCOVERY



\## Reused In Later Stage Gates

\- TRIAL

\- RESOLUTION



\---



\## PURPOSE



The Deposition Execution Engine transforms:



\- prepared deposition strategy  

\- structured question sets  



into:



\- real-time testimony capture  

\- structured evidence  

\- contradiction detection  

\- admissible record generation  



This stage answers:



> What did the witness actually commit to, and how does it impact the case?



\---



\# SYSTEM MODEL (SPINE / BRAIN / AGENT / PROGRAM / DATA)



\## SPINE (Governance)



The Spine enforces:



\- append-only testimony records  

\- immutable transcript structure  

\- traceability from question → answer → element  

\- no post-hoc mutation of testimony  



\---



\## BRAIN (Legal Structure)



The Brain provides:



\- admissibility guidance  

\- impeachment rules  

\- foundation requirements  

\- evidentiary classification  



\---



\## AGENT (Execution)



The Agent:



\- presents questions  

\- captures responses  

\- classifies answers  

\- identifies contradictions in real time  

\- recommends follow-up questions  



\---



\## PROGRAMS (Deterministic Engine)



Programs:



\- transcribe audio/video  

\- segment Q/A  

\- structure transcript  

\- detect contradictions  

\- map testimony to elements  



\---



\## DATA



\### Canonical

\- transcript  

\- Q/A pairs  

\- structured testimony  

\- mapped statements  

\- contradiction records  



\### Non-Canonical

\- agent suggestions  

\- strategy prompts  



\---



\# PRE-CONDITIONS (FAIL CLOSED)



Must exist:



\- deposition plan  

\- question sets  

\- mapping to elements  



Else → FAIL CLOSED



\---



\# CORE MODEL



Each deposition interaction produces:



\- question  

\- answer  

\- classification  

\- mapping  

\- traceability  



\---



\# TRANSCRIPT MODEL



```yaml

TranscriptSegment:

&#x20; segment\_id: UUID

&#x20; type: QUESTION | ANSWER

&#x20; text: string

&#x20; timestamp\_start

&#x20; timestamp\_end

&#x20; speaker


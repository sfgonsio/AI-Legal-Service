\# CASECORE — STAGE 07 BURDEN \& PERSUASION ANALYSIS SPEC

\## Deterministic · Authority-Bound · Outcome-Oriented



\---



\## STAGE GATE ALIGNMENT



\*\*Primary Stage Gate:\*\* CASE BUILD



\## Reused In Later Stage Gates

\- DISCOVERY

\- TRIAL

\- RESOLUTION



\---



\## PURPOSE



Burden \& Persuasion Analysis determines whether the mapped evidence satisfies:



\- the \*\*burden of production\*\*

\- the \*\*burden of proof\*\*

\- the \*\*standard of persuasion\*\*



for each COA element.



This stage answers:



> Can this case win under the law?



\---



\# SYSTEM MODEL (SPINE / BRAIN / AGENT / PROGRAM / DATA)



\## SPINE (Governance)



The Spine enforces:



\- fail-closed progression  

\- explicit burden evaluation per element  

\- no silent assumptions of proof  

\- append-only evaluation records  



\---



\## BRAIN (Legal Authority)



The Brain defines:



\- burden allocation (who must prove)  

\- burden type (production vs persuasion)  

\- standard (preponderance, clear \& convincing, etc.)  



The Brain answers:



> What must be proven and to what level?



\---



\## AGENT (Evaluation)



The Agent evaluates:



\- mapped evidence vs burden  

\- sufficiency of proof  

\- weaknesses in proof  

\- probability of satisfaction  



\---



\## PROGRAMS (Deterministic Engine)



Programs:



\- compare coverage vs burden requirements  

\- calculate burden satisfaction  

\- enforce evaluation rules  



\---



\## DATA (Canonical Discipline)



\### Canonical

\- burden objects  

\- evaluation results  

\- satisfaction scores  



\### Non-Canonical

\- strategy  

\- attorney opinion  



\---



\# PRE-CONDITIONS (FAIL CLOSED)



Must exist:



\- COA elements  

\- evidence-to-element mappings  

\- coverage scores  



Missing any → FAIL CLOSED



\---



\# CORE MODEL



Each element must be evaluated against:



\- burden of production  

\- burden of proof  

\- persuasion standard  



\---



\# BURDEN OBJECT



```yaml

Burden:

&#x20; element\_id: UUID

&#x20; burden\_type: PRODUCTION | PROOF

&#x20; standard: PREPONDERANCE | CLEAR\_AND\_CONVINCING | BEYOND\_REASONABLE\_DOUBT

&#x20; responsible\_party: PLAINTIFF | DEFENDANT


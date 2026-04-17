\# PROGRAM CONTRACT TEMPLATE



This template defines the required structure for all deterministic execution programs in the AI Legal Service Platform.



Programs are bounded execution modules responsible for transforming governed inputs into governed outputs.



Programs are not agents.



Programs do not reason conversationally.



Programs perform deterministic or deterministically constrained computation.



---



\# 1 Program Identity



Program Name:



program\_<NAME>



Program Layer:



Programs



Reasoning Stage Transition:



Define the reasoning pipeline stage this program implements.



Examples:



Source Material → Facts  

Facts → Events  

Events → Signals  

Signals → Patterns  

Patterns → Causes of Action  

Causes of Action → Coverage



---



\# 2 Purpose



Explain:



What the program does.



Why the program exists.



Where it fits in the reasoning pipeline.



Programs should be described as \*\*bounded transformations\*\*, not reasoning agents.



---



\# 3 Scope



\### In Scope



List the specific operations this program performs.



\### Out of Scope



Examples:



Attorney decision making  

Freeform reasoning  

User conversation  

Cross-case inference  

Uncontrolled tool access



---



\# 4 Trigger Conditions



Define when the program may execute.



Possible triggers:



Agent invocation  

Workflow step  

Manual UI action  

System pipeline progression  

Replay validation



---



\# 5 Inputs



List all required inputs.



Example:



case\_id  

run\_id  

source fragments  

facts  

entities  

events  

patterns  

configuration parameters



Each input must include:



type  

required/optional  

source of truth



---



\# 6 Outputs



Define outputs produced.



Example:



facts  

events  

signals  

patterns  

cause\_of\_action structures  

coverage outputs



Each output must define:



destination store  

review requirement  

provenance requirements



---



\# 7 Read Boundaries



Define what data the program may read.



Examples:



Evidence Graph objects  

Configuration registries  

Case-scoped data



Programs must never read cross-case data.



---



\# 8 Write Boundaries



Define what the program may write.



Examples:



facts  

events  

signals  

patterns  

claim support structures



Programs must not modify unrelated objects.



---



\# 9 Reasoning Model Alignment



Map program behavior to:



system\_REASONING\_MODEL.md



Define:



upstream stage  

downstream stage



---



\# 10 Workflow State Alignment



Map program behavior to:



system\_STATE\_MODEL.md



Define:



allowed entry state  

success state  

failure state



---



\# 11 Determinism Requirements



Define deterministic expectations.



Examples:



stable transformation rules  

replay equivalence  

controlled randomness  

configuration locking



---



\# 12 Provenance Requirements



Each output must include:



case\_id  

run\_id  

program\_name  

timestamp  

supporting objects



---



\# 13 Audit Events



Program must emit audit events for:



start  

completion  

failure  

rerun



---



\# 14 Failure Handling



Define behavior for:



invalid inputs  

missing dependencies  

data inconsistencies  

write failures



Define:



halt vs retry  

state transition  

audit event



---



\# 15 Replay Behavior



Programs must support replay validation.



Define:



rerun rules  

supersession rules  

duplicate detection



---



\# 16 Tool Access



List tools the program may use.



Examples:



entity resolver  

pattern detector  

normalization utilities



Programs must not call unregistered tools.



---



\# 17 Security Constraints



Programs must enforce:



case isolation  

data minimization  

no external uncontrolled calls



---



\# 18 Human Review Boundaries



Define what outputs require human review.



Examples:



claim formation  

coverage scoring



---



\# 19 Acceptance Criteria



Program contract is complete when:



inputs defined  

outputs defined  

read/write boundaries defined  

state transitions defined  

determinism rules defined  

audit rules defined



---



\# 20 Authoring Notes



All programs must follow this template.



Expected programs include:



program\_FACT\_NORMALIZATION  

program\_COMPOSITE\_ENGINE  

program\_PATTERN\_ENGINE  

program\_COA\_ENGINE  

program\_COVERAGE\_ENGINE


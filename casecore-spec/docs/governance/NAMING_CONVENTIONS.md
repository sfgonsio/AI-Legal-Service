\# /casecore-spec/docs/governance/NAMING\_CONVENTIONS.md



\# NAMING CONVENTIONS



\## Purpose



This document defines all naming rules for CASECORE to prevent drift, ambiguity, and future refactoring risk.



These rules are mandatory across:

\- backend services

\- frontend code

\- schemas

\- APIs

\- database objects

\- workflows

\- contracts

\- documentation



\---



\## 1. Internal System Name



\*\*casecore\*\*



This is the ONLY name used for all internal system identifiers.



\---



\## 2. External Product Name



\*\*TBD (Not Yet Defined)\*\*



External branding must NOT be used in any internal technical implementation.



\---



\## 3. Strict Separation Rule



Internal system naming and external branding MUST remain separate.



\### Internal = casecore  

\### External = brand (future)



These must never be mixed.



\---



\## 4. Required Usage (MANDATORY)



The following MUST use `casecore`:



\### Repositories

\- casecore-spec

\- casecore-build-kit (future)



\### Services

\- casecore-workflow-engine

\- casecore-artifact-service

\- casecore-audit-service

\- casecore-llm-gateway



\### APIs

\- /api/casecore/...

\- /casecore/workflows/...



\### Database

\- casecore\_matters

\- casecore\_documents

\- casecore\_facts

\- casecore\_events

\- casecore\_audit\_log



\### Schemas

\- casecore.fact.schema.json

\- casecore.event.schema.json



\### Events

\- casecore.fact.created

\- casecore.event.generated

\- casecore.artifact.promoted



\---



\## 5. Prohibited Usage (ZERO TOLERANCE)



The following are NOT allowed anywhere in the system:



\### ❌ Deprecated Name

\- TrialForge



\### ❌ Product Branding (current or future)

\- Any marketing name



\### ❌ Mixed Naming

\- casecoreTrial

\- trial\_casecore

\- brandedCasecore



\---



\## 6. Identifier Standards



\### Format Rules



| Type | Format |

|------|--------|

| IDs | UPPER\_SNAKE or PREFIX-0001 |

| Files | lowercase-with-dashes |

| Schemas | dot.notation.schema.json |

| APIs | lowercase paths |

| Events | dot.separated.lowercase |



\---



\### Examples



\#### IDs

\- MTR-0001

\- DOC-0001

\- FCT-0001

\- EVT-0001

\- RUN-20260318-001



\#### Files

\- fact-normalization.md

\- coa-engine.yaml



\#### Schemas

\- casecore.fact.schema.json



\#### APIs

\- /api/casecore/facts

\- /api/casecore/events



\#### Events

\- casecore.fact.created

\- casecore.coa.mapped



\---



\## 7. UI Naming Rules



UI may display:

\- External product name (future)

\- Human-friendly labels



BUT:



System identifiers must NEVER be exposed as:

\- branded language

\- legal conclusions

\- misleading terms



\---



\## 8. Migration Rule



All existing references to:

\- TrialForge



MUST be replaced with:

\- casecore



No exceptions.



\---



\## 9. Enforcement



Violations of naming rules must be rejected in:



\- code review

\- schema validation

\- CI checks

\- contract validation



\---



\## 10. Future Branding



When product naming is finalized:



\- It will ONLY be applied to:

&#x20; - UI layer

&#x20; - marketing

&#x20; - domain



\- It will NOT:

&#x20; - change database names

&#x20; - change APIs

&#x20; - change schemas

&#x20; - change internal identifiers



\---



\## Final Rule



> Internal naming must remain stable for the life of the system.  

> Branding may change. Architecture must not.




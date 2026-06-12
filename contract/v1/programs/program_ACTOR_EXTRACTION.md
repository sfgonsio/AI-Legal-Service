# program_ACTOR_EXTRACTION
(Authoritative Program Contract — v1 | Ingest-time Extraction)

---

## 1. Purpose

Populate case actors as early as possible, during save-path ingest, using a deterministic rule-based extractor. No LLM, no NER model, no analytical dependencies.

## 2. Inputs

- Normalized document text (from ingest pipeline).
- Existing case actors (from the case's Actor rows, including seeded plaintiff/defendant/court).

## 3. Rules

- Proper-noun 2-4 token phrases, optionally prefixed by `Mr./Mrs./Ms./Dr./Hon./Judge/Attorney/Counsel/Rev/Prof/Sen/Rep/Gov.`.
- Organization suffix match: `Inc./LLC/L.L.C./Corp./Corporation/Company/Co./Partnership/LP/PLC/GmbH/Ltd.`.
- Stop-phrase filter removes salutations, month/day names, generic boilerplate.

## 4. Resolution semantics

- Exact canonical match (lowercased, title-stripped, punctuation-stripped) → RESOLVED.
- Substring-containment fuzzy match to exactly one existing canonical → RESOLVED.
- Substring-containment fuzzy match to multiple existing canonicals → AMBIGUOUS.
- No match → CANDIDATE.

RESOLVED rows are never auto-downgraded by later extractions.

## 5. Outputs

- `Actor` rows (one per canonical per case; `mention_count` updated on re-encounters).
- `ActorMention` rows per occurrence: `snippet`, `offset_start/end`, `confidence`.

## 6. Attorney review

- `PATCH /actors/{id}` promotes CANDIDATE→RESOLVED, splits AMBIGUOUS, adjusts `entity_type` / `role_hint`.
- `GET /actors/{id}/mentions` surfaces source documents for verification.

## 7. Non-goals

- No cross-case actor linking.
- No entity-disambiguation ML.
- No address extraction, no phone/email extraction (future work).
- No authority resolution.

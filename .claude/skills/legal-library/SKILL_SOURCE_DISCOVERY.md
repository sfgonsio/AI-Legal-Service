# SKILL_SOURCE_DISCOVERY

## Use when

- No accepted source candidate exists for a target authority (e.g., a CACI instruction, a statute section, a regulation cite).
- The legal-library inventory has identified a gap that needs candidate-source proposals.

## Do NOT use when

- A source candidate has already been verified — use `SKILL_SOURCE_VERIFICATION` instead.
- The target authority is already in `contract/v1/knowledge/authority_catalog.yaml` with a known canonical source.
- The target is not a legal authority (e.g., case-specific facts, attorney work product).

## Inputs

- `target_authority_id` (e.g., `CACI_1900`, `EVID_500`)
- `jurisdiction` (country / state / county / city)
- `authority_type` (statute, regulation, jury_instruction, etc.)
- `hierarchy_class` reference from `contract/v1/doctrine/LEGAL_SOURCE_HIERARCHY.md`

## Procedure

1. Identify the official publisher per `LEGAL_SOURCE_HIERARCHY.md` for the given authority type and jurisdiction.
2. Locate primary URLs / locations served by the official publisher.
3. Locate, if any, official secondary access pathways (e.g., GovInfo, eCFR, official judicial council pages).
4. Reject any candidate that is not traceable to an official publisher.
5. Record candidate metadata: URL, publisher, access method, candidate type (primary | authorized | secondary).

## Outputs

`SOURCE_CANDIDATE_LIST` — ordered list of candidates per target authority, with publisher class and access pathway notes.

## Validation rules

- Every candidate must include a publisher and a pathway.
- No candidate may be from an unofficial scraper, aggregator, or summarizing site.
- No candidate may be from model knowledge alone; every entry must be externally verifiable.

## Failure modes

- No official publisher exists for the requested target → return an empty list with a `NO_OFFICIAL_PUBLISHER` reason code.
- Publisher exists but candidate pathway is paywalled or behind a non-authorized portal → record with `RESTRICTED_ACCESS` and route to user for credential decision.

## Test fixture expectations

- Fixture: known-good target (e.g., `EVID_500`) must produce at least one candidate from the official California Legislative Information publisher.
- Fixture: nonsense target must produce an empty list with `NO_OFFICIAL_PUBLISHER`.

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

This skill MUST NOT be invoked for live source discovery, candidate persistence, or downstream pipeline activation until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` (defined in `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md`) is completed and approved. Test-fixture exercises only until the gate clears.

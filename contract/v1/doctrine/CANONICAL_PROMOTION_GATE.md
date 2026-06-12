# CANONICAL_PROMOTION_GATE

## Scope

Defines the gates that must be satisfied before any authority item may be promoted into the canonical spine.

## Required gates (all must pass)

1. Source verified as official or legally authoritative per `LEGAL_SOURCE_HIERARCHY.md`.
2. Official text captured accurately and provenance hash recorded.
3. Jurisdiction confirmed.
4. Authority type confirmed.
5. Effective/version date recorded or explicitly marked `unknown` with justification.
6. Citation complete per `AUTHORITY_INTAKE_MANIFEST_SCHEMA.md`.
7. Provenance hash created for both raw capture and normalized form.
8. Normalization preserves original legal meaning (judge review passed).
9. COA / burden / remedy / admissibility applicability assessed (attorney review passed).
10. No-drift review passed (no contamination, no reverse flow, no AI-invented content, no evidence influence).
11. No case-evidence or case-fact influenced the authority.
12. No AI invented or paraphrased authority text.
13. No non-canonical material contaminated the canonical item.
14. Completeness scorecard within acceptable range for the authority's expected scope.
15. Promotion packet assembled per `SKILL_PROMOTION_PACKET`.
16. Promotion packet approved by an authorized human reviewer (signature block populated).

## Promotion is not automatic

Promotion may not be performed by any agent autonomously. The `AGENT_CANONICAL_SPINE_GOVERNOR` may **recommend** promotion; the actual canonical write requires a human-approved signed packet.

## Failure handling

Any gate failure routes the item to revision or quarantine per `REJECTION_QUARANTINE_PROTOCOL.md`. The item may not bypass any gate.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 14
- `contract/v1/doctrine/LEGAL_SPINE_DOCTRINE.md`
- `contract/v1/doctrine/REJECTION_QUARANTINE_PROTOCOL.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live canonical promotion may occur until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved. The gates defined here apply equally during and after reconciliation — reconciliation does not weaken any gate.

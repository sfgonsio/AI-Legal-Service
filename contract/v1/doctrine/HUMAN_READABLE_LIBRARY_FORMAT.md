# HUMAN_READABLE_LIBRARY_FORMAT

## Scope

Defines the format for human-readable library pages rendered from canonical authority.

## Direction of derivation

```text
canonical structured law (AUTHORITY_PACK_FORMAT)
        ↓
human-readable markdown / library page
```

Never the reverse. Human-readable text is **not** canonical authority.

## Required page sections (in order)

1. Title
2. Jurisdiction
3. Authority Type
4. Official Citation
5. Source / Accessed Date
6. Effective Date / Version
7. Official Text
8. Plain-English Explanation
9. Legal Use
10. COA / Burden / Remedy Connections
11. Related Authorities
12. Review Status
13. Canonical Status
14. Warnings / Limitations

## Population rules

- Every section either pulls from the canonical authority pack with explicit citation, or is marked `[missing-canonical]`.
- No section may contain content not traceable to the canonical pack.
- `Plain-English Explanation` may rephrase for readability but may not change legal meaning; the official text is the binding text.
- `Warnings / Limitations` must include any `[missing-canonical]` markers found elsewhere on the page, aggregated.

## Footer requirement

Every page footer must include the canonical authority pack's `authority_id` and `provenance_hash` so the rendering is traceable to a specific canonical version.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 9
- `contract/v1/doctrine/AUTHORITY_PACK_FORMAT.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live human-readable library page may be published until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved.

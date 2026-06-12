# LEGAL_SOURCE_HIERARCHY

## Scope

Defines the authoritative-source hierarchy used by `AGENT_LEGAL_SOURCE_VERIFIER` to classify candidate sources.

## Principle

Official or legally authoritative sources are used first. Secondary sources may assist research but may never become canonical authority.

## Hierarchy table

| Authority type | Accepted source priority |
|---|---|
| Federal statutes | Official U.S. Code / official government source |
| Federal regulations | eCFR, CFR, agency official sources, GovInfo where appropriate |
| State statutes | Official state legislative source |
| State jury instructions | Official judicial council / official court source |
| County law | Official county code, county court, county agency, or official code publisher under county authority |
| City law | Official municipal code, city agency, or official code publisher under city authority |
| Industry law | Official regulator, licensing body, statutory scheme, rulemaking authority, agency guidance |
| GAAP | FASB Accounting Standards Codification / official FASB materials or authorized access pathway |
| Internal Revenue Code / Federal Tax Code | Official IRC / U.S. Code Title 26 / official federal tax source |
| Treasury Regulations | Code of Federal Regulations Title 26, eCFR, Treasury official materials |
| IRS guidance | IRS official guidance, Revenue Rulings, Revenue Procedures, Notices, Announcements, Internal Revenue Bulletin |

## Verifier requirements

The source verifier must document, for every classified source:

- Source publisher and class against the hierarchy.
- Access date (ISO 8601, UTC).
- Version or effective date (or explicit `unknown` with justification).
- Jurisdiction (country / state / county / city).
- Citation completeness.

## Secondary sources

Secondary sources (treatises, practitioner aggregators, commercial databases) may be cited as **research aids** in review notes but may not be used as the canonical source of authority text.

## References

- `contract/v1/LEGAL_LIBRARY_AGENT_CONTROL_PLANE.md` Section 5
- `contract/v1/doctrine/CANONICAL_PROMOTION_GATE.md`

## HARD GATE — CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION

No live source classification may produce canonical records until the preflight `CONTRACT_V1_AUTHORITY_CATALOG_RECONCILIATION` is completed and approved.

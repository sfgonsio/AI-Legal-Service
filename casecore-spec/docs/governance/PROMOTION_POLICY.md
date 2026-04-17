# /casecore-spec/docs/governance/PROMOTION_POLICY.md

# PROMOTION POLICY

## Purpose
Define how proposal artifacts may become canonical artifacts.

## Core Rule
No proposal becomes canonical without governed validation and authorized promotion.

## Promotion Stages
1. Proposal created
2. Schema validated
3. Provenance validated
4. Review state established
5. Human or governed approval action recorded
6. Promotion executed by platform service
7. Audit event recorded
8. Lineage updated

## Artifact Classes
### Facts
- proposal facts may be promoted to canonical facts
- human review is normally required

### Events
- event proposals may be promoted after fact and provenance checks
- conflict flags must be preserved, not erased

### Narrative Outputs
- narrative outputs are generally proposal/support artifacts
- they should not become canonical facts merely by approval

## Prohibited
- direct model promotion
- silent auto-promotion
- promotion without audit record
- promotion without source refs

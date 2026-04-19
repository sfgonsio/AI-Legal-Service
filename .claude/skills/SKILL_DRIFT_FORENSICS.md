# SKILL_DRIFT_FORENSICS

## Mission
Detect unauthorized drift in proposed execution or generated patches.

## Detect
- invented schema fields
- invented routes
- invented folders
- invented tables
- out-of-scope file modifications
- route-pattern mismatch
- source-of-truth duplication
- canonical/non-canonical leakage
- deprecated field reuse in new logic

## Required Checks
1. Compare changed files against allowed files in active slice contract
2. Compare introduced fields against actual provided models and schemas
3. Compare route shape against actual route samples
4. Verify no forbidden semantics appear in patch

## Required Outcome
If any unauthorized drift is found:
- BLOCK before generation, or
- HALT after generation
# /casecore-spec/meta/traceability/FINAL_INTEGRATED_REVIEW_CHECKLIST.md

# FINAL INTEGRATED REVIEW CHECKLIST

## Purpose
This checklist is used to verify that CASECORE is coherent as an integrated system, not just a collection of files.

## Review Domains

### 1. Authoritative vs Derived
- `/casecore-spec` remains the sole source of truth
- `/casecore-build-kit` remains derived only
- no conflicting builder-only logic exists

### 2. Naming
- internal naming remains `casecore`
- deprecated names exist only in explicitly allowed exception files

### 3. Contract Completeness
- schemas exist
- APIs exist
- events exist
- enums exist
- audit rules exist
- workflow rules exist
- program contracts exist
- agent contracts exist
- taxonomies exist
- manifest exists

### 4. Validation
- schema example validation passes
- pipeline validation passes
- runtime enforcement passes
- CI workflow exists

### 5. Frontend Truth
- proposal vs canonical distinction is preserved
- truth-labeling rules exist
- view-model policy exists

### 6. Governance
- promotion policy exists
- model governance exists
- runtime enforcement policy exists
- responsibility matrix exists
- integration contract exists

### 7. Persistence and DB
- data model exists
- entity relationship model exists
- DDL exists
- migration strategy exists
- indexing strategy exists

### 8. Traceability
- inventories refreshed
- integrated review updated
- build-kit inventory exists

## Final Rule
CASECORE is only considered handoff-ready when all review domains pass without contradiction.

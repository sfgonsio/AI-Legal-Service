# /casecore-spec/docs/governance/INDEXING_STRATEGY.md

# INDEXING STRATEGY

## Purpose
Define search/index separation from canonical persistence.

## Rules
- canonical truth lives in relational persistence
- search index supports retrieval and exploration
- search index is not source of truth
- reindexing must be possible from canonical records and source files

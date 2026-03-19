# /casecore-spec/docs/governance/COMPONENT_ACCEPTANCE_CRITERIA.md

# COMPONENT ACCEPTANCE CRITERIA

## Purpose
Define done-criteria by component.

## Workflow Engine
- enforces allowed transitions
- logs material transitions
- rejects invalid progression

## Artifact Service
- stores canonical/proposal distinction
- maintains lineage metadata
- preserves schema/version metadata

## Audit Service
- append-only behavior for material events
- queryable by actor, matter, artifact, run

## LLM Gateway
- returns typed proposal envelopes
- captures model metadata
- rejects non-conforming outputs

## Frontend
- labels truth/state correctly
- exposes source drill-down where required
- does not blur proposal and canonical states

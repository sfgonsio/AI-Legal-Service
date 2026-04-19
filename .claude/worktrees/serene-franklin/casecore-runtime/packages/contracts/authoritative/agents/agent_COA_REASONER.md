# /casecore-spec/packages/contracts/agents/agent_COA_REASONER.md

# AGENT CONTRACT — COA_REASONER

## Purpose
Generate attorney-facing narrative support regarding claim-element coverage, conflicts, and gaps.

## Type
Bounded agent

## Reads
- COA coverage outputs
- fact/event support structures
- trace/provenance references

## Writes
- narrative support proposals
- discovery gap suggestions
- attorney memo proposals

## Restrictions
- no final legal conclusion
- no canonical fact mutation
- must preserve uncertainty and support boundaries

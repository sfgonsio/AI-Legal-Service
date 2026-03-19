# /casecore-spec/packages/contracts/agents/agent_MAPPING_AGENT.md

# AGENT CONTRACT — MAPPING_AGENT

## Purpose
Assist in proposing links between facts, events, entities, and legal structures.

## Type
Bounded agent

## Reads
- fact proposals/canonical facts
- event proposals/canonical events
- entity records
- governed taxonomies

## Writes
- proposal artifacts only
- mapping suggestions
- gap notes

## Restrictions
- no direct canonical mutation
- no hidden remapping of governed structures

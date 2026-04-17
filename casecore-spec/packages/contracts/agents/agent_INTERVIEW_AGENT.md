# /casecore-spec/packages/contracts/agents/agent_INTERVIEW_AGENT.md

# AGENT CONTRACT — INTERVIEW_AGENT

## Purpose
Support structured intake questioning and intake proposal generation.

## Type
Bounded agent

## Reads
- intake prompts
- prior intake context
- matter setup context

## Writes
- intake proposal artifacts
- issue prompts
- structured interview outputs

## Restrictions
- may not set canonical facts directly
- may not approve case posture
- may not render final legal advice

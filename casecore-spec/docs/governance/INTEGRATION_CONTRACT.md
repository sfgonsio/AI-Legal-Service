# /casecore-spec/docs/governance/INTEGRATION_CONTRACT.md

# INTEGRATION CONTRACT

## Purpose
Define how all major subsystems integrate safely.

## Core Integration Rule
No subsystem may bypass governed contracts to mutate canonical system state.

## Required Integration Boundary
- contracts/schemas define shape
- contracts/apis define exchange
- contracts/events define async signaling
- audit contracts define log obligations
- workflow contracts define allowed state progression

## Claude Boundary
Claude-originated outputs must enter as proposal artifacts only.

## Frontend Boundary
Frontend may not invent or mutate canonical semantics.

## Persistence Boundary
Relational persistence stores source-of-truth records; search/index infrastructure is supportive, not authoritative.

## Rule
Integration convenience may not override determinism, auditability, or proposal/canonical separation.

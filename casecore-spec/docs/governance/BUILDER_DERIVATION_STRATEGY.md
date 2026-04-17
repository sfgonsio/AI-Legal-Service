# /casecore-spec/docs/governance/BUILDER_DERIVATION_STRATEGY.md

# BUILDER DERIVATION STRATEGY

## Purpose
Define how the builder-facing execution directory will be derived.

## Source
- `/casecore-spec` is the sole authoritative source

## Derived Build Areas
- platform core
- contracts and workflows
- database and persistence
- frontend and design system
- AI/proposal subsystem
- security/ops/acceptance

## Rules
- no derived file may become a competing source of truth
- derived build-kit docs should point back to authoritative source paths
- derived builder grouping is for execution convenience only

# /casecore-spec/docs/governance/ENGINEERING_OPERATING_MODEL.md

# ENGINEERING OPERATING MODEL

## Purpose
Define how implementation work is governed.

## Repository Model
- `/casecore-spec` is the authoritative specification repository area
- build-facing materials must derive from it
- implementation should preserve contract-first discipline

## Required Practices
- typed contracts first
- schema/version awareness
- ADR-driven material change control
- traceability updates for major changes
- fixture validation before major promotion/release

## Review Expectations
- naming rules checked
- proposal/canonical separation preserved
- audit obligations preserved
- frontend truth-labeling preserved

## Rule
Engineering speed is important, but not at the expense of governed semantics.

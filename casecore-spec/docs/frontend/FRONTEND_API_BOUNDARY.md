# /casecore-spec/docs/frontend/FRONTEND_API_BOUNDARY.md

# FRONTEND API BOUNDARY

## Purpose
Define frontend/backend interaction discipline.

## Rules
- frontend does not invent canonical state
- frontend consumes typed APIs
- frontend may compose view models, but may not alter authoritative artifact semantics
- proposal/canonical distinction must be preserved from API to UI

## Required Behavior
- explicit API typing
- explicit empty/error states
- no hidden fallback language that changes legal meaning

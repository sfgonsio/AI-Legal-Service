# /casecore-runtime/apps/api/README.md

# CASECORE RUNTIME API

## Purpose
Expose governed CASECORE runtime capabilities through an API surface.

## Initial Routes
- GET /health
- POST /runs
- GET /runs/{run_id}
- GET /artifacts/{artifact_id}
- POST /artifacts/promote
- GET /audit/{target_id}

## Rules
- no write path may bypass validators
- no promotion path may bypass runtime enforcement
- no route may silently invent canonical state

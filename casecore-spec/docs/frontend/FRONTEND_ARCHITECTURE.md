# /casecore-spec/docs/frontend/FRONTEND_ARCHITECTURE.md

# FRONTEND ARCHITECTURE

## Purpose
Define the frontend structure for CASECORE.

## Design Principles
- Matter-centric navigation
- Clear distinction between canonical and proposal states
- Traceability first
- Review workflows first-class
- Evidence drill-down always available from supported outputs

## Primary Surfaces
- Matter dashboard
- Evidence explorer
- Fact review workbench
- Timeline/event workspace
- COA coverage matrix
- Audit/trace viewer
- Admin/configuration screens

## State Rules
- UI must never present proposal artifacts as canonical without explicit label/state.
- UI must reflect workflow/review state clearly.
- UI must allow source drill-down for attorney trust.

## Technical Direction
- React + TypeScript
- shared design system
- typed API client
- clear separation between view models and canonical artifact models

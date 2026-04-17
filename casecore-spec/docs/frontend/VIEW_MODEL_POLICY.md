# /casecore-spec/docs/frontend/VIEW_MODEL_POLICY.md

# VIEW MODEL POLICY

## Purpose
Define the line between backend artifacts and frontend-composed view models.

## Rules
- frontend may compose display-focused models
- frontend may not alter canonical meaning
- frontend view models must preserve artifact state
- backend contract changes may require coordinated view-model changes

## Rule
UI convenience may not flatten or blur canonical/proposal distinctions.

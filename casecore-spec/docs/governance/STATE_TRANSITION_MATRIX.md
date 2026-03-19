# /casecore-spec/docs/governance/STATE_TRANSITION_MATRIX.md

# STATE TRANSITION MATRIX

## Purpose
Human-readable companion to workflow transition contracts.

| Object | From | To | Allowed |
|---|---|---|---|
| artifact | proposed | canonical | yes, governed only |
| artifact | proposed | rejected | yes |
| artifact | canonical | rejected | governed exception only |
| review | pending | approved | yes |
| review | pending | rejected | yes |
| review | approved | overridden | governed exception only |

## Rule
If a transition is not allowed by contract/workflow governance, it must be rejected.

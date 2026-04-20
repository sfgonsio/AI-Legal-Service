# GO_FORWARD_DEPRECATION_RULES

## Purpose
Enable forward progress without immediate full consolidation of duplicate structures.  
Reduce drift risk by enforcing a single set of authoritative paths for new work.

---

## Authoritative Paths (USE ONLY THESE)

All new work must use:

- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\contract\v1\agents`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\contract\v1\skills`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\contract\v1\slices`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-runtime\apps\api\casecore\backend`

These paths are the **only source of truth** for:
- agent definitions
- skills
- slice contracts
- active backend implementation

---

## Deprecated / Non-Authoritative Paths (DO NOT USE)

The following are **deprecated for active development**:

- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-build-kit\**`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-runtime\packages\contracts\authoritative\**`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec\packages\contracts\**`
- `C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-runtime\production\backend\**`
- Any duplicate or shadow definitions of:
  - agents
  - skills
  - programs
  outside the authoritative paths

These may exist for:
- legacy
- reference
- prior experiments

They are **not valid for new work**.

---

## Go-Forward Rule

When performing new work:

1. Use only authoritative paths.
2. Do not clean, refactor, or migrate deprecated paths during unrelated feature work.
3. If a deprecated path is encountered and appears required:

   - PAUSE
   - CLASSIFY the path
   - Decide explicitly:

     - **YES (promote):**
       - bring forward intentionally into authoritative structure
       - update references as part of a controlled change

     - **NO (ignore):**
       - leave as deprecated
       - continue work using authoritative paths

---

## No-Drift Rule

No new work may:

- introduce additional authoritative locations for:
  - agents
  - skills
  - slice contracts
  - backend logic

- reference deprecated paths unless explicitly approved

---

## Runtime Consideration

If runtime mirrors exist (e.g., `.claude/`):

- they must be treated as **derived artifacts**
- they must not become a second source of truth
- they must align with:

  `C:\Users\sfgon\Documents\GitHub\AI Legal Service\contract\v1\*`

---

## Enforcement Philosophy

- Prefer forward progress over cleanup
- Fix issues when encountered, not preemptively
- Avoid large refactors during active feature delivery
- Maintain clarity of authority at all times

---

## Future Milestone

A dedicated **Source Consolidation Milestone** will:

- merge duplicate structures
- eliminate deprecated paths
- establish a permanent single-root contract (potentially `/contract`)

This is **not required** for current development progress.

---

## Summary

- One authoritative source per domain
- No new duplication
- No cleanup during feature work
- Fix only when encountered
- Move forward with discipline
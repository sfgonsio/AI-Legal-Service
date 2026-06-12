# NO-DRIFT WORKING AGREEMENT

## Status

ACTIVE — governing rule for how work is organized across branches, worktrees, and sessions. Subordinate to the existing NO-DRIFT governance system (Governor / Sentinel) in spirit; this document governs **execution hygiene** (branch/worktree/session discipline) rather than knowledge promotion.

## Why this exists

Work fragmented across multiple `claude/*` git worktrees and never consolidated onto a single line. The result: the INTAKE persistence (Wave 1) was implemented and tested inside worktree branch `claude/youthful-johnson-1ee1a2`, while the canonical working branch carried only a stub router and an **empty** `INTAKE_DB_SPEC.md` (`PASTE CONTENT HERE`). Meanwhile a dead worktree's files were committed into `main`. This document makes that class of failure a rule violation, not an accident.

## Rules

### R1 — One canonical trunk
`main` is the single canonical line. All work converges there through reviewable PRs. No long-lived silently-diverging parallel branches.

### R2 — Worktrees are temporary and tracked
Every `.claude/worktrees/*` worktree resolves to exactly one of:
- **Consolidated** — its work landed on `main` via PR; the worktree and branch are then removed; or
- **Abandoned** — explicitly declared dead and removed.

An unmerged worktree is an OPEN item. It is never silently "done." Orphaned worktrees are a drift defect.

### R3 — No worktree pollution in history
`.claude/worktrees/**` is never committed as tracked content. If found in tracked history, it is flagged for removal, not extended.

### R4 — No placeholder commits
A spec/contract file is never committed with a placeholder body (e.g. `PASTE CONTENT HERE`) under a message claiming real content. Empty specs falsely signal completion.

### R5 — Gate completion is defined, on the canonical line
A stage gate is "complete" only when its tickets are implemented on `main`, its tests/proof pass there, its governing spec is filled, and its seed cases exist. INTAKE = Wave 1 (W1-T1…W1-T7).

### R6 — Session grounding
Each working session begins by reading the stage-gate framework and wave tickets and stating the current gate/wave before acting. Identity of the repo and any referenced `#NNN` is confirmed, never assumed.

## Enforcement

These rules are mirrored in the repo-root `CLAUDE.md` so they load every session. Violations are corrected before new feature work proceeds.

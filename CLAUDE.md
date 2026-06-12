# AI Legal Service / CASECORE Project Rules

## Purpose
This repository contains governed legal-platform design, workflow, and runtime assets. Claude must preserve determinism, traceability, auditability, and reproducibility.

## Non-negotiable rules
- Never claim files are written unless they exist in the real working tree and git status or git diff confirms them.
- Never use temp folders, cache folders, exported session folders, or copied outputs as the source of truth.
- Always identify the real repo root before editing files.
- Canonical and proposal content must remain separated.
- Workflow, contract, and state consistency outrank convenience edits.
- If file path, service root, build target, or deploy target is ambiguous, stop and report the ambiguity instead of guessing.

## Execution discipline
- Prefer the smallest safe edit set.
- Verify touched files before and after editing.
- Before commit or push:
  - run git status
  - confirm changed files match intended scope
  - confirm frontend vs backend target is correct
- Do not treat UI text as legal truth unless supported by approved design and traceability.

## Repo-specific guidance
- Main legal platform logic belongs in this repository.
- Deployment-only convenience repos do not define legal architecture.
- Use project subagents from .claude/agents for repo-specific behavior.
- Use project skills from .claude/skills for repeatable procedures.

## No-drift working agreement (see contract/v1/doctrine/NO_DRIFT_WORKING_AGREEMENT.md)
These rules exist because work previously fragmented across branches/worktrees and stranded the INTAKE persistence off the canonical line.

### Identity — confirm before acting
- We build **CaseCore**; the working tree is **`sfgonsio/AI-Legal-Service`**. The separate repo `sfgonsio/casecore` (and `casecore-ui`, `Casecoredesignsystem`, `CASSCORE_DESIGN-SYSTEM`) is NOT this working tree.
- **Never assume a bare `#NNN` belongs to this repo.** Resolve which repo it is first.

### One canonical trunk — no fragmentation
- **`main` is the single canonical trunk.** All work converges there via reviewable PRs. No long-lived silently-diverging branches.
- **Worktrees are temporary.** Every `.claude/worktrees/*` worktree ends as either (a) consolidated onto `main` via PR, or (b) explicitly removed. **No orphaned worktrees** — an unmerged worktree is an OPEN item, not "done."
- **Never commit `.claude/worktrees/**` as tracked content.** Worktree files in history are pollution.

### No stub commits
- Never commit a spec/contract file whose body is a placeholder (e.g. `PASTE CONTENT HERE`) under a message claiming real content.

### Ground each session
- Before working: read `docs/case_flow/00_stage_gate_framework.md` (the six gates: INTAKE → CASE BUILD → DISCOVERY → TRIAL → RESOLUTION → CLOSURE) and `contract/v1/data/CORE_DATA_WAVE_TICKETS.md`, and state the current gate/wave. If you cannot, stop and ask.

### Gate completion is defined
- A stage gate is complete only when its tickets are implemented **on `main`**, its tests/proof pass there, its spec is filled (not a stub), and its seed cases exist. **INTAKE = Wave 1 (W1-T1…W1-T7).** Report status from the tree, never from optimism.
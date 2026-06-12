# CaseCore — Working Agreement (READ FIRST, EVERY SESSION)

This file is loaded at the start of every session. It exists to **prevent drift and fragmentation**, which have happened before. Follow it before doing any work.

## 0. Identity — confirm before acting

- We build **CaseCore**, a litigation legal platform. The working tree is **`sfgonsio/AI-Legal-Service`** (this repo).
- There is a **separate** GitHub repo `sfgonsio/casecore` with its own PR stream (e.g. `#156`). It is **NOT** checked out here and is **NOT** our working tree. Repos `casecore-ui`, `Casecoredesignsystem`, `CASSCORE_DESIGN-SYSTEM` are also not ours.
- **Never assume a bare `#NNN` belongs to this repo.** Resolve which repo it is before acting on it.

## 1. Ground yourself before any task

At session start, before proposing or changing anything:
1. Read the memory index at `~/.claude/projects/C--Users-sfgon-Documents-GitHub-AI-Legal-Service/memory/MEMORY.md` and the relevant memory files.
2. Read `docs/case_flow/00_stage_gate_framework.md` (the six governing gates) and `contract/v1/data/CORE_DATA_WAVE_TICKETS.md` (the wave plan).
3. State, in one line, **where we are and what gate/wave we are on** before doing work. If you cannot, stop and ask — do not guess.

## 2. ONE canonical working line — no fragmentation

- **`main` is the single canonical trunk.** All work converges there via reviewable PRs.
- Do **not** create long-lived parallel branches that silently diverge. If a branch exists, it has a stated purpose and a plan to land on `main` or be retired.
- **Worktrees are temporary.** Every `.claude/worktrees/*` worktree must end one of two ways: (a) its work is consolidated onto the canonical line via PR, or (b) it is explicitly abandoned and removed. **No orphaned worktrees.** A finished worktree that has not been merged is an open, tracked item — not "done."
- **Never commit `.claude/worktrees/**` contents into the repo.** Nested-worktree files in tracked history are pollution and a drift signal — flag them, don't add to them.

## 3. No stub or placeholder commits

- Do not commit a spec/contract file whose body is a placeholder (e.g. `PASTE CONTENT HERE`) while the commit message claims real content. Either write the content or do not commit it. A committed empty spec is a false signal of completion.

## 4. Stage-gate discipline

- The six governing gates are **INTAKE → CASE BUILD → DISCOVERY → TRIAL → RESOLUTION → CLOSURE** (`docs/case_flow/00_stage_gate_framework.md`). They are the only top-level workflow taxonomy. Do not invent a parallel one.
- Internal stage specs (Fact Normalization, Authority Stack, COA, etc.) live **under** a gate. Each must declare its `## Stage Gate Alignment`.

## 5. "Gate complete" has a definition — meet it, don't claim it

- **INTAKE gate = Wave 1 (W1-T1…W1-T7)** in `CORE_DATA_WAVE_TICKETS.md`. A gate is complete only when: its tickets are implemented **on the canonical line** (not stranded in a worktree), its proof script / tests pass there, its governing spec doc is filled (not a stub), and its X-T seed cases exist. Report status from the actual tree, never from memory or optimism.

## 6. Persist what you learn

- After meaningful work or any course-correction, update the memory files so the next session does not re-drift. Treat this as part of the task, not optional.

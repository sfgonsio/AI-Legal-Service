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
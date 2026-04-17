---
name: deployment-discipline
description: Use before commit, push, Vercel deploy, Render deploy, or any release-like step.
---

# Deployment Discipline

## Required checks
1. Run git status
2. Confirm changed files are expected
3. Confirm target:
   - frontend deploy
   - backend deploy
   - documentation only
4. Confirm no reliance on cache, temp, session, or exported files
5. Confirm commit scope is intentionally narrow

## Refuse release when
- working tree is clean but a deploy was expected
- changed files are outside intended scope
- wrong service is being built
- frontend and backend paths are mixed up
- unknown files are being staged
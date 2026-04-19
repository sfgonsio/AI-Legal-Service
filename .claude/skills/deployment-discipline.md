---
description: Verifies deploy-target clarity and safe release behavior before push or deployment.
tools: Read, Grep, Glob, LS, Bash
model: sonnet
---

# Purpose
Prevent wrong-target or wrong-scope deployment behavior.

# Inputs
- changed files
- repo target
- build target
- deploy target

# Outputs
- release readiness status
- blocking issues
- safe next command
# SKILL_NO_DRIFT_PATCHING

Purpose:
Force patch-only, contract-aligned generation.

Rules:
- Use only provided files
- No inferred structure
- No extra refactors
- Stop if missing data

Output:
1. Validation
2. Drift Check
3. Patch Plan
4. Code

Reject if:
- New fields invented
- Files outside scope modified
- Deprecated fields used

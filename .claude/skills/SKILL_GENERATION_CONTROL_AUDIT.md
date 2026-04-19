# SKILL_GENERATION_CONTROL_AUDIT

## Mission
Clamp model generation into deterministic, tightly governed build behavior.

## Required Controls
- temperature = 0 or lowest supported
- patch-only mode
- stop-on-ambiguity
- structured output
- bounded file scope
- single-slice scope
- no uncontrolled retries
- no freeform redesign

## Detect
- broad redesign prompts
- multiple unrelated tasks in one execution
- missing generation constraints
- freeform explanation replacing patch-oriented output
- generation settings inconsistent with governed build mode

## Required Outcome
If generation control is unsafe:
- BLOCK before generation, or
- HALT after generation
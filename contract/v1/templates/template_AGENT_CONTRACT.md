# AGENT CONTRACT TEMPLATE

This template defines the required structure for all AI agents in the AI Legal Service Platform.

Agents provide bounded reasoning, orchestration, and human interaction support.

Agents must not replace deterministic programs.

---

# 1 Agent Identity

Agent Name:

agent_<NAME>

Agent Layer:

Agents

Primary Role:

Example:

intake  
entity mapping  
legal reasoning support  
discovery planning  
deposition preparation  
trial preparation

---

# 2 Purpose

Explain:

What problem the agent solves.

Where it sits in the litigation workflow.

How it supports the reasoning pipeline.

Agents should be described as **bounded reasoning roles**, not general assistants.

---

# 3 Scope

### In Scope

List allowed behaviors.

Examples:

structured questioning  
issue spotting  
mapping suggestions  
legal reasoning assistance

### Out of Scope

Examples:

final legal judgment  
direct database mutation  
uncontrolled tool access  
cross-case reasoning

---

# 4 Trigger Conditions

Define when the agent may be invoked.

Examples:

client intake  
entity review stage  
claim analysis stage  
discovery planning stage

---

# 5 Inputs

Define allowed inputs.

Examples:

case context  
facts  
entities  
events  
patterns  
claims  
coverage outputs  
user responses

---

# 6 Outputs

Define structured outputs.

Examples:

interview transcripts  
entity mapping suggestions  
claim support analysis  
discovery targets  
deposition outlines  
trial prep summaries

Outputs must specify:

draft vs authoritative  
review requirements

---

# 7 Interaction Model

Define how the agent interacts with users.

Examples:

guided questioning  
structured prompts  
clarification loops

Agents must not behave unpredictably.

---

# 8 Reasoning Model Alignment

Map the agent to stages in:

system_REASONING_MODEL.md

Examples:

Source Material  
Facts  
Patterns  
Causes of Action  
Coverage

---

# 9 Workflow State Alignment

Map agent invocation to:

system_STATE_MODEL.md

Define:

allowed entry states  
resulting states

---

# 10 Tool Access

List tools agent may use.

Examples:

knowledge index  
entity resolver  
document search

Agents must only use registered tools.

---

# 11 Program Invocation

Agents may request execution of programs.

Examples:

program_FACT_NORMALIZATION  
program_PATTERN_ENGINE  
program_COA_ENGINE

Agents must not replace program logic.

---

# 12 Memory Constraints

Agents may use temporary context but must not treat memory as authoritative storage.

Material outputs must be persisted through governed structures.

---

# 13 Determinism Guardrails

Agent outputs must:

use structured formats  
signal uncertainty  
avoid hidden mutation

---

# 14 Provenance

Agent outputs must include:

case_id  
agent_name  
timestamp  
support references

---

# 15 Audit Events

Agents must log:

invocation  
completion  
failure  
program handoff

---

# 16 Escalation Rules

Agents must escalate when:

evidence conflicts  
legal support weak  
out-of-scope request received

---

# 17 Human Review Boundaries

Agents must never finalize:

legal claims  
litigation strategy  
court submissions

These require attorney review.

---

# 18 Human Presentation Lens

Explain agent in business terms.

Example:

"The Discovery Agent analyzes coverage gaps and proposes evidence requests."

---

# 19 Acceptance Criteria

Agent contract complete when:

inputs defined  
outputs defined  
tool access defined  
program interactions defined  
review boundaries defined

---

# 20 Authoring Notes

Agents expected in platform include:

agent_INTERVIEW_AGENT  
agent_MAPPING_AGENT  
agent_COA_REASONER  
agent_DISCOVERY_AGENT  
agent_DEPOSITION_AGENT  
agent_TRIAL_PREP_AGENT
# Program: WORKFLOW_ORCHESTRATOR

## Purpose

The WORKFLOW_ORCHESTRATOR governs the deterministic execution of platform workflows.  
It controls program sequencing, agent invocation, approval checkpoints, rerun behavior, and state transitions.

## Responsibilities

- enforce workflow ordering
- validate prerequisites before execution
- dispatch programs and agents
- manage state transitions
- enforce approval gates
- record execution provenance
- coordinate reruns and supersession
- ensure deterministic execution

## Execution Scope

The orchestrator manages execution across:

- INTERVIEW_AGENT
- FACT_NORMALIZATION
- MAPPING_AGENT
- COMPOSITE_ENGINE
- TAGGING_ENGINE
- COA_ENGINE

## Core Workflow

1. Case intake
2. Interview agent execution
3. Fact normalization
4. Evidence mapping
5. Composite event construction
6. Tagging engine execution
7. Cause-of-action generation
8. Attorney review

## Deterministic Requirements

The orchestrator must guarantee:

- deterministic program ordering
- reproducible workflow transitions
- complete execution audit trails
- replay-safe rerun behavior

## Outputs

The orchestrator records:

- workflow state transitions
- program execution records
- agent execution records
- approval checkpoints
- rerun requests
- supersession propagation

## Governance

The WORKFLOW_ORCHESTRATOR must operate exclusively through:

- the platform state model
- governed workflow rules
- contract version v1
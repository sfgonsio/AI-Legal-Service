# AI Legal Platform — Architecture

## 1. Overview

The AI Legal Platform is a deterministic, governed legal work engine designed to transform raw evidence into structured legal reasoning while preserving attorney control, auditability, replay safety, and build-ready execution contracts.

The platform is not a generic chatbot. It is a governed runtime composed of:

- AI agents
- deterministic execution programs
- workflow orchestration
- evidence graph modeling
- legal taxonomies and rules
- tool gateway enforcement
- replay and audit controls
- attorney review checkpoints

The architecture is designed to support end-to-end legal workflows from intake through legal claim assembly.

---

## 2. Core Architectural Principle

The platform separates responsibilities into distinct governed layers:

- **AI Agents** perform bounded cognitive tasks
- **Deterministic Programs** transform evidence and legal structures in reproducible ways
- **Workflow Orchestration** governs execution order, approvals, reruns, and state transitions
- **Evidence Graph** stores the platform’s structured legal data model
- **Legal Intelligence Assets** define the legal taxonomy and rule logic
- **Tool Gateway** controls safe system access
- **Replay and Audit Controls** ensure defensibility and determinism

This separation is what makes the platform buildable, explainable, and trustworthy.

---

## 3. End-to-End Workflow

The platform supports the following governed execution flow:

```text
Client / Attorney Trigger
        ↓
INTERVIEW_AGENT
        ↓
FACT_NORMALIZATION
        ↓
MAPPING_AGENT
        ↓
COMPOSITE_ENGINE
        ↓
TAGGING_ENGINE
        ↓
COA_ENGINE
        ↓
Attorney Review
        ↓
Rerun / Approval / Closure
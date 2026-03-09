# AI Legal Platform — File Index

## Overview

This document describes the full repository structure of the AI Legal Platform.
The repository contains the authoritative Contract v1 specification used to build
the deterministic AI legal reasoning system.

The platform is organized into several layers:

- runtime contracts
- deterministic execution programs
- AI agents
- orchestration rules
- legal reasoning assets
- evidence graph schema
- tool runtime gateway
- deterministic replay harness

---

# Repository Structure

AI Legal Service/
├── contract/v1/
│
│   ├── agents/
│   ├── programs/
│   ├── orchestration/
│   ├── taxonomies/
│   ├── rules/
│   ├── schemas/
│   ├── tools/
│   ├── harness/
│   └── system/
│
└── docs/

---

# Platform Runtime Layer

## contract/v1/system/platform_runtime_contract.md

Purpose  
Defines the complete runtime contract for the AI Legal platform.

Role in Platform  
This document binds together all agents, programs, orchestration rules,
schemas, tools, and replay requirements into a single governed runtime.

Why It Matters  
This file defines how the system must behave when implemented.

---

## contract/v1/system/platform_build_index.yaml

Purpose  
Lists all platform components required to assemble the runtime.

Role in Platform  
Allows implementation platforms (Antigravity, Claude, etc.) to identify
the contracts that must be loaded to build the system.

Why It Matters  
This is the **system assembly map**.

---

# AI Agent Contracts

## contract/v1/agents/agent_INTERVIEW_AGENT.md

Purpose  
Defines the AI agent responsible for conducting structured client interviews.

Role in Platform  
Captures case information and converts it into structured intake records.

Why It Matters  
This is the entry point of the platform workflow.

---

(continue this pattern for all files)
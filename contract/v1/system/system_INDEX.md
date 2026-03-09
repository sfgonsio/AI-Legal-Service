# AI Legal Service Platform  
## System Architecture Index

This document provides the authoritative index of the **system-level architecture specifications** for the AI Legal Service Platform.

Its purpose is to prevent architectural drift and ensure that developers, architects, and agents know **where each category of system constraint or behavior is defined.**

Only the documents listed here define the official system architecture.

---

# 1. Platform Architecture

### system_STACK_ARCHITECTURE.md

Defines the structural layers of the platform.

Platform layer model:

SPINE  
DATA GRAPH  
PROGRAMS  
AGENTS  
UI

This document governs **where functionality belongs in the platform.**

No component may violate these layer boundaries.

---

# 2. Litigation Reasoning Model

### system_REASONING_MODEL.md

Defines the intelligence pipeline used by the platform to transform raw case material into structured legal reasoning.

Canonical reasoning progression:

Source Material  
→ Facts  
→ Entities & Relationships  
→ Events  
→ Signals  
→ Patterns  
→ Causes of Action  
→ Coverage  
→ Strategy Support

This document governs **how the platform thinks**.

No program or agent may bypass intermediate reasoning layers without explicit contract definition.

---

# 3. Evidence Graph

### system_EVIDENCE_GRAPH.md

Defines the **authoritative case data model** used by the platform.

Core structures include:

- cases
- documents
- fragments
- facts
- entities
- aliases
- relationships
- events
- signals
- patterns
- causes_of_action
- coverage
- provenance
- review_state

This document governs **how litigation memory is stored and structured.**

---

# 4. Workflow State Model

### system_STATE_MODEL.md

Defines the lifecycle and workflow states through which case intelligence moves.

Typical state progression:

source_capture  
→ fact_normalization  
→ entity_mapping  
→ event_construction  
→ pattern_detection  
→ coa_analysis  
→ coverage_evaluation  
→ attorney_review  
→ revision_or_approval  
→ strategy_support_ready

This document governs **how case work progresses through the platform.**

---

# 5. Relationship to Other System Specifications

System-level documents interact with other specification domains:

### Execution Programs

Defined in:

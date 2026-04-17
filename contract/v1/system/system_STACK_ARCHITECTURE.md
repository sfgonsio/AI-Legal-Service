Absolutely. Here is the **SSOT-ready draft** for `system_STACK_ARCHITECTURE.md`.

Copy this directly into your repo as:

`contract/v1/system/system_STACK_ARCHITECTURE.md`

---

# system_STACK_ARCHITECTURE.md

## 1. Document Purpose

This document defines the authoritative platform layer model for the **AI Legal Service Platform**. It establishes the structural boundaries, responsibilities, interfaces, and constraints across the full system stack so that all future agents, programs, workflows, data models, and user interfaces are implemented consistently.

This document exists to prevent architectural drift, responsibility overlap, and implementation ambiguity.

If any downstream specification conflicts with this document, this document governs until formally revised through controlled change.

---

## 2. Scope

This document governs the platform stack for:

* deterministic execution
* evidence-bound legal workflows
* AI reasoning agents
* deterministic program modules
* evidence graph persistence
* attorney-facing application behavior
* auditability and replay governance

This document applies to all current and future:

* agents
* programs
* services
* data stores
* workflow engines
* UI surfaces
* integrations
* approval paths

---

## 3. Architectural Principle

The platform is a **governed litigation reasoning system** composed of five primary layers:

1. **Spine**
2. **Data Graph**
3. **Programs**
4. **Agents**
5. **UI**

These layers must remain structurally distinct.

Core rule:

**The Spine governs the platform. The Data Graph stores authoritative case memory. Programs compute deterministically. Agents reason within bounds. The UI presents and routes, but does not own system truth.**

---

## 4. Stack Overview

### 4.1 Canonical Layer Order

From lowest to highest:

1. **Spine**
2. **Data Graph**
3. **Programs**
4. **Agents**
5. **UI**

### 4.2 Execution Hierarchy

The platform operates according to the following control model:

* the **Spine** defines rules, validation, permissions, replay, and audit constraints
* the **Data Graph** holds authoritative structured case state
* **Programs** perform deterministic transforms against governed inputs
* **Agents** interpret, reason, propose, and orchestrate next actions within approved boundaries
* the **UI** exposes workflows, status, review surfaces, and approvals to humans

### 4.3 Non-Negotiable Rule

No upper layer may violate lower-layer constraints.

Examples:

* UI cannot bypass program contracts
* agents cannot bypass tool registry or lane governance
* programs cannot silently mutate authoritative stores
* data cannot exist outside case boundaries
* no component may bypass Spine controls

---

## 5. Layer Definitions

---

## 5.1 SPINE Layer

### 5.1.1 Purpose

The Spine is the platform’s deterministic governance layer. It ensures that all system behavior is controlled, validated, auditable, replayable, and bounded.

### 5.1.2 Responsibilities

The Spine is responsible for:

* contract validation
* manifest governance
* allowed tool access
* lane enforcement
* deterministic execution rules
* replay validation
* audit event requirements
* repository integrity checks
* case boundary enforcement
* prohibited action enforcement
* run identity and replay comparability

### 5.1.3 Canonical Spine Components

Examples include:

* `contract_manifest`
* `tool_registry`
* `lanes`
* `roles`
* `validator`
* `replay harness`
* `audit governance`
* `acceptance checklist`
* `build integrity checks`
* deterministic fingerprinting mechanisms
* contract hash locking

### 5.1.4 Spine Rules

The Spine must:

* govern all agent and program actions
* define which tools may be called
* define which roles may perform which actions
* validate structural integrity before execution
* require auditable events for governed actions
* prevent silent drift across contract-bound artifacts

### 5.1.5 Spine Prohibitions

The Spine must never:

* contain business UI logic
* contain case-specific reasoning output
* act as a substitute for the Data Graph
* act as an AI agent
* allow direct uncontrolled tool invocation
* permit ungoverned state mutation

### 5.1.6 Core Principle

**The Spine is not an app feature. It is the platform control system.**

---

## 5.2 DATA GRAPH Layer

### 5.2.1 Purpose

The Data Graph is the authoritative persistent case memory for the platform. It stores structured legal matter data derived from documents, interviews, mappings, events, relationships, signals, patterns, and legal reasoning outputs that have been accepted into governed case state.

### 5.2.2 Responsibilities

The Data Graph is responsible for storing:

* cases
* matters
* documents
* document provenance
* entities
* aliases
* facts
* events
* relationships
* signals
* patterns
* causes of action
* evidence links
* coverage assessments
* review status
* confidence metadata
* provenance keys
* approvals and disposition states as assigned by system design

### 5.2.3 Data Graph Characteristics

The Data Graph must be:

* authoritative
* case-bounded
* queryable
* structured
* auditable
* version-aware
* provenance-linked
* replay-compatible
* accessible only through governed interfaces

### 5.2.4 Authoritative Memory Rule

The Data Graph is the authoritative memory of the platform.

If information matters to case state, workflow progression, legal reasoning traceability, or attorney review, it must be stored in the Data Graph or a governed authoritative store defined by contract.

### 5.2.5 Data Graph Prohibitions

The Data Graph must never:

* store uncontrolled agent scratch memory as authoritative fact
* be mutated directly by the UI
* be mutated by an agent outside governed write paths
* accept records without provenance requirements
* cross case boundaries unless explicitly authorized by future architecture

### 5.2.6 Core Principle

**Nothing material to litigation state may live only inside agent memory.**

---

## 5.3 PROGRAM Layer

### 5.3.1 Purpose

Programs are deterministic execution modules that transform governed inputs into governed outputs according to explicit contracts.

Programs perform bounded system computation.

### 5.3.2 Responsibilities

Programs are responsible for:

* deterministic transformations
* normalization
* composite generation
* pattern detection
* legal structuring logic
* scoring
* coverage analysis
* replayable computations
* bounded writes to authoritative stores
* emitting auditable execution events

### 5.3.3 Canonical Programs

Examples include:

* `program_FACT_NORMALIZATION`
* `program_COMPOSITE_ENGINE`
* `program_PATTERN_ENGINE`
* `program_COA_ENGINE`
* `program_COVERAGE_ENGINE`

### 5.3.4 Program Characteristics

Programs must be:

* contract-defined
* input-bounded
* output-defined
* deterministic or deterministically constrained
* replayable
* auditable
* lane-governed
* explicit in failure handling
* explicit in side effects
* explicit in which authoritative stores they may read and write

### 5.3.5 Program Write Rule

Programs may write to authoritative stores only through governed and auditable paths defined in their contract.

No program may perform silent mutation.

### 5.3.6 Program Prohibitions

Programs must never:

* improvise outside contract scope
* act as conversational agents
* store opaque reasoning blobs as system truth
* perform uncontrolled external calls
* alter case state without emitting required audit events
* bypass approval gates
* rely on hidden non-contractual state

### 5.3.7 Core Principle

**Programs compute. They do not “think” in an unconstrained sense.**

---

## 5.4 AGENT Layer

### 5.4.1 Purpose

Agents are bounded reasoning and orchestration components that interpret context, interact with humans or workflows, propose structured outputs, and trigger deterministic program execution where appropriate.

### 5.4.2 Responsibilities

Agents are responsible for:

* question sequencing
* context interpretation
* human interaction
* mapping suggestions
* legal reasoning proposals
* workflow routing
* issue spotting
* escalation
* recommendation generation
* structured output preparation
* initiating approved program flows

### 5.4.3 Canonical Agents

Examples include:

* `INTERVIEW_AGENT`
* `MAPPING_AGENT`
* `COA_REASONER`
* `DISCOVERY_AGENT`
* `DEPOSITION_AGENT`
* `TRIAL_PREP_AGENT`

### 5.4.4 Agent Characteristics

Agents must be:

* bounded by contract
* lane-governed
* tool-restricted
* case-bounded
* explicit about confidence and uncertainty where required
* non-authoritative unless outputs are accepted into governed state
* auditable in actions that affect workflow or persistent state

### 5.4.5 Agent Memory Rule

Agent memory is temporary and non-authoritative unless the contents are explicitly converted into governed persistent structures.

Temporary reasoning context may support agent performance, but it must not be treated as authoritative case truth.

### 5.4.6 Agent Prohibitions

Agents must never:

* directly redefine legal truth in authoritative stores without governed acceptance paths
* call tools outside allowed registry and lanes
* cross case boundaries
* silently mutate system state
* bypass deterministic program modules when deterministic computation is required
* become informal substitutes for program logic
* become unbounded general-purpose assistants inside the platform runtime

### 5.4.7 Core Principle

**Agents think. Programs compute. Agents do not own authoritative truth.**

---

## 5.5 UI Layer

### 5.5.1 Purpose

The UI is the human-facing application shell through which attorneys, staff, and approved users interact with the platform.

The UI exists to collect inputs, present outputs, route workflows, support review, and surface status.

### 5.5.2 Responsibilities

The UI is responsible for:

* intake surfaces
* workflow visualization
* evidence review screens
* timeline and graph views
* approvals and review actions
* routing user commands into governed platform workflows
* displaying outputs from agents and programs
* presenting errors, status, and audit-related user feedback
* role-based interaction surfaces

### 5.5.3 UI Characteristics

The UI must be:

* role-aware
* state-aware
* contract-aligned
* non-authoritative for core case logic
* a consumer of platform state, not the source of truth
* consistent with governed workflow states

### 5.5.4 UI Prohibitions

The UI must never:

* act as the authoritative store of case state
* embed hidden business logic that bypasses programs or agents
* make direct uncontrolled writes to the Data Graph
* bypass the Spine
* create case state transitions outside governed workflows
* become the runtime owner of legal reasoning rules

### 5.5.5 Core Principle

**The UI is a shell and control surface, not the litigation engine itself.**

---

## 6. Cross-Layer Interaction Rules

### 6.1 Allowed Primary Interaction Pattern

The preferred interaction pattern is:

**UI → Agents and/or Programs → Data Graph → governed by Spine**

All execution is governed by the Spine, whether invoked directly or indirectly.

### 6.2 Programs and Data Graph

Programs may read and write governed data according to contract.

### 6.3 Agents and Programs

Agents may invoke Programs only where:

* the program is authorized
* the lane permits execution
* required inputs are present
* audit requirements are satisfied
* the program contract allows the invocation context

### 6.4 UI and Agents

The UI may interact with agents for:

* interviews
* guided workflows
* reviews
* recommendations
* structured question-answer exchanges
* decision support surfaces

### 6.5 UI and Programs

The UI may trigger programs only through governed application paths. The UI must not directly embody the program contract.

### 6.6 Spine and All Layers

The Spine governs all layers and is not optional.

---

## 7. Explicit Boundary Rules

### 7.1 Spine vs Data Graph

* Spine governs the rules
* Data Graph stores the case memory

The Spine does not replace the Data Graph.
The Data Graph does not replace governance.

### 7.2 Data Graph vs Agent Memory

* Data Graph is authoritative and persistent
* agent memory is temporary and non-authoritative

### 7.3 Programs vs Agents

* Programs perform deterministic transforms
* Agents perform bounded reasoning and orchestration

If the platform must produce repeatable computational output, that behavior belongs in a Program, not an Agent.

### 7.4 Agents vs UI

* Agents reason
* UI presents, captures, routes, and displays

The UI must not hide or replicate agent logic in uncontrolled ways.

### 7.5 Programs vs UI

* Programs implement system computation
* UI triggers and displays results

The UI must not embed authoritative transformation logic.

---

## 8. Authoritative Source of Truth Rules

### 8.1 Platform Governance Truth

The Spine is the authoritative source of truth for:

* allowed system structure
* validation requirements
* tool access constraints
* deterministic governance rules
* replay expectations
* audit constraints

### 8.2 Case Data Truth

The Data Graph is the authoritative source of truth for:

* persisted case entities
* persisted facts
* persisted relationships
* persisted events
* persisted signals
* persisted patterns
* persisted cause-of-action structures
* persisted review state, where modeled there
* provenance-linked case memory

### 8.3 Execution Truth

Program contracts define authoritative execution behavior for deterministic modules.

### 8.4 Interaction Truth

Agent contracts define authoritative behavior for agent roles.

### 8.5 Presentation Truth

UI specifications define display and interaction behavior, but if UI behavior conflicts with lower-layer contracts, lower-layer contracts govern.

---

## 9. Determinism and Audit Requirements

### 9.1 Determinism Rule

Any platform behavior that materially changes authoritative case state must be deterministic or deterministically constrained according to contract.

### 9.2 Replay Rule

All material program executions and governed state mutations must support replay validation or an equivalent deterministic verification mechanism where specified.

### 9.3 Audit Rule

All material state changes, program executions, approvals, escalations, and governed tool calls must emit auditable records according to Spine rules.

### 9.4 Silent Mutation Prohibition

No layer may silently alter authoritative case state.

### 9.5 Hidden Logic Prohibition

No production behavior that affects case state may depend on hidden, undocumented, or non-contractual logic.

---

## 10. Case Boundary and Isolation Rules

### 10.1 Case Boundary Rule

All agent actions, program actions, data access, and UI context must remain bound to the active case or matter scope unless explicitly authorized by future architecture.

### 10.2 Cross-Case Prohibition

No agent or program may infer, retrieve, mutate, or blend data across cases without an explicit approved design pattern and governance rule.

### 10.3 Isolation Principle

Each case is an isolated governed reasoning domain.

---

## 11. Approval and Escalation Principle

### 11.1 Human Governance Rule

Where legal judgment, strategic significance, or attorney responsibility is implicated, the platform must support escalation and approval rather than silently finalize authoritative output.

### 11.2 Approval Boundaries

Program and agent contracts must define:

* what may be proposed automatically
* what may be persisted automatically
* what requires review
* what requires attorney approval
* what must be blocked pending escalation

### 11.3 Design Implication

The stack architecture must support controlled human-in-the-loop governance without collapsing deterministic program behavior or data integrity.

---

## 12. MVP Stack Definition

The MVP platform is defined as follows.

### 12.1 Spine

* contract manifest
* tool registry
* lanes
* validator
* replay harness
* audit governance

### 12.2 Data Graph

At minimum:

* cases
* documents
* entities
* facts
* events
* relationships
* signals
* patterns
* causes of action
* provenance

### 12.3 Programs

* FACT_NORMALIZATION
* COMPOSITE_ENGINE
* PATTERN_ENGINE
* COA_ENGINE
* COVERAGE_ENGINE

### 12.4 Agents

* INTERVIEW_AGENT
* MAPPING_AGENT
* COA_REASONER

### 12.5 UI

* intake workflow
* mapping review workflow
* evidence graph review surfaces
* coverage and COA review surfaces
* attorney approval interfaces
* audit-aware status displays

---

## 13. Deferred Layer Expansion

The following may be layered after MVP without changing the stack model:

* DISCOVERY_AGENT
* DEPOSITION_AGENT
* TRIAL_PREP_AGENT
* advanced analytics
* cross-matter intelligence
* litigation dashboard expansion
* trial room orchestration
* predictive modules
* specialized evidence scoring modules

All future expansion must conform to this stack architecture.

---

## 14. Implementation Guidance

### 14.1 Recommended Build Posture

Recommended implementation posture:

* **UI shell** may be accelerated using Antigravity or equivalent
* **Agents** should use a bounded reasoning runtime
* **Programs** should be implemented as deterministic services
* **Data Graph** should be implemented in a governed structured database
* **Spine** must remain explicit and enforceable as a first-class platform layer

### 14.2 Anti-Spaghetti Implementation Rule

No implementation team may collapse the following into one indistinct runtime layer:

* agent logic
* deterministic program logic
* authoritative persistence
* governance enforcement
* UI behavior

If these are collapsed, the platform becomes ungovernable and non-defensible.

### 14.3 Build Objective

The objective is to build a platform whose core can be extended safely over time without breaking determinism, auditability, or legal defensibility.

---

## 15. Architectural Maxims

The following maxims govern interpretation of this document:

* **The Spine governs the Brain.**
* **Agents think. Programs compute.**
* **The Data Graph is authoritative memory.**
* **The UI is not the source of truth.**
* **Nothing material may live only in temporary memory.**
* **No silent mutation.**
* **No uncontrolled tool use.**
* **No cross-case leakage.**
* **Determinism where state changes matter.**
* **Auditability is mandatory, not optional.**

---

## 16. Relationship to Other System Documents

This document must be read together with the following future or companion documents:

* `system_REASONING_MODEL.md`
* `system_EVIDENCE_GRAPH.md`
* `system_STATE_MODEL.md`
* program contracts
* agent contracts
* tool registry
* lane governance
* manifest and validator controls

This document defines layer boundaries.
Other documents define behavior within those boundaries.

---

## 17. Open Design Questions

The following items are intentionally deferred to companion architecture documents:

* exact Evidence Graph schema
* exact workflow state machines
* exact program input and output schemas
* exact agent prompt architecture
* exact confidence scoring methodology
* exact approval thresholds by workflow
* exact replay comparison methodology for all execution types

These must be resolved in companion SSOT documents and must not contradict this stack model.

---

## 18. Acceptance Criteria

This document is considered accepted when:

* all platform specifications align to the five-layer stack
* all programs are clearly distinct from agents
* authoritative persistence is assigned to the Data Graph
* governance is explicitly assigned to the Spine
* UI is defined as non-authoritative
* no downstream spec collapses layer responsibilities
* implementation teams can determine where new logic belongs without ambiguity

---

## 19. Final Directive

This platform must be built as a **governed litigation reasoning system**, not as an unstructured AI application.

All future system work must preserve clean separation between:

* governance
* memory
* computation
* reasoning
* presentation

This separation is the primary defense against architectural drift, legal risk, and platform spaghetti.

---

## 20. Summary Statement

The AI Legal Service Platform is a layered system in which:

* the **Spine** governs,
* the **Data Graph** remembers,
* the **Programs** compute,
* the **Agents** reason,
* and the **UI** serves the human.

That is the authoritative stack.

---

This gets you materially closer to the finish line.

The next right move is `system_REASONING_MODEL.md`, because it will define how raw evidence becomes legal intelligence across the stack.

I can draft that next in the same SSOT-ready format.

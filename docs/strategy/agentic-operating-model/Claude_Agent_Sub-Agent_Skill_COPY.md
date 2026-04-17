# Portfolio of Claude Agents for a Legal Service SaaS (Company‑1)

Date: Apr 15, 2026 • Author: M365 Copilot (for Steve Gonsiorowski) 

Scope: Corporate + Company‑level agents, subagents, and skills; orchestration, security (chain‑of‑custody), KPIs, and a 30‑60‑90 build plan. 

Monetization: (1) Salaried by 1–3 firms; (2) per‑case or subscription; (3) case brokerage (fixed fee or % of win).







---

# Portfolio of Claude Agents for a Legal Service SaaS (Company‑1)

Date: Apr 15, 2026 • Author: M365 Copilot (for Steve Gonsiorowski) 

Scope: Corporate + Company‑level agents, subagents, and skills; orchestration, security (chain‑of‑custody), KPIs, and an Activation Framework (agent‑launched design, development & learning). 

Monetization: (1) Salaried by 1–3 firms; (2) per‑case or subscription; (3) case brokerage (fixed fee or % of win).



---



## 0) Executive Summary & Recommended Approach



Strategy: Build with a Hybrid Top‑Down + Bottom‑Up (Anchor‑First) approach.



- Top‑Down (Corporate): Establish shared guardrails and platform services (security, governance, knowledge/retrieval, agentops, skill registry, observability, monetization analytics). 

- Bottom‑Up (Company‑1): Implement end‑to‑end legal workflows—**Intake → Mapping → Opposition → Discovery → Strategy/War‑Room**—plugged into the corporate spine from day one. Extract templates, then scale to Company‑2/3.



Why hybrid? It delivers speed (real value in Company‑1 quickly) and consistency (no fragmentation across companies).



---



## 1) Token Usage & Cost Optimization Strategy



Mission: Ensure platform‑wide cost efficiency and prevent unnecessary token burn across all agents and workflows.



### Rules

- Response budgets: Max 900 tokens per agent reply; 1,800 tokens for multi‑agent plans. 

- RAG limits: Top 3 canonical chunks per query; long documents are summarized at ingestion. 

- Compression modes: GPT Buddy & Research run compressed canonical mode for CAJI/CAEC references. 

- Non‑canonical size: Summaries ≤ 300 tokens; always labeled as non‑canonical leads. 

- Continuation guard: When output > 900 tokens, agents ask: “Continue?” 

- Structured outputs: Favor JSON and concise bullet formats; avoid verbose narrative. 

- Budget enforcement: AgentOps Orchestrator halts tasks exceeding budgets.



### Caching

- CAJI/CAEC lookups: Cache 7 days, invalidate on source updates. 

- Case Snapshot: Maintain a compressed state (**800–1,200 tokens**) for repeated use.



### Summarization

- Pre‑reasoning abstraction: Summarize RAG retrievals before agent reasoning. 

- Variant limit: Opposition narratives capped at 2 variants.



### Logging

- Observability: Track token burn per agent/workflow/company; alert on anomalies.



---



## 2) Case Snapshot Architecture



Mission: Reduce repeated token usage by creating a standardized, compressed representation of the case.



- Size target: 800–1,200 tokens. 

- Contents: Parties, jurisdiction, COAs, top evidence items, risks, discovery status, next actions. 

- Lifecycle: Updated at stage gates; consumed downstream by all agents. 

- Storage: External memory (tenant‑scoped); never re‑generated unless required.



---



## 3) Master Prompt Policy



- Every agent starts with: mission, role, boundaries, token budget, escalation rules. 

- Illegal: Infinite loops; recursive self‑calls; speculative legal conclusions. 

- Citations: Legal assertions must cite canonical CAJI/CAEC/caselaw. 

- Tiering: Product/UX/Dev roles may reference CAJI/CAEC for context only (Tier B). 

- Prompt context fields: `{tenant}`, `{jurisdiction}`, `{caseId}`, `{tokenBudget}` required. 

- Routing: Out‑of‑scope requests must be routed to the proper agent.



---



## 4) Tool Usage Contract



- Necessity rule: Tools invoked only when needed, one call per step unless new data arrives. 

- Hashing discipline: `Custody.hashAndLog` is idempotent; never duplicate on the same item. 

- RAG specificity: Queries include jurisdiction, elements, expected output size. 

- MCP minimalism: Scope calls to minimal fields; avoid broad payloads. 

- Telemetry: Every tool call is logged with cost & latency by Observability.



---



## 5) Canonical Data Compression Rules



Mission: Minimize repetitive CAJI/CAEC output size while preserving legal fidelity.



- Compressed structure includes: 

  - `instructionId` / `section` 

  - `title` (CAJI) / `division/article/section` (CAEC) 

  - essential elements (CAJI) / key admissibility notes (CAEC) 

- No boilerplate: Remove repetitive preambles unless explicitly requested. 

- Element summary format: Use compact element lists for mapping tasks. 

- Do not restate full texts unless asked.



---



## 6) Global RAG Rules



- Grounding: Legal outputs must be retrieval‑grounded in CACI/CALCRIM, CAEC, caselaw. 

- No synthesis without citations: Canonical references are mandatory. 

- Gateway: General agents use RAG via Research/GPT Buddy. 

- Pre‑compression: All retrieved content is compressed before reasoning.



---



## 7) Activation Framework (Agent‑Launched Design, Development & Learning)



Mission: Replace traditional calendar timelines with an always‑on, multi‑agent activation model where design, development, validation, and learning occur continuously and concurrently.



### Core Principles

- Parallelization: Agents operate simultaneously across architecture, design, legal mapping, discovery drafting, testing, and deployment. 

- Instant generation: PRDs, UX flows, code scaffolds, test suites, and legal mappings are produced in minutes using canonical authority (CAJI/CAEC). 

- Continuous learning: Agents refine outputs based on telemetry, user signals, and CI insights. 

- Rapid iteration: Human reviews remain, but cycles compress from weeks to minutes. 

- Agent‑orchestrated workflows: AgentOps Orchestrator schedules and coordinates tasks in real time.



### 7.1 Activation Cycle (Continuous Loop)

1. Ideation/Request → Executive Agent routes to functional agents. 

2. Snapshots & Context Packing → Case Snapshot + compressed CAJI/CAEC. 

3. Multi‑Agent Generation → Product, UX, Architecture, Code, Legal, Research, Discovery/Opposition. 

4. Auto‑Testing & Validation → QA, Lineage, Security, Performance checks. 

5. Integrated Review → Claude Coach & Observability; human approvals. 

6. Deployment → DevOps & Release; Change Management communications. 

7. Continuous Improvement → CI Insights feeds back to Step 1.



### 7.2 Role of Humans (in the loop)

- Attorneys: approve legal outputs. 

- PM/UX: approve user experiences. 

- CTO/Architect: approve structural changes. 

- Release/Comms: approve deployment & messaging.



### 7.3 Governance

- ABAC/RBAC enforced; WORM logging on all agent actions. 

- Skills versioned; updates gated by evaluation. 

- Anti‑token‑burn rules enforced globally. 

- External outputs require attorney approval.



### 7.4 One‑Line Summary

Activation = continuous, multi‑agent execution where design, development, and legal reasoning happen in minutes—not days—under a single governed orchestration loop.



---



## 8) Layered Architecture



### 8.1 Corporate Agents (shared across all companies)



- Portfolio Management Agent — Tracks performance, allocates resources, surfaces ROI across companies. 

- Branding Agent — Enforces brand guides, tone, disclaimers; validates external content. 

- Executive Management Agent — Executive briefs, consolidated statuses, cross‑company initiatives. 

- Investment Management Agent — CAC/LTV, payback, margins; capital allocation. 

- Governance & Risk Agent — Policies: PII, holds, retention, audit trails, chain‑of‑custody. 

- Security & Identity Agent — RBAC/ABAC, tenant isolation, SSO, secrets, consent logging. 

- KnowledgeOps / Retrieval Agent — Multi‑tenant indices, knowledge graph, provenance. 

- AgentOps Orchestrator — Routing/DAGs, retries, rate‑limits, failover; supervisor/worker. 

- Observability & Evaluation Agent — Telemetry (latency, cost, quality), traces, regression evals. 

- Skill Registry Agent — Catalog/version/approve skills & tools; telemetry; deprecations.



### 8.2 Shared Platform Services (“Spine” + “Brain”)



- Spine: Identity (tenants/roles/attributes), WORM audit logs, connectors (docs, CRM, email/calendar, storage, ticketing, analytics), storage, message bus, schedule. 

- Brain: Claude planners/routers/evaluators; strict tool contracts; externalized memory per tenant; retrieval/RAG with ABAC filtering and provenance.



---



## 9) Company‑1 Agents, Subagents, and Skills (Legal Service SaaS)



> Rule of thumb 

> - Agent: persistent goal‑owner with its own backlog/KPIs/authority. 

> - Subagent: specialized worker under an agent for a sub‑domain/step. 

> - Skill: small callable capability (inputs → process → outputs) with tight contracts.



### 9.1 Legal Operations & Case Delivery



Case Guidance Agent (Legal Expert) 

Mission: Drive end‑to‑end case workflow design; jurisdiction & local judicial expertise; encode successful stage gates and narrow workflows.



- Subagents: Jurisdiction Knowledge; Workflow Designer; Instruction/Evidence Mapper 

- Core Skills: `COA.design`, `Burden.analysis`, `Remedy.model`, `InstructionMap.linkEvidence`



Intake Interview Agent (Interview Analyst) 

Mission: Conduct client interviews grounded in Jury Instructions & Evidence Codes; build complaint, COA, burdens, remedies; summarize in legal/plain terms.



- Skills: `Narrative.parse`, `MissingInfo.prompt`, `Complaint.skeleton`, `Summarize.dual`



War‑Room Orchestrator Agent (War‑Room Analyst) 

Mission: Prepare stage gates; synthesize context; run “what‑if” scenarios to strengthen client case.



- Skills: `StageGate.manage`, `Resilience.plan`, `Scenario.whatIf`



### 9.2 Research & Retrieval



Research Agent (Added) 

Mission: Search legal libraries and the internet to find citable information supporting the case; stress the opposition.



- Subagents: Legal Library Search; Web Research; Citation & Provenance Checker 

- Skills: `Legal.RAG.query`, `Web.search`, `Provenance.validate`



GPT Buddy Agent (Added) 

Mission: Grounded in the case; supports GPT‑assisted search; separates canonical vs non‑canonical streams; feeds attorney‑driven research with clear labeling.



- Subagents: Case Context Loader; Canonicalization Pipeline; Non‑Canonical Stream Manager; Synthesis & Contrast 

- Skills: `Context.loadCaseState`, `Canonicalize.sources`, `NonCanonical.label`, `Research.summarizeCompare` 

- Legal authority summary: CAJI + CAEC are the lens; canonical/non‑canonical info is bound by legal authority.



### 9.3 Opposition / Adversarial Analysis



Opposition Simulator Agent (Alternative Scenario Engineer) 

Mission: Stress‑test case; simulate defense narratives, motions, exclusion tactics; flag contradictions & perjury risks (ethically).



- Subagents: Defense Strategy Simulator; Contradiction Finder; Perjury Risk Analyzer 

- Skills: `Defense.motionDrafts`, `Evidence.exclusionTactics`, `Contradiction.detect`, `PerjuryRisk.mitigate`



### 9.4 Discovery



Discovery Agent 

Mission: Generate and manage discovery artifacts; schedule/track responses; manage subpoenas and experts.



- Subagents: Interrogatory/RFA/RFP Generator; Deposition Planner; Subpoena & Expert Ops; Calendar & Deadline Tracker 

- Skills: `Discovery.interrogatories` / `Discovery.RFA` / `Discovery.RFP`, `Deposition.plan`, `Subpoena.draft`, `Expert.match`, `Calendar.sync`



### 9.5 Product & Delivery (Platform)



Product Strategy Agent (PM) — PRDs, roadmap, prioritization. 

Skilled in attorney workflow & CAJI/CAEC (context only; no legal opinions).



Delivery Agent (Project Manager) — Execution, task orchestration, closure; risk mgmt. 

Skilled in attorney workflow & CAJI/CAEC (planning context; no drafting).



Code Assistant Agent (Developers) — UI/middleware/backend scaffolding.



Design System Agent (UX Expert) — Design tokens, components, audits. 

Skilled in attorney workflow & CAJI/CAEC (UX/UI workflows; no legal advice).



QA Automation Agent (Test Engineer) — Unit/regression/integration suites; gates. 

Skilled in attorney workflow & CAJI/CAEC (admissibility constraints; informational only).



Architecture Review Agent (System Architect) — ADRs; scalability/cost/reliability. 

Skilled in attorney workflow & CAJI/CAEC (validate decisions; non‑prescriptive).



DevOps & Release Agent (Deployment Engineer) — Staging/push; health checks; rollbacks.



Change Management Agent (Communication Manager) — User readiness; change impact; No‑Go authority. 

Skilled in attorney workflow & CAJI/CAEC (communications; must not opine on law).



AgentOps Coach (Claude Coach) — E2E quality/process reviews; CTO capability growth.



Repo Hygiene & Structure Agent (Quality Engineer) — Folder/file conventions; dedupe/waste removal.



User Testing Agent (User Testing Engineer) — UT design & execution; reports. 

Skilled in attorney workflow & CAJI/CAEC (realistic usage; informational only).



### 9.6 Security, Performance & Integrations



Security Agent (Security Engineer) — Secure prod/pre‑prod; detect nefarious actions; exposure mgmt. 

Skilled in attorney workflow & CAJI/CAEC (contextual awareness; summary‑only).



Perf & Scalability Agent (Performance Manager) — Perf budgets; load testing; scaling plans.



MCP Integration Agent (MCP Engineer) — Cross‑API tool integrations; LLM usage via MCP.



Insights & Continuous Improvement Agent (CI Engineer) — Usage analysis; improvement validation; PM partnership.



Legal Data & Lineage Agent (Legal Database Expert) — DB for chain‑of‑custody, hashing, Merkle proofs; reproducible connections. 

- Subagents: Chain‑of‑Custody & Hashing; Lineage & Reproducibility Queries 

- Skills: `Custody.hashAndLog`, `Custody.verify`, `Lineage.traceReport`



### 9.7 Brokerage, Billing, Conflicts, Ethics



Brokerage Matching Agent — Scores & matches cases to attorneys; fee terms; conflict checks.



Billing & Monetization Agent — Subscription/per‑case billing; chargeback dashboards (streams #1–#3).



Conflict Check Agent — Attorney/client conflicts; bar status; jurisdiction compliance. 

Skilled as attorney & legal authoritative law; access routed to avoid prescriptive outputs.



Ethics & Compliance Agent — Confidentiality checks, disclaimers, external publishing rules.



### 9.8 Social Media Analyst Agent (OSINT)



Mission: Scour public and consented social media sources to find information on entities and actors (plaintiff, defendant, deponents, related parties). Collect, verify, and inventory posts, profiles, images, videos, and links; preserve metadata; build correlation graphs; and produce admissibility-ready chain-of-custody artifacts.



- Subagents:

  - Platform Collectors (X/Twitter, Facebook, Instagram, LinkedIn, TikTok, Reddit)

  - Link Traversal & Correlation (follow in-platform and cross-platform links)

  - Entity Resolution (handle matching, alias detection, account verification)

  - Media Forensics (EXIF extraction, hash, near-duplicate detection)

  - Geolocation & Temporal Analysis (location inference, time window alignment)

  - Archive & Custody (perma-archival screenshots, URL capture, hashing, WORM logs)



- Skills:

  - `Social.collect(platform)` (API-first collection; fall back to compliant scraping; rate-limit)

  - `Social.scrape.compliant` (respect ToS/robots; no circumvention; public/consented only)

  - `Social.resolveEntities` (match handles to real-world actors; confidence scoring)

  - `Social.linkGraph.build` (build graph of accounts, links, mentions, shared media)

  - `Social.metadata.extract` (URL, postId, author handle, timestamps, EXIF, geo, device hints)

  - `Social.hashAndLog` (SHA-256 of HTML/text/media; Merkle root for bundles; custody event)

  - `Social.archive.capture` (screenshot + raw content capture; archive URI; retrieval info)

  - `Social.geolocate` (geo inference from content/metadata)

  - `Social.credibility.score` (source reputation, recency, consistency, bot-likelihood)

  - `Social.chainReport` (summarize artifacts with provenance and custody chain)

  - `Social.legalHold.tag` (mark artifacts under legal hold; block purge)

  - `Social.redact.sensitive` (blur faces/PII for internal review packets)



- Outputs:

  - Inventory list of social artifacts (platform, URL, author, timestamp, description, hashes)

  - Correlation graph (entities ↔ actors ↔ accounts ↔ posts/media)

  - Credibility scores and risk notes (bot-likelihood, impersonation risk)

  - Chain-of-custody report (hashes, archival screenshots, timestamps, signatures)

  - War-room digest (time-bounded narrative; what-if signal flags)



- Guardrails:

  - Public/consented content only; comply with platform Terms of Service (ToS).

  - No circumvention of technical measures; no false personas; adhere to CFAA and privacy laws.

  - Treat social content as non-canonical: usable as leads or impeachment signals only, not authoritative legal assertions.

  - Authentication required for legal use (subpoena/API export/attestation); attorney approval before filing/publishing.

  - All artifacts hashed (SHA-256), archived, and written to WORM custody logs; ABAC/RBAC enforced.



- Integration:

  - GPT Buddy Agent: ingest as non-canonical stream (labeled), contrasted with canonical CAJI/CAEC.

  - Research Agent: cross-check claims, enrich with public records; attach provenance.

  - Case Guidance/War-Room: consume digests for strategy and actor mapping; no legal opinions.

  - Discovery Agent: use inventory to draft tailored subpoenas, interrogatories, RFAs.



- Access Tier:

  - Operates under Tier B / Summary-only for general platform (context and inventory).

  - Escalates to Tier A only when routed via Discovery/Legal for authentication workflows.



---



## 10) CA Legal Retrieval & Review (CAJI + CAEC)



Mission: Retrieve, interpret, and apply CA Jury Instructions (CAJI: CACI for civil, CALCRIM for criminal) and CA Evidence Code (CAEC) to case facts and evidence. Ensure outputs are canonical, citable, provenance‑tracked; provide context links and admissibility assessments.



- Subagents: CAJI Retrieval; CAEC Retrieval; Citation & Provenance Checker; Contextual Mapper; Case Law Search 

- Skills: 

  - `Legal.CA.CAJI.retrieve` (filter by instructionId/topic/element/keywords) 

  - `Legal.CA.CAEC.retrieve` (filter by division/article/section/keywords; citation + snippet) 

  - `Legal.CaseLaw.searchCA` (court level + date range) 

  - `Review.CaJuryInstruction` (elements; proof requirements) 

  - `Review.CaEvidenceCode` (admissibility: foundation/hearsay/relevance/privilege/authentication) 

  - `Context.CaJuryInstruction` (evidence → elements; coverage; cite) 

  - `Context.CaEvidenceCode` (item admissibility; risks + mitigations; cite) 

  - `Citation.CA.normalize` (standardize citations; Bluebook/California local) 

  - `Canon.CA.validateSource` (verify canonical; reject/label non‑canonical)



- Outputs: Canonical excerpts with citations (CACI/CALCRIM/CAEC) & provenance; element coverage maps; admissibility assessments; next‑question prompts.



- Notes: CACI and CALCRIM are distinct instruction sets under CAJI. Always include `citation`, `sourceType`, `instructionSet (CACI|CALCRIM where applicable)`, and `provenance`. ABAC/RBAC enforced; WORM audit logging. Non‑canonical web results are leads only.



---



## 11) CAJI/CAEC Access Matrix (Corrected Tiers)



Mission: Grant CAJI (CACI/CALCRIM) and CAEC skills to appropriate agents with tiered controls, ensuring canonical citations, provenance, and human approval.



### Tier A — Full Legal Use 

(Retrieve, review/interpret, context map, admissibility assess; attorney approval required for filings/publishing)



- Case Guidance Agent (Legal Expert)

- Research Agent

- GPT Buddy Agent (canonical‑first; non‑canonical labeled; synthesis for attorney review)

- Opposition Simulator Agent (Alternative Scenario Engineer)

- Discovery Agent



> Note: War‑Room Orchestrator is Summary‑Only by default; elevate to Tier A only if you want legally grounded plans with citations.



### Tier B — Summary‑Only 

(Read‑only canonical excerpts/summaries/citations; *no prescriptive legal conclusions**)*



- Product Strategy Agent (PM)

- Delivery Agent (Project Manager)

- Design System Agent (UX Expert)

- Code Assistant Agent (Developers)

- QA Automation Agent (Test Engineer)

- Architecture Review Agent (System Architect)

- DevOps & Release Agent (Deployment Engineer)

- Change Management Agent (Communication Manager; No‑Go authority)

- AgentOps Coach (Claude Coach)

- Repo Hygiene & Structure Agent (Quality Engineer)

- User Testing Agent (User Testing Engineer)

- Security Agent (Security Engineer)

- Perf & Scalability Agent (Performance Manager)

- MCP Integration Agent (MCP Engineer)

- Insights & Continuous Improvement Agent (CI Engineer)

- Legal Data & Lineage Agent (Legal Database Expert)

- War‑Room Orchestrator Agent (War‑Room Analyst)



### Tier C — Routed Access 

(Do not call CAJI/CAEC directly; route via *Research Agent / GPT Buddy** to receive labeled canonical vs non‑canonical results)*



- Intake Interview Agent (Interview Analyst)

- Brokerage Matching Agent

- Billing & Monetization Agent

- Conflict Check Agent

- Ethics & Compliance Agent



Guardrails: Canonical‑only legal assertions; citation + provenance required. ABAC/RBAC enforced; least‑privilege scopes; WORM logs on calls. Non‑canonical sources labeled “leads only”; never for filings. Human attorney approval required for any filing/publishing or prescriptive legal conclusions.



Operations: Skills versioned; upgrades via feature flags & canary evals. Caching/routing through Research Agent. Evaluation gates: citation validity, coverage accuracy, latency/cost budgets.



RACI: R = Legal agents; A = Attorney of record; C = Product/UX/Architecture/Dev; I = Security/Observability.



---



## 12) Orchestration Patterns



- Supervisor–Worker: Executive Agent plans; function agents execute; executive aggregates. 

- Router/Dispatcher: Intent classification routes to specialized agent/skill. 

- DAG Pipelines: Deterministic sequences (Intake → Mapping → Opposition → Discovery → War‑Room). 

- Human‑in‑the‑Loop: Mandatory review before filings, external publishing, or financial actions.



---



## 13) Security & Chain‑of‑Custody (Critical Requirements)



- SHA‑256 Hashing: Every raw file → hash; large files → chunk hashing + per‑chunk hash. 

- Merkle Trees: Bundle multiple items → Merkle root representing the set (proofs). 

- Immutable WORM Logs: Append custody events (ingest, transfer, access, transform) with `previousHash` and `blockHash`; signed entries. 

- ABAC Retrieval: All queries filtered by tenant, role, sensitivity, legal hold tags. 

- Legal Holds & Retention: Governance agent applies holds; prevents purge; retention schedules enforced.



### 13.1 Custody Event (JSON)

```json

{

  "eventId": "evt_2026-04-15T17:22:11Z_001",

  "caseId": "CASE-123",

  "itemId": "EVID-456",

  "action": "ingest",

  "sha256": "f8b1...9c",

  "mime": "application/pdf",

  "sizeBytes": 482191,

  "timestamp": "2026-04-15T17:22:11Z",

  "actor": "intake@company-1",

  "previousHash": "0000...000",

  "blockHash": "7a13...af",

  "signature": "ed25519:SIG...",

  "tags": ["tenant:company-1","sensitivity:high","legalHold:false"]

}



Hashing & Merkle (psuedocode)

# file-level hash

sha256_hex = sha256(file_bytes).hexdigest()



# chunked hashing for large files

CHUNK = 4  1024  1024  # 4MB

chunks = [file_bytes[i:i+CHUNK] for i in range(0, len(file_bytes), CHUNK)]

leaf_hashes = [sha256(c).digest() for c in chunks]



# merkle tree build

nodes = leaf_hashes[:] if leaf_hashes else [sha256(file_bytes).digest()]

while len(nodes) > 1:

    paired = []

    for i in range(0, len(nodes), 2):

        left = nodes[i]

        right = nodes[i+1] if i+1 < len(nodes) else left  # duplicate last if odd

        paired.append(sha256(left + right).digest())

    nodes = paired

merkle_root = nodes[0].hex()
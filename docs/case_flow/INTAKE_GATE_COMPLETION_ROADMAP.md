# INTAKE STAGE GATE — COMPLETION ROADMAP

## Stage Gate Alignment
**Primary Stage Gate:** INTAKE

## Definition of "complete" (authoritative — user-defined 2026-06-12)
The INTAKE gate is complete when these six capabilities are **fully operational**, **usable through the UI**, and provide **source-document traceability** for legally authoritative + evidential files:
**legal library · gpt & research · interview · file upload · actors · triangulation.**
**Proof:** upload **T1100** through the UI and complete an interview intake with **a recorded session AND a textual file**, with every derived item traceable to its source.

> Supersedes the narrow Wave-1 data-layer "complete." Per-output status is **observed-by-code-read**, not yet verified by running the app.

## Foundational finding — two disconnected stacks
- **Running product:** legacy `production/backend/models.py` + routes + `production/frontend` (React/Vite) — wired to FastAPI + UI.
- **Wave 1/2 `core_models.py`** (intake_service, recordings, transcripts, message-normalization) — **not wired to the app**; schema+services+tests only.
- **Decision required (Phase 0):** wire `core_models` into the app, OR extend the legacy models, OR migrate legacy → core. This threads through every capability below.

---

## Per-output roadmap

Legend — **DoD** = definition of done (operational + UI + traceability) · status: ✅ MEETS · 🟡 PARTIAL · ⛔ ABSENT

### O1 — File upload  🟡→✅ (closest)
- **DoD:** upload via UI; persisted with hash/dedup/versioning; uploaded file is the traceability anchor for derived items.
- **Accomplished:** `UploadPanel.jsx` (drag-drop, SHA256, dedup, retry, zip); backend `/documents/upload` (+zip, ingest trigger, hash-addressed storage).
- **Next:** verify by running; confirm the uploaded-file → EvidenceReference anchor is populated for T1100.
- **Effort:** ~0.5 session (verification).

### O2 — Actors  🟡→✅
- **DoD:** extract/add/edit/merge actors in UI; each actor traceable to source mentions.
- **Accomplished:** `ActorsList.jsx` full CRUD+merge; backend extraction, dedup, `ActorMention` (doc/interview + offset + snippet).
- **Next:** verify by running; confirm mention → source-doc drill-down surfaces in UI (currently mention_count shown, no click-through).
- **Effort:** ~0.5–1 session (verify + add mention drill-down).

### O3 — Legal library  🟡
- **DoD:** browse/search authority in UI; each cited authority traceable to its canonical source with provenance.
- **Accomplished:** `LegalLibrary.jsx` browse/search/view; backend corpus + routes; provenance schema (`AUTHORITY_PACK_FORMAT`, manifest) specified.
- **Next:** load real canonical authority data with live provenance (currently spec-only/gated); wire authoritative-source traceability (authority → source_url/hash) into the UI.
- **Effort:** ~1–2 sessions (more if canonical packs must go through the promotion gate).

### O4 — Interview (recorded + textual)  🟡
- **DoD:** UI conducts interview with **both** a recorded audio session and textual responses; recording + transcript persisted and traceable.
- **Accomplished:** text Q&A + narrative operational (legacy `Interview` + routes); audio-capture UI exists (MediaRecorder/Web Speech) but dumps audio as a generic file upload; `InterviewRecording`/`InterviewTranscriptSegment` schema exists in `core_models` (unwired).
- **Next:** backend routes for audio upload + transcript (wire `core_models` or legacy); connect UI recorder to them; decide transcription approach (browser STT vs server STT); traceability from interview-derived items → recording/transcript segment.
- **Effort:** ~2–3 sessions.

### O5 — Triangulation  🟡→⛔
- **DoD:** cross-reference actors/facts/sources across documents in UI; conflicts/ambiguity preserved and explorable.
- **Accomplished:** Wave 2 message-normalization models fully designed (`ReferencedActorCandidate`, threads, statements, quality flags) but **orphaned (no routes)**; one-way `EvidenceReference` backfill only; no cross-ref UI.
- **Next:** wire normalization service to routes / build correlation logic (actor↔facts↔sources, conflict markers); build triangulation UI (drill-down + conflict view).
- **Effort:** ~3–5 sessions.

### O6 — GPT & research  ⛔ (heaviest, net-new)
- **DoD:** AI-assisted research usable in UI (reason over library + case + external), grounded with citations/traceability.
- **Accomplished:** none — no LLM anywhere (no anthropic/openai); all analysis is rule-based heuristics.
- **Next:** integrate Anthropic SDK (with prompt caching per the claude-api skill); design grounded-research flow + citations; build research UI; wire traceability of AI claims → sources. Requires an API key + provider decision.
- **Effort:** ~4–6 sessions (high uncertainty).

### X1 — Source-document traceability (cross-cutting)
- **DoD:** any derived item (fact/actor/claim/event) links to its exact source document; single-call fact→source; "click-through" in UI; covers authoritative + evidential files.
- **Accomplished:** schema columns + `EvidenceReference` (backfill from ActorMention); authority provenance specified.
- **Next:** wire traceability into the extraction pipeline (not just backfill); single-call fact→source endpoint; UI click-through; unify evidential + authoritative provenance.
- **Effort:** ~2–3 sessions (foundational; do early).

### X2 — Proof harness & E2E
- **DoD:** repeatable run of the exact proof: upload **T1100** via UI + recorded + textual interview; every derived item traces to source; gate marked COMPLETE.
- **Accomplished:** none (T1100 is external to repo; not yet run end-to-end).
- **Next:** stand up app; scripted/observed E2E; obtain T1100 from user; fix breakages; sign off.
- **Effort:** ~1–2 sessions (plus recurring verification).

---

## Sequencing (phases)
- **Phase 0 — Foundation (1–2):** run the app; verify O1/O2; make the two-stack decision; scaffold X2 proof harness.
- **Phase 1 — Traceability backbone (X1) (2–3):** required by every capability.
- **Phase 2 — Interview recorded+textual (O4) (2–3).**
- **Phase 3 — Legal library provenance (O3) (1–2).**
- **Phase 4 — Triangulation (O5) (3–5).**
- **Phase 5 — GPT & research (O6) (4–6).**
- **Phase 6 — Proof & harden (X2 + O1/O2 finalize) (1–2).**

## Total estimate
**~15–22 focused prompt sessions**, grouped in the 6 phases above. At ~1–2 sessions/day → roughly **2–4 weeks** of active work. Highest-uncertainty items: GPT/research (O6) and triangulation (O5).

## Estimate depends on (decisions / external inputs)
1. Two-stack reconciliation decision (wire core_models vs extend legacy vs migrate).
2. LLM provider + API key (blocks O6).
3. Transcription approach for recorded sessions (browser vs server STT).
4. Availability of real canonical authority data (affects O3 provenance).
5. The **T1100** file (needed for the proof).

## Progress log
- 2026-06-12: roadmap created from 3-agent codebase assessment. Nothing built against this definition yet; Wave-1 data layer + seed tests done but unwired to app.

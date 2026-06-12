# SESSION CARRYOVER — read this first, then continue

Single-file handoff so a fresh session starts with **only** the needed context.
Authoritative detail lives in `docs/case_flow/INTAKE_GATE_COMPLETION_ROADMAP.md`
and the memory files. Don't re-explore the whole repo — work from the set below.

## Goal
Complete the **INTAKE stage gate** to the user's definition: six capabilities
**operational + usable in the UI + source-traceable** — legal library, gpt &
research, interview, file upload, actors, triangulation — proven by uploading
**T1100** in the UI and a **recorded + textual** interview.

## Where we are (done)
Backend boots; extraction pipeline handles **all T1100 media** — text/pdf (pypdf),
images (Claude-vision OCR), audio/video (Whisper + ffmpeg) — all **deduped**
(content-addressed, never reprocess a duplicate) and **source-traceable**
(fact→doc + text_span). LLM layer live (`/llm/status` = configured). Keys in
`.env`. Security incident resolved (no keys in repo; Stage 16 secret guard).
PRs #6–#17 merged. trunk = `main`.

## Next (pick up here, roadmap newest-first)
1. **Full T1100 ingest + dedup validation** — process T1100, then T3800 (overlaps);
   report unique-processed vs duplicates-skipped counts. Bulk; costs API $.
2. Claude-quality actor extraction (replace noisy rule-based; kills "Hey Jeremey").
3. RAG / authoritative research (O6) — embed the 1,689-record legal library
   (OpenAI embeddings), retrieve, Claude answers **with citations**; vector store
   = pgvector (prod) / local (dev). 4. Triangulation logic + UI. 5. Interview
   recorded-session wiring. 6. Frontend UI verification.

## RULES (bind me AND any sub-agents)
- **One trunk `main`; one change = one branch → PR → squash-merge → delete branch.** No direct commits to main. No long-lived branches. No orphan worktrees.
- **Build for correctness, scalability, NO fragility, resilience.** Degrade gracefully (e.g. missing key/ffmpeg/storage → clear status, never crash).
- **Verify by running, don't assume** — the static code-read was optimistic and missed 3 boot/IO bugs. Prove each change against real T1100 data.
- **Never reprocess duplicates** (content-addressed dedup is in `ingest_pipeline`).
- **Secrets:** never in chat, never committed; keys only in gitignored `.env`. Stage 16 pre-commit guard blocks key commits.
- **Cost discipline:** default model tiers **Haiku/Sonnet, not Opus**; dedup; **sample 3–5 files before any bulk run**; platform API billing is the Anthropic *Console* account, SEPARATE from the Claude.ai $250 subscription that funds dev sessions.
- `casecore-runtime/production/` is gitignored → **force-add** (`git add -f`) backend files. Pre-commit hook `validate_contract.ps1` must pass (Stage 15 worktree guard, Stage 16 secret guard).
- Two-stack decision: converge on contract-aligned **`core_models`** as canonical via strangler-fig; keep the app green at every step.

## WORKING SET (don't wander outside without reason)
- Backend root: `casecore-runtime/production/backend/`
  - `main.py` (app + lifespan + `/llm/status`; loads `.env`)
  - `models.py` (legacy, wired) · `core_models.py` (contract-aligned, canonical target)
  - `database.py` · `routes/{documents,actors,interviews,legal_library,analysis,cases}.py`
  - `brain/{content_extractors,ingest_pipeline,evidence_service,actor_extractor,legal_library}.py`
  - `llm/{config,providers}.py` (Claude+OpenAI abstraction) · `.env` (keys, gitignored)
  - `services/intake_service.py` · `tests/`
- Frontend (UI work): `casecore-runtime/production/frontend/` (Vite/React)
- Docs/rules: `docs/case_flow/INTAKE_GATE_COMPLETION_ROADMAP.md`, `contract/v1/doctrine/NO_DRIFT_WORKING_AGREEMENT.md`, root `CLAUDE.md`
- Evidence: `C:\Users\sfgon\Documents\Archive\.All_Source_Files\T1100` (real, ~31GB mixed media)

## RUN / VALIDATE
- venv: `casecore-runtime/production/backend/.venv` (has fastapi, sqlalchemy, anthropic, openai, pypdf, python-docx, python-dotenv).
- Start backend (F:\ evidence drive is usually unmounted → storage auto-falls-back to local):
  `cd backend && CASECORE_STORAGE_PATH="$(pwd)/storage_local" ./.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`
- Kill a stuck server: PowerShell `Get-NetTCPConnection -LocalPort 8000 ... | Stop-Process`.
- Confirm keys: `GET /llm/status`. Quick AV/OCR tests: standalone python that `load_dotenv(.env, override=True)`; **print ascii-safe** (`.encode('ascii','replace')`) — Windows console is cp1252.
- ffmpeg is installed (WinGet). Whisper limit 25MB → code extracts/chunks audio.

## COST POSTURE for this session
User is cost-sensitive (Claude.ai subscription ~50% used, refresh Jul 1). Prefer
Sonnet for build work; keep turns focused; bank PRs frequently; sample before bulk.

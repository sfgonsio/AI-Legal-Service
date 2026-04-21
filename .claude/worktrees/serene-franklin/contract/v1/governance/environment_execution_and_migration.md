# Governed Runtime Execution & Migration Strategy
## CaseCore Platform - Architecture & Deployment

---

## 1. OVERVIEW

CaseCore operates as **one codebase with three governed runtimes**, each with distinct capabilities, database targets, and operational restrictions.

| Aspect | Sandbox | Demo | Live |
|---|---|---|---|
| **Use Case** | Local dev, QA, feature testing | Client demos, investor presentations | Production, real cases |
| **Database** | `casecore_sandbox.db` (SQLite) | `casecore_demo.db` (SQLite) | Production PostgreSQL |
| **Can Demo Login?** | ✓ Yes | ✓ Yes | ✗ No (403) |
| **Can Reset?** | ✓ Yes | ✓ Yes | ✗ No (403) |
| **Can Seed?** | ✓ Yes | ✓ Yes (DemoBaseline only) | ✗ No (403) |
| **Demo on Startup?** | ✗ Manual only | ✓ Yes (first run) | ✗ Never |
| **Data Durability** | Ephemeral | Ephemeral | **Permanent** |

---

## 2. RUNTIME CONFIGURATION

### Environment Variable: `CASECORE_RUNTIME`

```bash
export CASECORE_RUNTIME=sandbox   # Local development
export CASECORE_RUNTIME=demo      # Staging/demos
export CASECORE_RUNTIME=live      # Production
```

**Failure Mode:** If `CASECORE_RUNTIME` is not set or invalid:
- Backend: Server refuses to start (RuntimeError on startup)
- Frontend: Assumes safest option (live-like restrictions)

### Runtime Identity

Initialized at application startup via `initialize_runtime_config()` in `main.py`:

```python
# backend/main.py lifespan hook
runtime_config = initialize_runtime_config()
print(f"[CaseCore] Runtime: {runtime_config.name.value}")
```

Exposed to frontend via `/api/runtime/config` endpoint:

```javascript
// frontend
const config = await fetchRuntimeConfig()
// { runtime: "demo", capabilities: {...}, environment: "development" }
```

---

## 3. CAPABILITY MATRIX

All runtime permissions controlled by `RuntimeCapabilities` in `runtime_config.py`:

```python
RuntimeCapabilities.CAPABILITIES = {
    "sandbox": {
        "can_seed": True,
        "can_reset": True,
        "can_load_scenario": True,
        "can_demo_login": True,
        "seed_on_startup": False,  # Manual only
    },
    "demo": {
        "can_seed": True,           # Locked to DemoBaseline
        "can_reset": True,
        "can_load_scenario": False,  # Future
        "can_demo_login": True,
        "seed_on_startup": True,  # DemoBaseline on first run
    },
    "live": {
        "can_seed": False,
        "can_reset": False,
        "can_load_scenario": False,
        "can_demo_login": False,
        "seed_on_startup": False,
    },
}
```

**Frontend Visibility:**
- Fetched at app startup via `/api/runtime/config`
- Controls visibility of reset buttons, demo login button, scenario controls
- RuntimeBanner component shows current runtime status

---

## 4. DATABASE ISOLATION

### Runtime-Specific Database Targets

In `backend/database.py`:

```python
DB_TARGETS = {
    "sandbox": "sqlite+aiosqlite:///./casecore_sandbox.db",
    "demo":    "sqlite+aiosqlite:///./casecore_demo.db",
    "live":    os.getenv("DATABASE_URL"),  # Production PostgreSQL
}

DATABASE_URL = os.getenv("DATABASE_URL") or DB_TARGETS[CASECORE_RUNTIME]
```

**Key Protection:** Each runtime connects to its own database.
- Sandbox reset cannot affect demo data
- Demo reset cannot affect live data
- Accidental `CASECORE_RUNTIME=demo` does not expose production data

### Database Initialization

Schema creation and migrations are **separate from seeding**:

```bash
# Schema only (idempotent)
python scripts/init_runtime.py
alembic upgrade head

# Seeding (on-demand, non-idempotent)
POST /api/scenario/load { "name": "mills_v_polley" }
POST /api/scenario/reset
```

---

## 5. AUTHENTICATION & DEMO SHORTCUTS

### Forced Login in All Runtimes

**Governance Requirement:** PasswordGate (session-level) + Login (user-level) are REQUIRED in sandbox, demo, and live.

```jsx
// App.jsx
return (
  <PasswordGate>              {/* ← ENFORCED: All runtimes must pass */}
    <Routes>
      <Route path="/login" element={<Login />} />  {/* ← ENFORCED: All runtimes */}
      ...
    </Routes>
  </PasswordGate>
)
```

**Demo Login is NOT an auth bypass.** It is a convenience shortcut that:
- Still requires PasswordGate session entry
- Still stores authentication tokens in localStorage
- Still respects logout and session expiration
- Is only allowed in sandbox/demo, rejected in live

### Backend Auth Guards

`routes/auth.py` checks runtime before accepting demo accounts:

```python
@router.post("/api/auth/login")
async def login(data: LoginRequest):
    runtime = get_runtime_config()
    user = DEMO_USERS.get(data.email.lower())
    
    if user and runtime.name == "live":
        # Live: reject demo accounts
        raise HTTPException(status_code=401, detail="Demo accounts disabled in live")
    
    # Sandbox/demo: allow demo accounts
    ...
```

### Frontend Auth Guards

`useAuth.jsx` prevents demo login in live:

```javascript
const demoLogin = async () => {
  const config = await fetchRuntimeConfig()
  if (config.runtime === 'live') {
    return { ok: false, error: 'Demo login disabled in live' }
  }
  // ... demo login proceeds in sandbox/demo
}
```

### PasswordGate (Unchanged)

Session-level password entry (shows BEFORE login):
- Applied equally across all runtimes
- Enforced in `components/PasswordGate.jsx`
- VITE_APP_PASSWORD from environment variables

---

## 5.5 Storage Isolation (NEW)

All file operations must respect runtime isolation:

```python
# In backend/storage.py
BASE_PATHS = {
    RuntimeName.SANDBOX: "./storage/sandbox",
    RuntimeName.DEMO: "./storage/demo",
    RuntimeName.LIVE: "/data/live",  # Production path, outside repo
}

# All operations use StorageConfig
storage = get_storage_config()
path = storage.get_document_path(case_id, doc_id, filename)
```

**Live Protection:**
- Document deletion: raises `PermissionError` in live
- Case folder deletion: raises `PermissionError` in live
- Storage clear: raises `PermissionError` in live
- Sandbox/demo: all operations allowed

---

## 6. ENDPOINT GUARDS & SCENARIO MANAGEMENT

### RuntimeGuard Decorator

All destructive endpoints protected by `@RuntimeGuard`:

```python
@router.post("/api/scenario/reset")
@RuntimeGuard(allowed_runtimes=["sandbox", "demo"], operation="reset")
async def reset_scenario(db: AsyncSession = Depends(get_db)):
    """Reset to DemoBaseline. Forbidden in live."""
    result = await ScenarioLoader.reset_to_baseline(db)
    return { "status": "reset", "loaded": result }
```

**Live Protection:** If `CASECORE_RUNTIME=live`:
```
POST /api/scenario/reset
→ 403 Forbidden: "reset is not allowed in live runtime"
```

### Scenario System

**ScenarioPackage:** Named bundle of seed data
- `DemoBaseline`: Default demo scenario (Mills v. Polley case)
- Future: Customer scenarios, test scenarios

**ScenarioLoader:** Service to load/reset scenarios
- `load_scenario(name)`: Load any available scenario
- `reset_to_baseline()`: Clear all data and reload DemoBaseline
- `list_available()`: Show available scenarios

**API Endpoints:**
```
GET  /api/scenario/available     → List scenario names
POST /api/scenario/load          → Load scenario { "name": "..." }
POST /api/scenario/reset         → Reset to DemoBaseline
GET  /api/scenario/status        → Count cases, docs, COAs, burdens
```

---

## 7. MIGRATION FLOW

### Schema Evolution (Migrations)

**Tool:** Alembic (SQLAlchemy migrations)

**Pattern:** Idempotent, append-only, tracked in version control

```bash
# Apply all pending migrations
alembic upgrade head

# Create new migration (for development)
alembic revision --autogenerate -m "Add new table"
```

**Behavior:** Same migration applied to all runtimes (sandbox, demo, live)

### Scenario Evolution (Seeding)

**Tool:** ScenarioLoader service

**Pattern:** Non-idempotent (deletes old data), on-demand, environment-controlled

```bash
# Manual seed (development)
POST /api/scenario/load { "name": "mills_v_polley" }

# Auto-seed on startup (demo only)
# controlled by: runtime.can("seed_on_startup")
```

**Behavior:** Only runs in sandbox/demo; forbidden in live

---

## 8. LIVE PROTECTION LAYERS

### Layer 1: Environment Variable Gate
- `CASECORE_RUNTIME` must equal "live"
- If missing/invalid: server refuses to start (fail-safe)

### Layer 2: Database Isolation
- Live connects to production PostgreSQL (DATABASE_URL)
- Sandbox/demo connect to local SQLite
- No shared database; reset in demo cannot affect live

### Layer 3: Endpoint Guards
- Reset/seed endpoints return 403 Forbidden in live
- RuntimeGuard decorator enforces per-endpoint
- All violations logged with runtime context

### Layer 4: Auth Rejection
- Demo accounts (attorney@, paralegal@, viewer@) rejected in live
- Fallback attorney session not created in live
- Only real user credentials accepted

### Layer 5: Frontend Controls
- RuntimeBanner shows "🔴 LIVE" in red
- Demo login button hidden or returns error in live
- Reset/scenario buttons hidden in live

### Layer 6: Startup Behavior
- Seeding disabled in live (even if seed_on_startup=true)
- Schema-only initialization; no data mutations
- Migrations applied, but seeding refused

---

## 9. ROLLOUT STRATEGY

### Phase 1: Sandbox (Local Development)

**Setup:**
```bash
export CASECORE_RUNTIME=sandbox
python scripts/init_runtime.py
npm run dev  # Frontend
python -m uvicorn main:app  # Backend
```

**Verification:**
- [ ] `GET /api/runtime/config` returns `{ runtime: "sandbox", ... }`
- [ ] Demo login button works
- [ ] Reset button works
- [ ] RuntimeBanner shows "🔒 SANDBOX"
- [ ] Dashboard loads with seeded data (or empty if manual seed)

**Data:** SQLite at `casecore_sandbox.db`

### Phase 2: Demo (Staging/Presentations)

**Setup:**
```bash
export CASECORE_RUNTIME=demo
python scripts/init_runtime.py
# Database auto-seeds on first run if empty
npm run build && npm run preview
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Verification:**
- [ ] `GET /api/runtime/config` returns `{ runtime: "demo", ... }`
- [ ] Demo data (Mills v. Polley) loads automatically
- [ ] Demo login button works
- [ ] Reset button works (clears and reseeds)
- [ ] RuntimeBanner shows "🎭 DEMO"

**Data:** SQLite at `casecore_demo.db` (can be safely deleted and recreated)

### Phase 3: Live (Production)

**Pre-Deployment Checklist:**
- [ ] `CASECORE_RUNTIME=live` set in production environment
- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] Schema migration run: `alembic upgrade head`
- [ ] Real client data imported (if applicable)
- [ ] All API keys, secrets configured
- [ ] PasswordGate enabled with secure password
- [ ] SSL/TLS enforced (HTTPS only)
- [ ] Backup strategy verified (daily snapshots)

**Deployment:**
```bash
export CASECORE_RUNTIME=live
export DATABASE_URL=postgresql://...  # Production DB
export VITE_APP_PASSWORD=<secure_password>

# Schema only (migrations already applied)
alembic upgrade head

# No seeding, no reset endpoint access
npm run build
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Verification:**
- [ ] `GET /api/runtime/config` returns `{ runtime: "live", ... }`
- [ ] RuntimeBanner shows "🔴 LIVE"
- [ ] `POST /api/scenario/reset` returns 403 Forbidden
- [ ] Demo login button hidden or returns error
- [ ] Standard auth required (no demo shortcuts)
- [ ] All operations logged with runtime context
- [ ] Real client cases visible

---

## 10. OPERATIONAL RUNBOOKS

### Running Sandbox Locally

```bash
cd casecore-runtime/apps/api

# Terminal 1: Backend
export CASECORE_RUNTIME=sandbox
python -m uvicorn casecore.backend.main:app --reload

# Terminal 2: Frontend
cd casecore/frontend
npm run dev  # Vite proxy will forward /api to localhost:8000
```

### Resetting Demo Data

```bash
curl -X POST http://localhost:8000/api/scenario/reset \
  -H "Content-Type: application/json"
# Response: { "status": "reset", "scenario": "mills_v_polley", "loaded": {...} }
```

### Loading a Different Scenario

```bash
curl -X POST http://localhost:8000/api/scenario/load \
  -H "Content-Type: application/json" \
  -d '{"name": "mills_v_polley"}'
```

### Checking Runtime Status

```bash
# Frontend
const config = await fetchRuntimeConfig()
console.log(config.runtime)  // "sandbox", "demo", or "live"

# Backend
GET /api/runtime/config
GET /api/runtime/health
GET /api/scenario/status
```

### Disaster Recovery (Live Only)

If production data corruption occurs:

1. **Backup Restore:** Use database backup service (Supabase, Render)
   ```bash
   # Never use /api/scenario/reset or DELETE operations
   # Use your cloud provider's point-in-time recovery
   ```

2. **App Restart:** No special handling needed
   - Live runtime cannot reset itself
   - All API calls will fail gracefully if data is corrupted
   - Manual database restore is the only path forward

3. **Logging:** All attempts to reset/seed are logged
   ```
   [RuntimeGuard] reset blocked in live (allowed: sandbox, demo)
   ```

---

## 11. SCHEMA MIGRATIONS

### Adding a New Table

```bash
cd casecore-runtime/apps/api

# 1. Define model in models.py
class NewModel(Base):
    __tablename__ = "new_models"
    ...

# 2. Create migration
alembic revision --autogenerate -m "Add new_models table"

# 3. Review migration
cat alembic/versions/xxx_add_new_models_table.py

# 4. Apply to local sandbox
export CASECORE_RUNTIME=sandbox
alembic upgrade head

# 5. Test with demo data
curl -X POST http://localhost:8000/api/scenario/reset

# 6. Commit migration to Git
git add alembic/versions/
git commit -m "Migration: add new_models table"

# 7. Deploy to live
# (Deployment process applies: alembic upgrade head)
```

### Adding a New Column

Use the safe migration pattern in `database.py`:

```python
_MIGRATIONS = [
    ("table_name", "column_name", "VARCHAR DEFAULT 'value'"),
]

async def upgrade_db():
    """Safely add columns via ALTER TABLE (one per connection)"""
    for table, column, col_type in _MIGRATIONS:
        try:
            async with engine.begin() as conn:
                await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except Exception:
            pass  # Column already exists
```

---

## 12. TROUBLESHOOTING

### "CASECORE_RUNTIME not set" Error

```
RuntimeError: CASECORE_RUNTIME must be set to sandbox, demo, or live
```

**Fix:**
```bash
export CASECORE_RUNTIME=demo
python -m uvicorn main:app
```

### "Reset is not allowed in live" Error

```
403 Forbidden: reset is not allowed in live runtime
```

**Expected behavior:** This is correct. Live runtime cannot be reset.

**If you need to fix production data:**
1. Use your cloud database provider's backup/restore service
2. Never try to bypass this protection

### Database "sqlite: database is locked" Error

```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes writing to same SQLite database

**Fix (local development):**
```bash
# Kill existing processes
pkill -f "python.*main:app"
pkill -f "npm.*dev"

# Restart
export CASECORE_RUNTIME=sandbox
python -m uvicorn main:app
```

**Fix (demo/sandbox):**
```bash
# Delete and recreate
rm casecore_sandbox.db
python scripts/init_runtime.py
curl -X POST http://localhost:8000/api/scenario/reset
```

### Runtime Config Not Exposing to Frontend

```javascript
const config = await fetchRuntimeConfig()
// Returns default/fallback instead of real config
```

**Fix:**
1. Ensure `/api/runtime/config` endpoint is accessible
2. Check CORS middleware in main.py (allow all by default)
3. Check browser console for fetch errors

```bash
curl http://localhost:8000/api/runtime/config
```

---

## 13. FUTURE ENHANCEMENTS

- [ ] **Multi-tenant:** Extend scenario system for customer-specific scenarios
- [ ] **Audit Logging:** Centralized log of all reset/seed operations per runtime
- [ ] **Automated Backups:** S3 snapshots of sandbox/demo databases
- [ ] **A/B Testing:** Load different scenarios for A/B feature testing
- [ ] **Data Synthesis:** Auto-generate test cases and scenarios
- [ ] **Runtime Switching:** Allow development to switch runtimes without restart (unlikely; keep current design)

---

## 14. SUMMARY

| Aspect | Implementation |
|---|---|
| **Governance** | CASECORE_RUNTIME env var (sandbox\|demo\|live) |
| **Capability Map** | RuntimeCapabilities class; runtime-specific booleans |
| **Database Isolation** | Runtime-specific connection strings; no shared DB |
| **Live Protection** | 6-layer defense: env var, DB, endpoints, auth, frontend, startup |
| **Auth Continuity** | PasswordGate unchanged; demo login guarded by runtime |
| **Migration** | Alembic; applied to all runtimes identically |
| **Seeding** | ScenarioLoader; on-demand, forbidden in live |
| **Dashboard** | RuntimeBanner shows current runtime; drives UI capability visibility |
| **Rollout Order** | Sandbox (dev) → Demo (staging) → Live (prod) |
| **Failure Mode** | Server refuses to start if CASECORE_RUNTIME invalid |

---

**End of Document**

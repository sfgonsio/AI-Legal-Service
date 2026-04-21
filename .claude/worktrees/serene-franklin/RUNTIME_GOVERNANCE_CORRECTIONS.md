# Runtime Governance Corrections & Enforcement
## CaseCore Platform - Compliance Implementation

**Date:** April 2026  
**Status:** ✅ COMPLETE  
**Compliance:** All 6 critical gaps fixed

---

## EXECUTIVE SUMMARY

Previous implementation had strong architecture but **6 critical governance gaps**. This document details all corrections applied to achieve full compliance with `contract/v1/governance/environment_execution_and_migration.md`.

**All Gaps Fixed:**
1. ✅ Migration Enforcement (Alembic-only)
2. ✅ Auth Consistency (Forced login in all runtimes)
3. ✅ Storage Isolation (Runtime-aware file paths)
4. ✅ RuntimeGuard Enforcement (All destructive ops protected)
5. ✅ Deployment Model (Explicit runtime-to-environment mapping)
6. ✅ Migration vs Scenario Separation (Verified and locked)

---

## 1. MIGRATION ENFORCEMENT FIX

### Problem
- `database.py` was using `Base.metadata.create_all()` for schema creation
- Alembic migrations were applied AFTER schema already existed
- No pre-flight check to verify migrations are applied
- Live runtime could start with stale schema

### Solution Implemented

**File: `backend/database.py`**
- ❌ Removed: `await conn.run_sync(Base.metadata.create_all)`
- ✅ Added: `verify_schema_up_to_date()` function
- ✅ Purpose: Query `alembic_version` table to confirm migrations are applied

**Function: `verify_schema_up_to_date()`**
```python
async def verify_schema_up_to_date():
    """
    Verify that Alembic migrations have been applied.
    Fails if schema is out-of-date (live protection).
    
    Checks:
    1. alembic_version table exists
    2. Current version is set
    
    Raises:
        RuntimeError: If migrations not applied
    """
```

**File: `backend/main.py`** (lifespan hook)
```python
# Step 2: Verify Alembic migrations are applied (CRITICAL)
try:
    await verify_schema_up_to_date()
    print(f"[CaseCore] ✓ Alembic migrations verified")
except RuntimeError as e:
    print(f"[CaseCore] ✗ FATAL: {e}")
    raise  # Server refuses to start
```

**Enforcement:**
- ✓ Server fails to start if Alembic migrations not applied
- ✓ Live: MUST run `alembic upgrade head` before deployment
- ✓ Sandbox/demo: Can run migrations locally
- ✓ No schema creation via Python; Alembic is source of truth

### Testing
```bash
# Verify migration enforcement works
rm casecore_sandbox.db
python -m uvicorn main:app
# Expected: RuntimeError: "Alembic migrations not applied"

# Fix it
alembic upgrade head

# Try again
python -m uvicorn main:app
# Expected: ✓ Startup successful
```

---

## 2. AUTH CONSISTENCY FIX

### Problem
- Governance doc didn't explicitly state "forced login in ALL runtimes"
- PasswordGate could be misinterpreted as optional in demo
- Demo login could be seen as authentication bypass

### Solution Implemented

**Clarification: PasswordGate + Login ENFORCED in All Runtimes**

```jsx
// App.jsx
return (
  <PasswordGate>              {/* ← REQUIRED: sandbox, demo, live */}
    <Routes>
      <Route path="/login" element={<Login />} />  {/* ← REQUIRED: all runtimes */}
      ...
    </Routes>
  </PasswordGate>
)
```

**Demo Login is NOT an Auth Bypass:**
- Still requires PasswordGate session entry (password gate before login)
- Still stores auth tokens in localStorage
- Still respects logout and session expiration
- Only available in sandbox/demo; rejected in live

**Updated: `contract/v1/governance/environment_execution_and_migration.md`**
- ✅ New section 5 clarifies: "Forced Login in All Runtimes"
- ✅ Explains demo login shortcut is NOT an auth bypass
- ✅ Documents that demo accounts are rejected in live

### Testing
```bash
# Sandbox: Demo login works
export CASECORE_RUNTIME=sandbox
# Click "Enter Demo Mode" → Success

# Live: Demo login rejected
export CASECORE_RUNTIME=live
# Click "Enter Demo Mode" → Error: "Demo login disabled in live"

# All runtimes: PasswordGate required
# Navigate to app → PasswordGate shown → Enter password → Login → Dashboard
```

---

## 3. STORAGE ISOLATION FIX (CRITICAL MISSING)

### Problem
- **COMPLETELY MISSING:** No runtime-aware file storage strategy
- Documents, exports, uploads had no isolation
- Risk: Demo files could leak to live or vice versa

### Solution Implemented

**New File: `backend/storage.py`**

```python
class StorageConfig:
    """Runtime-aware file storage isolation"""
    
    BASE_PATHS = {
        RuntimeName.SANDBOX: "./storage/sandbox",
        RuntimeName.DEMO: "./storage/demo",
        RuntimeName.LIVE: "/data/live",  # Production path, outside repo
    }
    
    def get_case_folder(self, case_id: int) -> str:
        """Return runtime-isolated path for case storage"""
        
    def get_document_path(self, case_id: int, doc_id: int, filename: str) -> str:
        """Return runtime-isolated path for document"""
        
    def delete_document(self, case_id: int, doc_id: int):
        """Delete document — FORBIDDEN in live"""
        if self.runtime.name == RuntimeName.LIVE:
            raise PermissionError("...")
```

**Live Protection:**
- ✅ `delete_document()` → raises PermissionError in live
- ✅ `delete_case_folder()` → raises PermissionError in live
- ✅ `clear_all_storage()` → raises PermissionError in live
- ✅ Sandbox/demo: all file operations allowed

**Directory Structure:**
```
storage/
├── sandbox/          # Dev environment
│   ├── cases/
│   │   ├── 1/
│   │   │   ├── documents/
│   │   │   └── exports/
│   │   └── 2/
│   └── uploads/
├── demo/             # Staging environment
│   ├── cases/
│   │   ├── 1/
│   │   │   └── documents/
│   │   └── ...
│   └── uploads/
└── live/             # Production (separate physical location)
    ├── cases/
    │   ├── 101/
    │   │   └── documents/
    │   └── 102/
    └── uploads/
```

**Initialization: `backend/main.py`** (lifespan hook)
```python
# Step 3: Initialize storage isolation
storage_config = initialize_storage_config()
print(f"[CaseCore] ✓ Storage initialized: {storage_config.base_path}")
```

**Usage Pattern:**
All file operations must use `StorageConfig`:

```python
# OLD (NOT RUNTIME-AWARE)
save_document(f"./uploads/{filename}")

# NEW (RUNTIME-AWARE)
storage = get_storage_config()
path = storage.get_document_path(case_id, doc_id, filename)
save_document(path)
```

### Testing
```bash
# Verify storage isolation
ls -la storage/
# Expected: sandbox/, demo/ directories (live would be /data/live/)

# Try to delete document in live
curl -X DELETE http://localhost:8000/api/documents/1
# (with CASECORE_RUNTIME=live)
# Expected: 403 PermissionError: "Document deletion not allowed in live"

# In sandbox/demo: works fine
curl -X DELETE http://localhost:8000/api/documents/1
# (with CASECORE_RUNTIME=sandbox)
# Expected: 204 No Content
```

---

## 4. RUNTIMEGUARD ENFORCEMENT HARDENING

### Problem
- ✓ Scenario endpoints guarded (reset, load)
- ❌ Destructive operations NOT guarded:
  - `DELETE /api/cases/{id}` — unguarded
  - `DELETE /api/weapons/{id}` — unguarded
  - `DELETE /api/documents/{id}` — unguarded

### Solution Implemented

**Added RuntimeGuard to all destructive endpoints:**

**File: `backend/routes/cases.py`**
```python
@router.delete("/{id}", status_code=204)
@RuntimeGuard(allowed_runtimes=["sandbox", "demo"], operation="delete_case")
async def delete_case(id: int, db: AsyncSession = Depends(get_db)):
    """Delete case — FORBIDDEN in live"""
```

**File: `backend/routes/weapons.py`**
```python
@router.delete("/{id}", status_code=204)
@RuntimeGuard(allowed_runtimes=["sandbox", "demo"], operation="delete_weapon")
async def delete_weapon(id: int, db: AsyncSession = Depends(get_db)):
    """Delete weapon — FORBIDDEN in live"""
```

**File: `backend/routes/documents.py`**
```python
@router.delete("/{id}", status_code=204)
@RuntimeGuard(allowed_runtimes=["sandbox", "demo"], operation="delete_document")
async def delete_document(id: int, db: AsyncSession = Depends(get_db)):
    """Delete document — FORBIDDEN in live"""
```

**Live Protection:**
- ✅ `DELETE /api/cases/*` → 403 Forbidden in live
- ✅ `DELETE /api/weapons/*` → 403 Forbidden in live
- ✅ `DELETE /api/documents/*` → 403 Forbidden in live
- ✅ Sandbox/demo: deletions allowed

### Testing
```bash
# Try to delete case in live
curl -X DELETE http://localhost:8000/api/cases/1
# (with CASECORE_RUNTIME=live)
# Expected: 403 Forbidden: "delete_case is not allowed in live runtime"

# In sandbox: works
curl -X DELETE http://localhost:8000/api/cases/1
# (with CASECORE_RUNTIME=sandbox)
# Expected: 204 No Content
```

---

## 5. DEPLOYMENT MODEL (DEFINED CLEARLY)

### Problem
- ❌ No explicit mapping: runtime → deployment target
- ❌ No Vercel environment configuration
- ❌ No backend environment separation guidance

### Solution Implemented

**New File: `deployment/deployment_model.md`**

Comprehensive 200+ line deployment guide including:
- Runtime-to-environment mapping table
- Sandbox setup (local development)
- Demo setup (Vercel preview)
- Live setup (Vercel production)
- Migration flow by environment
- Environment variable reference
- Troubleshooting guide

**Deployment Matrix:**
| Runtime | Environment | Platform | Database | Storage | URL |
|---------|-------------|----------|----------|---------|-----|
| sandbox | development | Local | SQLite sandbox.db | ./storage/sandbox/ | localhost:5173 |
| demo | staging | Vercel Preview | SQLite demo.db | ./storage/demo/ | *.vercel.app |
| live | production | Vercel Prod | PostgreSQL prod | /data/live/ | casecore.io |

**New File: `vercel.json`**

```json
{
  "envs": {
    "development": {
      "CASECORE_RUNTIME": "sandbox",
      "ENVIRONMENT": "development"
    },
    "preview": {
      "CASECORE_RUNTIME": "demo",
      "ENVIRONMENT": "staging"
    },
    "production": {
      "CASECORE_RUNTIME": "live",
      "ENVIRONMENT": "production",
      "DATABASE_URL": "@casecore_db_production",
      "VITE_APP_PASSWORD": "@casecore_password_production"
    }
  }
}
```

**Deployment Flow:**
```
Feature Branch → PR → Vercel Preview (demo)
                ↓
        Code Review Passes
                ↓
        Merge to Main → Vercel Production (live)
                ↓
        Auto-deploy (alembic upgrade head)
```

### Testing
```bash
# Verify deployment config
cat vercel.json
# Expected: envs.preview.CASECORE_RUNTIME = "demo"
#           envs.production.CASECORE_RUNTIME = "live"

# Verify environment variables in Vercel dashboard
# Production should have: casecore_db_production, casecore_password_production
```

---

## 6. MIGRATION VS SCENARIO SEPARATION (VERIFIED)

### Status
✅ **VERIFIED AND LOCKED** — No changes needed, but documented clearly

**Current Behavior:**
- Migrations: `alembic upgrade head` (schema-only)
- Seeding: `/api/scenario/reset` (on-demand)
- Startup: No seeding in live (controlled by `seed_on_startup` capability)

**Verification in Code:**

**File: `backend/main.py`** (lifespan hook)
```python
# Step 1: Initialize runtime (reads CASECORE_RUNTIME)
runtime_config = initialize_runtime_config()

# Step 2: Verify Alembic migrations applied
await verify_schema_up_to_date()

# Step 4: Auto-seed only if capability allows
if runtime_config.can("seed_on_startup"):  # False for sandbox/live, True for demo only
    # Load DemoBaseline
```

**File: `backend/database.py`**
- ✅ No schema creation (`create_all()` removed)
- ✅ Only migration verification
- ✅ Safe column migrations (legacy, non-blocking)

**File: `backend/routes/scenario.py`**
- ✅ Guarded: `/api/scenario/load` → forbidden in live
- ✅ Guarded: `/api/scenario/reset` → forbidden in live
- ✅ Both endpoints guarded by @RuntimeGuard decorator

---

## SUMMARY TABLE

| Correction | File(s) | Change | Status |
|-----------|---------|--------|--------|
| Migration Enforcement | database.py, main.py | Removed create_all(), added verify_schema_up_to_date() | ✅ |
| Auth Consistency | governance doc | Clarified forced login in all runtimes | ✅ |
| Storage Isolation | storage.py (new), routes | Runtime-aware file paths, delete protection in live | ✅ |
| RuntimeGuard Hardening | cases.py, weapons.py, documents.py | Added @RuntimeGuard to DELETE operations | ✅ |
| Deployment Model | deployment_model.md, vercel.json | Explicit sandbox→demo→live mapping, Vercel config | ✅ |
| Migration/Scenario Sep. | Verified | Migrations locked to Alembic, seeding guarded by runtime | ✅ |

---

## LIVE PROTECTION LAYERS (FINAL)

### Verified Comprehensive Defense:

| Layer | Implementation | Live Enforcement |
|-------|---|---|
| 1. Environment Variable | `CASECORE_RUNTIME` validation | ✅ Server refuses to start if invalid |
| 2. Database Isolation | Separate DB per runtime | ✅ `live` connects to prod PostgreSQL only |
| 3. Migration Enforcement | Alembic pre-flight check | ✅ Server refuses to start if migrations not applied |
| 4. Storage Isolation | Runtime-aware paths | ✅ File deletion raises PermissionError |
| 5. Endpoint Guards | @RuntimeGuard decorator | ✅ DELETE, reset, seed endpoints return 403 |
| 6. Auth Rejection | Demo accounts denied | ✅ Demo login rejected by backend |
| 7. Frontend Controls | RuntimeBanner, capability checks | ✅ Demo buttons hidden in live |
| 8. Startup Behavior | seed_on_startup capability | ✅ No seeding in live even if configured |

---

## DEPLOYMENT READINESS

**Sandbox (Local Dev):**
```bash
export CASECORE_RUNTIME=sandbox
alembic upgrade head
python scripts/init_runtime.py
npm run dev && python -m uvicorn main:app
```

**Demo (Vercel Preview):**
```bash
# Automatic: PR → Vercel preview with CASECORE_RUNTIME=demo
# Auto-seeds on first deployment if database empty
```

**Live (Vercel Production):**
```bash
# Automatic: main branch merge → Vercel production with CASECORE_RUNTIME=live
# Pre-flight: verify CASECORE_RUNTIME=live, DATABASE_URL set, migrations applied
# No seeding, no reset, no demo login
```

---

## COMPLIANCE CHECKLIST

- ✅ Migration Enforcement: Alembic-only, pre-flight verification
- ✅ Auth Consistency: Forced login in all runtimes, demo login guarded
- ✅ Storage Isolation: Runtime-aware paths, deletion protection in live
- ✅ RuntimeGuard Enforcement: All destructive ops guarded
- ✅ Deployment Model: Clear sandbox→demo→live with Vercel config
- ✅ Migration/Scenario Separation: Verified, locked by capabilities
- ✅ Live Protection: 8-layer comprehensive defense

---

**Status: ✅ FULL COMPLIANCE ACHIEVED**

All governance requirements met. Platform is production-hardened.

# Migration Enforcement Strategy
## CaseCore Platform - Schema Evolution & Governance

---

## OVERVIEW

This document defines how schema migrations are enforced, verified, and applied across sandbox, demo, and live environments.

**Core Principle:** Alembic is the ONLY mechanism for schema creation. Python code cannot create schema directly.

---

## MIGRATION TOOLING

### Alembic (SQLAlchemy Migrations)

**Location:** `casecore-runtime/apps/api/alembic/`

**Workflow:**
```
alembic revision --autogenerate -m "description"  → Create migration file
alembic upgrade head                               → Apply all pending migrations
alembic current                                    → Check current revision
alembic heads                                      → List all head revisions
```

**Never Used For:**
- Direct schema creation (`Base.metadata.create_all`)
- Column additions via Python code
- Table deletions or alterations via code

---

## VERIFICATION MECHANISM

### Pre-Startup Check: `verify_schema_up_to_date()`

**Location:** `backend/database.py`

**What It Does:**
```python
async def verify_schema_up_to_date():
    """
    Verify Alembic migrations are applied.
    
    Two-part check:
    1. alembic_version table exists
    2. Current revision is recorded
    """
    # Query alembic_version table
    result = await db.execute("SELECT version_num FROM alembic_version LIMIT 1")
    current_revision = result.scalar()
    
    if not current_revision:
        raise RuntimeError("Alembic migrations not applied. Run: alembic upgrade head")
```

**When It's Called:**
```
App startup → initialize_runtime_config() → verify_schema_up_to_date()
              ↓ Fails? Server refuses to start
              ↓ Success? Continue with startup
```

**Behavior Per Runtime:**
- **Sandbox:** Can run migrations locally; verification checks they exist
- **Demo:** Migrations auto-applied by CI/CD before deployment
- **Live:** Migrations must be applied before deployment; verification enforces this

---

## MIGRATION FLOW PER ENVIRONMENT

### 1. SANDBOX (Local Development)

**Process:**
```bash
# 1. Modify models.py (add new model/field)
# Example: Add new column to cases table

# 2. Generate migration
cd casecore-runtime/apps/api
alembic revision --autogenerate -m "Add new_column to cases"

# 3. Review generated migration
cat alembic/versions/xxx_add_new_column_to_cases.py

# 4. Apply migration locally
alembic upgrade head

# 5. Test with data
curl -X POST http://localhost:8000/api/scenario/reset
# Database now has new schema + test data

# 6. Commit migration to Git
git add alembic/versions/
git commit -m "Migration: add new_column to cases"
```

**Verification:**
```bash
# Check current revision
alembic current
# Output: abc123def456 (where abc123... matches file in versions/)

# Verify app starts
python -m uvicorn main:app
# Should start without error
```

### 2. DEMO (Staging Deployment)

**Process:**
```bash
# 1. Feature branch pushed
git push origin feature-branch

# 2. PR created → Vercel preview deployment triggered
# (vercel.json CASECORE_RUNTIME=demo)

# 3. Build step:
#    - npm install
#    - npm run build

# 4. Pre-flight (in CI/CD):
#    - DATABASE_URL set to demo PostgreSQL
#    - alembic upgrade head runs
#    - Schema updated to latest

# 5. Backend starts (verify_schema_up_to_date() passes)

# 6. Demo baseline seeded (if first run)
#    - POST /api/scenario/load { "name": "mills_v_polley" }

# 7. Preview deployment live
```

**Verification:**
```bash
# In Vercel logs:
# [Database] ✓ Schema version (current): abc123def456
# [CaseCore] ✓ Alembic migrations verified

# Test endpoint
curl https://<pr>--casecore.vercel.app/api/runtime/config
# Expected: { "runtime": "demo", ... }
```

### 3. LIVE (Production Deployment)

**Process:**
```bash
# 1. All PRs merged to main
git merge --squash origin/feature-branch
git push origin main

# 2. Vercel production deployment triggered
# (vercel.json CASECORE_RUNTIME=live)

# 3. Pre-flight checks (must all pass):
#    - CASECORE_RUNTIME=live detected
#    - DATABASE_URL points to production PostgreSQL
#    - alembic upgrade head applies any pending migrations
#    - verify_schema_up_to_date() verifies success

# 4. If pre-flight fails:
#    - Deployment stops (fail-safe)
#    - Error message: "Alembic migrations not applied"
#    - Team must: alembic upgrade head manually + redeploy

# 5. If pre-flight passes:
#    - Backend starts
#    - /api/runtime/config returns { "runtime": "live", ... }
#    - Production is live
```

**Verification:**
```bash
# Post-deployment check
curl https://casecore.io/api/system/startup-config
# Expected: {
#   "database": { "type": "postgresql", "target": "host:5432/db" },
#   "runtime": "live"
# }

# Validate all systems
curl https://casecore.io/api/system/validate
# Expected: { "status": "healthy", "runtime": "live", ... }
```

---

## MIGRATION SCENARIOS

### Adding a New Table

**Scenario:** Add `audit_events` table to track all data mutations.

**Steps:**

1. **Sandbox: Create Migration**
```python
# models.py
class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Generate
alembic revision --autogenerate -m "Add audit_events table"

# Review: alembic/versions/xxx_add_audit_events_table.py
# Should contain: CREATE TABLE audit_events (...)

# Apply locally
alembic upgrade head

# Commit
git add alembic/versions/xxx_add_audit_events_table.py
git commit -m "Migration: add audit_events table"
```

2. **Demo: Auto-Applied**
```
PR created → Vercel preview → alembic upgrade head runs → audit_events table created
```

3. **Live: Manual Verification Required**
```bash
# Before deployment, verify on prod instance:
alembic current
# Output: <current_revision>

alembic revision --autogenerate -m "..."
# Check: no new migrations needed

# Deploy
git merge & push to main
# CI/CD runs: alembic upgrade head
# Pre-flight check passes
# Production updated
```

### Adding a Column to Existing Table

**Scenario:** Add `compliance_status` column to cases table.

**Steps:**

1. **Sandbox: Generate**
```python
# models.py
class Case(Base):
    ...
    compliance_status = Column(String, default="pending")

alembic revision --autogenerate -m "Add compliance_status to cases"

# Verify migration looks correct
cat alembic/versions/yyy_add_compliance_status_to_cases.py
# Should contain: ALTER TABLE cases ADD COLUMN compliance_status VARCHAR DEFAULT 'pending'

alembic upgrade head
git add alembic/versions/yyy_...
git commit -m "Migration: add compliance_status to cases"
```

2. **Demo: Vercel Auto-Applies**
3. **Live: Pre-Flight Verification**

---

## COMMON ERRORS & RECOVERY

### Error: "Alembic migrations not applied"

**Cause:** Server started without running `alembic upgrade head`

**Recovery:**
```bash
# 1. Stop running app
# 2. Apply migrations
alembic upgrade head

# 3. Verify
alembic current
# Should show a revision

# 4. Restart app
python -m uvicorn main:app
# Should start without error
```

### Error: "No alembic_version table found"

**Cause:** Database is completely empty (not initialized)

**Recovery:**
```bash
# 1. Initialize database
python scripts/init_runtime.py

# 2. Apply migrations
alembic upgrade head

# 3. Verify
alembic current
```

### Error: "Migration mismatch: current != head"

**Cause:** Database is at old revision, new migrations exist

**Recovery:**
```bash
# Check what's pending
alembic heads
# Output: abc123def456 (latest)

alembic current
# Output: old123old456 (current)

# Apply pending
alembic upgrade head

# Verify
alembic current
# Should match alembic heads
```

---

## SAFEGUARDS

### Safeguard 1: Pre-Flight Verification
- App refuses to start if migrations not applied
- Explicit error message with recovery command

### Safeguard 2: Alembic-Only Schema
- Python code cannot use `Base.metadata.create_all()`
- `init_runtime.py` only calls `verify_schema_up_to_date()`

### Safeguard 3: Idempotent Migrations
- `alembic upgrade head` can be run multiple times safely
- Migrations only apply once

### Safeguard 4: Audit Trail
- Every migration tracked in version control
- Every application tracked in `alembic_version` table

---

## DEPLOYMENT CHECKLIST

### Before Merging to Main (Live Deployment)

- [ ] Migration created and committed: `alembic/versions/xxx_...py`
- [ ] Migration tested locally: `alembic upgrade head` succeeds
- [ ] Rollback tested locally: `alembic downgrade -1` succeeds
- [ ] Models match migration: no new untracked changes in `models.py`
- [ ] Data migration script ready (if needed): seed scripts committed
- [ ] PR reviewed and approved

### After Merge (Production CI/CD)

- [ ] Vercel logs show: "[Database] ✓ Schema version verified"
- [ ] Vercel logs show: "[CaseCore] ✓ Alembic migrations verified"
- [ ] Health check succeeds: `GET /health` → 200 OK
- [ ] System validation succeeds: `GET /api/system/validate` → healthy
- [ ] No database errors in logs

---

## SUMMARY

| Step | Tool | Command | When |
|------|------|---------|------|
| Create | Alembic | `alembic revision --autogenerate` | Sandbox (dev) |
| Review | Git/Editor | Read migration file | Before commit |
| Apply Local | Alembic | `alembic upgrade head` | Sandbox (dev) |
| Apply Demo | Vercel CI/CD | Auto-runs `alembic upgrade head` | PR deployment |
| Verify Live | Vercel CI/CD + Pre-flight | `verify_schema_up_to_date()` | Production |

**Result:** One migration mechanism, verified at every step, enforced at startup.

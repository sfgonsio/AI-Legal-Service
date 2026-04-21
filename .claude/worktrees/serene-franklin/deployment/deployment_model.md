# CaseCore Deployment Model
## Runtime-to-Environment Mapping

---

## DEPLOYMENT MATRIX

| Runtime | Environment | Platform | Database | Storage | URL |
|---|---|---|---|---|---|
| **sandbox** | Development | Local (laptop) | SQLite `casecore_sandbox.db` | `./storage/sandbox/` | `localhost:5173` |
| **demo** | Staging | Vercel Preview | SQLite `casecore_demo.db` | `./storage/demo/` | `*.vercel.app` (preview) |
| **live** | Production | Vercel Production | PostgreSQL (prod) | `/data/live/` | `casecore.io` |

---

## SANDBOX (Development)

### Environment: `development`
### Platform: Local machine
### CASECORE_RUNTIME: `sandbox`

**Setup:**
```bash
export CASECORE_RUNTIME=sandbox
export DATABASE_URL=sqlite+aiosqlite:///./casecore_sandbox.db
export ENVIRONMENT=development
export PORT=8000
```

**Database:**
- SQLite: `./casecore_sandbox.db`
- Resettable at any time
- Can run migrations locally

**Storage:**
- Directory: `./storage/sandbox/`
- All files local to dev machine
- Can be deleted safely

**Features Enabled:**
- ✓ Reset endpoint (`POST /api/scenario/reset`)
- ✓ Seed endpoint (`POST /api/scenario/load`)
- ✓ Demo login allowed
- ✓ Admin operations allowed

**Startup Sequence:**
```bash
# 1. Install dependencies
npm install
pip install -r requirements.txt

# 2. Apply migrations
cd casecore-runtime/apps/api
alembic upgrade head

# 3. Initialize runtime
python scripts/init_runtime.py

# 4. Run backend
python -m uvicorn casecore.backend.main:app --reload

# 5. Run frontend (separate terminal)
cd casecore/frontend
npm run dev
```

**Verification:**
```bash
curl http://localhost:8000/api/runtime/config
# Expected: { "runtime": "sandbox", ... }

curl -X POST http://localhost:8000/api/scenario/reset
# Expected: 200 OK { "status": "reset", ... }
```

---

## DEMO (Staging)

### Environment: `staging`
### Platform: Vercel (Preview Deployment)
### CASECORE_RUNTIME: `demo`

**Configuration:**
- Triggered by: Pull requests to `main` branch
- Preview URL: `<pr-number>--casecore.vercel.app`
- Automatic deployment of every PR
- Isolated from production

**Environment Variables (Vercel Preview):**
```bash
CASECORE_RUNTIME=demo
DATABASE_URL=sqlite+aiosqlite:///./casecore_demo.db
ENVIRONMENT=staging
PORT=8000
VITE_API_URL=  # Vercel proxies /api to backend
```

**Database:**
- SQLite: `./casecore_demo.db` (ephemeral on preview)
- OR: Shared PostgreSQL demo database (if configured)
- Auto-seeds on first deployment if empty

**Storage:**
- Directory: `./storage/demo/`
- Ephemeral (lost when preview deployment destroyed)
- Can be safely recreated

**Features Enabled:**
- ✓ Reset endpoint (for presentations)
- ✓ Scenario loading
- ✓ Demo login
- ✓ PasswordGate

**Deployment Trigger:**
```bash
# Automatic:
git push origin feature-branch
# Creates: PR → Vercel preview deployment

# Or manual rebuild in Vercel dashboard
```

**Verification:**
```bash
# Get preview URL from Vercel
curl https://<pr>--casecore.vercel.app/api/runtime/config
# Expected: { "runtime": "demo", ... }

# Reset before showing to client
curl -X POST https://<pr>--casecore.vercel.app/api/scenario/reset
# Expected: 200 OK
```

**Use Cases:**
- Client demonstrations
- Feature review meetings
- Investor presentations
- Internal QA testing

---

## LIVE (Production)

### Environment: `production`
### Platform: Vercel (Production Deployment)
### CASECORE_RUNTIME: `live`

**Configuration:**
- Triggered by: Merge to `main` branch
- Production URL: `casecore.io` (configured in Vercel)
- Single source of truth for all client data
- All changes monitored and logged

**Environment Variables (Vercel Production):**
```bash
CASECORE_RUNTIME=live
DATABASE_URL=postgresql://user:pass@prod.supabase.co:5432/casecore
ENVIRONMENT=production
PORT=8000
VITE_APP_PASSWORD=<strong_password>
VITE_API_URL=https://api.casecore.io  # If separate API domain
```

**Database:**
- PostgreSQL: Production instance (Supabase, Render, or managed)
- **NEVER replaced or reset**
- Automated daily backups (30-day retention)
- Point-in-time recovery available

**Storage:**
- Directory: `/data/live/` (production file system)
- Persistent across deployments
- Managed by infrastructure team

**Features DISABLED:**
- ✗ Reset endpoint (returns 403 Forbidden)
- ✗ Scenario loading (returns 403 Forbidden)
- ✗ Demo login (rejected by auth)
- ✓ Standard authentication required
- ✓ PasswordGate enforced

**Deployment Process:**

1. **Code Review:**
   ```bash
   # PR review completed
   # All tests passing
   ```

2. **Merge to Main:**
   ```bash
   git merge --squash origin/feature-branch
   git push origin main
   ```

3. **Automatic Deployment:**
   ```
   main branch push
   ↓
   Vercel detects change
   ↓
   Build: npm run build
   ↓
   Pre-flight checks:
     - CASECORE_RUNTIME=live validation
     - Database connectivity check
     - Schema version verification
   ↓
   Deploy to production
   ↓
   Smoke tests (optional)
   ```

4. **Post-Deployment Verification:**
   ```bash
   # Check runtime config
   curl https://casecore.io/api/runtime/config
   # Expected: { "runtime": "live", "capabilities": {...falses...} }

   # Verify reset is blocked
   curl -X POST https://casecore.io/api/scenario/reset
   # Expected: 403 Forbidden

   # Test authentication
   # Login with real credentials (not demo accounts)
   ```

**Failure Handling:**

If deployment fails:
1. Vercel automatically rolls back previous version
2. Check logs: `vercel logs --production`
3. Fix issue and re-merge to main
4. Redeployment is automatic

If production data corrupted:
1. **Do NOT use** `/api/scenario/reset` (blocked anyway)
2. Use Supabase/database provider's backup restore
3. Choose point-in-time recovery
4. Verify data integrity before resuming operations

**Monitoring:**

```bash
# Real-time logs
vercel logs --production --follow

# Error tracking (if configured)
# Sentry, DataDog, New Relic, etc.

# Database monitoring
# Supabase dashboard
```

---

## MIGRATION FLOW BY ENVIRONMENT

### Adding a New Table

**Step 1: Create Migration (Sandbox)**
```bash
# On laptop (sandbox)
export CASECORE_RUNTIME=sandbox
cd casecore-runtime/apps/api

# Modify models.py
# Add new model class

# Generate migration
alembic revision --autogenerate -m "Add new_table"

# Review migration
cat alembic/versions/xxx_add_new_table.py

# Apply locally
alembic upgrade head

# Test with data
curl -X POST http://localhost:8000/api/scenario/reset
```

**Step 2: Test (Demo)**
```bash
# Push to feature branch
git commit -m "migration: add new_table"
git push origin feature-branch

# PR triggers Vercel preview (demo)
# Preview automatically runs: alembic upgrade head
# Demo baseline seeds automatically

# Verify in preview
curl -X POST https://<pr>--casecore.vercel.app/api/scenario/reset
# Should succeed with new table empty
```

**Step 3: Deploy (Live)**
```bash
# Merge to main
git merge --squash origin/feature-branch
git push origin main

# Vercel production deployment:
# 1. Pre-flight: verify alembic_version table exists
# 2. Deploy: run alembic upgrade head
# 3. Verify: new table is now in production schema

# Post-deployment
curl https://casecore.io/api/scenario/status
# New table exists in counts (if applicable)
```

---

## VERCEL CONFIGURATION

### vercel.json

```json
{
  "buildCommand": "cd casecore-runtime/apps/api/casecore/frontend && npm run build",
  "outputDirectory": "casecore-runtime/apps/api/casecore/frontend/dist",
  "installCommand": "npm install",
  
  "env": {
    "CASECORE_RUNTIME": {
      "value": "sandbox"
    }
  },
  
  "envs": {
    "development": {
      "CASECORE_RUNTIME": "sandbox",
      "ENVIRONMENT": "development",
      "PORT": "8000"
    },
    "preview": {
      "CASECORE_RUNTIME": "demo",
      "ENVIRONMENT": "staging",
      "PORT": "8000"
    },
    "production": {
      "CASECORE_RUNTIME": "live",
      "ENVIRONMENT": "production",
      "PORT": "8000",
      "DATABASE_URL": "@casecore_production_db",  # Vercel secret
      "VITE_APP_PASSWORD": "@casecore_live_password"  # Vercel secret
    }
  }
}
```

### Environment Secrets (Vercel Dashboard)

**Production Environment Only:**
- `casecore_production_db`: PostgreSQL connection string
- `casecore_live_password`: PasswordGate access password

---

## ENVIRONMENT VARIABLE REFERENCE

### Required Everywhere

```bash
CASECORE_RUNTIME=sandbox|demo|live  # Runtime mode
ENVIRONMENT=development|staging|production
PORT=8000
```

### Database

```bash
# Sandbox/Demo (optional; auto-detected)
DATABASE_URL=sqlite+aiosqlite:///./casecore_sandbox.db

# Live (REQUIRED)
DATABASE_URL=postgresql://user:pass@host:5432/casecore
```

### Frontend

```bash
# Development (optional; Vite proxies to localhost:8000)
VITE_API_URL=

# Staging/Production (point to API)
VITE_API_URL=https://api.casecore.io

# PasswordGate password
VITE_APP_PASSWORD=<password>  # Vercel secret in production
```

### API Keys (All Environments)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=...  # If used
```

---

## TROUBLESHOOTING DEPLOYMENTS

### "CASECORE_RUNTIME not set" in Vercel

**Issue:**
```
RuntimeError: CASECORE_RUNTIME must be set to sandbox, demo, or live
```

**Fix:**
```bash
# Vercel dashboard
Settings → Environment Variables
→ Add "CASECORE_RUNTIME" with value "demo" (for preview)
           or "live" (for production)
```

### Migration Fails on Production Deploy

**Issue:**
```
RuntimeError: Alembic migrations not applied
```

**Fix:**
1. Check previous deployment logs
2. Verify migration file is correct
3. Test locally: `alembic upgrade head`
4. Re-merge to main (triggers redeploy)

### Demo Database Locked

**Issue:**
```
sqlite3.OperationalError: database is locked
```

**Fix:**
```bash
# On local machine (sandbox)
rm casecore_sandbox.db
python scripts/init_runtime.py

# On Vercel preview (demo)
# Destroy and recreate preview deployment
```

---

## SUMMARY

- **Sandbox:** Local dev, full control, reset/seed at will
- **Demo:** PR preview, automated, for client presentations
- **Live:** Production, protected, no reset/seed, real data only

Each environment is isolated; changes cannot leak between them.

# Deployment Validation Checklist
## Pre-Deployment, Deployment, and Post-Deployment Verification

---

## PRE-DEPLOYMENT CHECKLIST (Before merging to main)

### Code Quality
- [ ] All tests passing: `npm test`, `pytest tests/`
- [ ] No linting errors: `eslint src/`, `pylint backend/`
- [ ] Type checking passes: `tsc --noEmit`, `mypy backend/`
- [ ] No console errors/warnings in development

### Migrations
- [ ] New migrations created (if schema changes): `alembic/versions/*.py`
- [ ] Migrations tested locally: `alembic upgrade head` succeeds
- [ ] Rollback tested: `alembic downgrade -1` succeeds
- [ ] Models match migrations: no untracked model changes
- [ ] Data migration scripts ready (if needed)

### Runtime Governance
- [ ] All POST/PATCH/DELETE endpoints have `@RuntimeGuard`
- [ ] No mutation endpoints unguarded in live-sensitive routes
- [ ] RuntimeGuard tests passing: `pytest test_runtime_guards.py`
- [ ] Live protection tests passing: `pytest test_live_protection.py`

### Environment Configuration
- [ ] `.env` variables documented in `.env.example`
- [ ] Secrets not committed (no DATABASE_URL in code)
- [ ] VITE_ variables set correctly for target environment
- [ ] All required env vars present in Vercel dashboard

### Documentation
- [ ] README updated if user-facing changes
- [ ] Governance docs updated if runtime behavior changed
- [ ] Migration docs updated with migration strategy
- [ ] Deployment notes in PR description

### Security
- [ ] No hardcoded credentials
- [ ] No API keys in logs
- [ ] No PII in error messages
- [ ] Auth flow unchanged or properly updated
- [ ] Rate limiting considered for new endpoints

### Review
- [ ] Code reviewed by at least one team member
- [ ] Merge conflicts resolved
- [ ] Branch up-to-date with main

---

## DEPLOYMENT VALIDATION CHECKLIST (During deployment)

### Vercel Build Phase

#### Build Output
- [ ] Build command completes without errors
- [ ] No "error" strings in build logs
- [ ] Asset optimization completes
- [ ] Bundle size within limits (if tracked)

#### Pre-Flight Checks (CI/CD Pipeline)

```bash
# These should run before app starts

# 1. Runtime detection
[ ] CASECORE_RUNTIME properly set (sandbox|demo|live)

# 2. Database connectivity
[ ] DATABASE_URL accessible (if needed)
[ ] Connection pool initialized
[ ] Test query succeeds: SELECT 1

# 3. Migration verification
[ ] Alembic upgrade head runs successfully
[ ] No migration errors in logs
[ ] [Database] ✓ Schema version verified

# 4. Storage initialization
[ ] Storage path accessible
[ ] Base directory created
[ ] Permissions allow write operations (sandbox/demo)

# 5. Runtime config validation
[ ] CASECORE_RUNTIME detected correctly
[ ] Capabilities loaded
[ ] Environment set (development|staging|production)
```

#### App Startup Logs (Should See)

```
======================================================================
STARTUP CONFIGURATION
======================================================================
Runtime:     SANDBOX|DEMO|LIVE
Environment: development|staging|production
Database:    casecore_sandbox.db | casecore_demo.db | ***@prod.example.com:5432/db
Storage:     ./storage/sandbox | ./storage/demo | /data/live
======================================================================
[CaseCore] ✓ All systems ready (sandbox|demo|live)
======================================================================
```

#### Health Checks

- [ ] `/health` returns 200 OK
- [ ] `/api/runtime/config` returns correct runtime
- [ ] `/api/system/health` returns healthy
- [ ] `/api/system/validate` returns status: healthy

### Demo Deployment (Vercel Preview)

- [ ] Preview URL accessible: `https://<pr>--casecore.vercel.app/`
- [ ] PasswordGate shows (if configured)
- [ ] RuntimeBanner shows "🎭 DEMO"
- [ ] Login works: test with demo account
- [ ] Dashboard loads: cases visible
- [ ] Scenario reset works: `POST /api/scenario/reset` returns 200

### Live Deployment (Vercel Production)

- [ ] Production URL accessible: `https://casecore.io/`
- [ ] PasswordGate shows and requires strong password
- [ ] RuntimeBanner shows "🔴 LIVE" in red
- [ ] Standard login works: test with real credentials
- [ ] Demo login FAILS: "Demo login disabled in live"
- [ ] Dashboard loads: real cases visible
- [ ] Reset endpoint FAILS: `POST /api/scenario/reset` returns 403
- [ ] Delete operations FAIL in live: `DELETE /api/cases/1` returns 403
- [ ] `/api/system/validate` shows all systems healthy

---

## POST-DEPLOYMENT CHECKLIST (After deployment)

### Immediate (within 5 minutes)

- [ ] No error alerts in monitoring system
- [ ] Error rate normal (no spike)
- [ ] Response times normal (no degradation)
- [ ] Database connections healthy
- [ ] API endpoints responding

### Short-term (within 1 hour)

```bash
# Validate runtime consistency
curl https://casecore.io/api/system/validate
# Expected: { "status": "healthy", "runtime": "live", ... }

# Check startup config
curl https://casecore.io/api/system/startup-config
# Expected: Runtime, environment, database, storage paths

# Test live protection
curl -X POST https://casecore.io/api/scenario/reset
# Expected: 403 Forbidden

# Test auth
curl -X POST https://casecore.io/api/auth/login \
  -d '{"email": "attorney@casecore.io", "password": "test"}'
# Expected: 401 Unauthorized (demo disabled in live)
```

### Smoke Tests (Critical Paths)

- [ ] Login successful (real user)
- [ ] Dashboard displays cases
- [ ] Case detail page loads
- [ ] Can view documents
- [ ] Can navigate tabs (Overview, Weapons, Strategies, etc.)
- [ ] War Room accessible
- [ ] Search/filter works
- [ ] Export/download works

### Monitoring (Ongoing)

- [ ] Error logs monitored for new patterns
- [ ] Performance metrics tracked
- [ ] Database slow query logs checked
- [ ] User feedback monitored
- [ ] Analytics updated (if used)

### Rollback Readiness

- [ ] Previous version tagged in Vercel
- [ ] Database backup created (if production)
- [ ] Rollback command documented
- [ ] Estimated rollback time < 5 minutes

---

## ENVIRONMENT-SPECIFIC CHECKLISTS

### SANDBOX Deployment

```
✅ Pre-deployment
  - Migrations tested locally
  - Guards tested locally
  - Tests passing

✅ Deployment
  - CASECORE_RUNTIME=sandbox detected
  - Storage at ./storage/sandbox/
  - Database at ./casecore_sandbox.db

✅ Post-deployment
  - RuntimeBanner shows "🔒 SANDBOX"
  - Demo login works
  - Reset works: POST /api/scenario/reset → 200
  - Delete works: DELETE /api/cases/1 → 204
```

### DEMO Deployment

```
✅ Pre-deployment
  - All sandbox checks pass
  - Feature complete and tested

✅ Deployment
  - CASECORE_RUNTIME=demo detected
  - Vercel preview URL live
  - alembic upgrade head applied

✅ Post-deployment
  - RuntimeBanner shows "🎭 DEMO"
  - Demo baseline seeded (if first run)
  - Reset works for presentations
  - Can test new features

✅ Cleanup
  - Destroy preview after PR merged
  - Storage cleaned up
```

### LIVE Deployment

```
✅ Pre-deployment
  - Code reviewed
  - All tests passing
  - Migrations tested
  - Guards verified
  - Backup created
  - Rollback plan ready

✅ Deployment
  - CASECORE_RUNTIME=live detected
  - DATABASE_URL points to production
  - alembic upgrade head applied (no errors)
  - verify_schema_up_to_date() passes
  - All env vars set correctly

✅ Immediate Post-deployment
  - /health returns 200
  - /api/system/validate returns healthy
  - No error alerts
  - Performance normal
  - RuntimeBanner shows "🔴 LIVE"

✅ Monitoring (Ongoing)
  - No data corruptions
  - Reset endpoint properly blocked (403)
  - Demo login properly blocked (401)
  - Delete operations properly blocked (403)
  - All mutations guarded
  - Users successfully logging in
  - Cases visible and editable

✅ Weekly Verification
  - Database integrity verified
  - Backup success confirmed
  - Runtime guards still enforced
  - No unauthorized access attempts
```

---

## VALIDATION ENDPOINT RESPONSES

### Healthy Deployment

```json
{
  "status": "healthy",
  "runtime": "live",
  "checks": {
    "database_accessible": true,
    "database_error": null,
    "migrations_current": true,
    "migrations_error": null,
    "storage_accessible": true,
    "storage_error": null,
    "startup_config_loaded": true
  },
  "timestamp": "2026-04-20T12:34:56Z"
}
```

### Degraded Deployment (Storage Issue)

```json
{
  "status": "degraded",
  "runtime": "live",
  "checks": {
    "database_accessible": true,
    "migrations_current": true,
    "storage_accessible": false,
    "storage_error": "Permission denied: /data/live",
    "startup_config_loaded": true
  },
  "timestamp": "2026-04-20T12:34:56Z"
}
```

### Critical Deployment (Database Down)

```json
{
  "status": "critical",
  "runtime": "live",
  "checks": {
    "database_accessible": false,
    "database_error": "Connection refused: localhost:5432",
    "migrations_current": false,
    "storage_accessible": true,
    "startup_config_loaded": true
  },
  "timestamp": "2026-04-20T12:34:56Z"
}
```

---

## TROUBLESHOOTING

### Common Issues During Deployment

#### Issue: "Alembic migrations not applied"
**Cause:** `alembic upgrade head` not run before app startup
**Fix:**
1. Check Vercel build logs for: `alembic upgrade head`
2. If missing, add to CI/CD pipeline
3. Redeploy

#### Issue: "Storage path not accessible"
**Cause:** Permissions issue or directory doesn't exist
**Fix:**
1. Check directory permissions
2. Ensure parent directory exists
3. For production: `/data/live/` must be writeable

#### Issue: "Runtime mismatch: frontend != backend"
**Cause:** Frontend env vars don't match backend CASECORE_RUNTIME
**Fix:**
1. Check Vercel env vars for branch
2. Frontend should use same CASECORE_RUNTIME as backend
3. Redeploy with correct env vars

#### Issue: "Database connection timeout"
**Cause:** DATABASE_URL incorrect or network issue
**Fix:**
1. Verify DATABASE_URL in Vercel secrets
2. Check database is running and accessible
3. Verify firewall rules
4. Test connection locally before redeploying

---

## AUTOMATED CHECKS (CI/CD)

```yaml
# Example .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Pre-deployment checks
      - name: Run migrations on test DB
        run: alembic upgrade head
      
      - name: Run guard tests
        run: pytest test_runtime_guards.py
      
      - name: Run live protection tests
        run: pytest test_live_protection.py
      
      - name: Check all mutations guarded
        run: ./scripts/validate_guards.sh
      
      - name: Lint code
        run: npm run lint && pylint backend/
      
      - name: Run tests
        run: npm test && pytest tests/
  
  deploy:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: vercel deploy --prod
      
      - name: Validate deployment
        run: ./scripts/validate_deployment.sh
```

---

## SUMMARY

| Phase | Checklist | Critical Items |
|-------|-----------|---|
| **Pre-Deployment** | ✅ Code, Migrations, Guards, Tests | All passing, guards added, no unguarded mutations |
| **Deployment** | ✅ Build, Pre-flight, Startup | Migrations applied, runtime detected, all systems ready |
| **Post-Deployment** | ✅ Health, Protection, Smoke Tests | Guards enforced, demo blocked in live, data protected |
| **Ongoing** | ✅ Monitoring, Integrity, Performance | No errors, no unauthorized access, backup verified |

**Result:** Production-hardened, governance-enforced, fully validated deployment.

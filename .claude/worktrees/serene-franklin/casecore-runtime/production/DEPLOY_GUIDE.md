# CaseCore Deployment Guide
## Render (Backend API) + Vercel (Frontend)

---

## Prerequisites

Before you start, you need:
- A GitHub account (free) — both Render and Vercel deploy from GitHub repos
- A Render account — sign up at render.com
- A Vercel account — sign up at vercel.com (use "Continue with GitHub")

---

## Step 1: Push Code to GitHub

Create a new private GitHub repository for CaseCore.

1. Go to github.com → New Repository
2. Name: `casecore` (or whatever you prefer)
3. Set to **Private**
4. Do NOT initialize with README (we already have files)
5. Click "Create repository"

Then push the production folder. From your local machine:

```bash
cd /path/to/AI Legal Service/casecore-runtime/production
git init
git add .
git commit -m "Initial CaseCore production deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/casecore.git
git push -u origin main
```

---

## Step 2: Deploy Backend to Render

### 2A. Create Web Service

1. Log into render.com
2. Click "New" → "Web Service"
3. Connect your GitHub account if not already connected
4. Select the `casecore` repository
5. Configure:
   - **Name:** `casecore-api`
   - **Region:** Oregon (US West) — closest to Sacramento
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Starter ($7/month)

### 2B. Add Persistent Disk

This is critical — without it, your SQLite database gets wiped on every deploy.

1. In the service settings, scroll to "Disks"
2. Click "Add Disk"
3. **Name:** `casecore-data`
4. **Mount Path:** `/opt/render/project/src/data`
5. **Size:** 1 GB (plenty for SQLite + case data)

### 2C. Set Environment Variables

In the service "Environment" tab, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/casecore.db` |
| `PYTHONUNBUFFERED` | `1` |
| `ENVIRONMENT` | `production` |
| `FRONTEND_URL` | *(add after Vercel deploy — see Step 3)* |

### 2D. Deploy

Click "Create Web Service". Render will:
1. Clone your repo
2. Install Python dependencies
3. Start the FastAPI server
4. Give you a URL like: `https://casecore-api.onrender.com`

### 2E. Verify

Visit `https://casecore-api.onrender.com/health` — you should see:
```json
{"status": "healthy", "service": "CaseCore API", "version": "1.0.0"}
```

Visit `https://casecore-api.onrender.com/docs` for the interactive Swagger API docs.

---

## Step 3: Deploy Frontend to Vercel

### 3A. Import Project

1. Log into vercel.com
2. Click "Add New" → "Project"
3. Import the same `casecore` GitHub repository
4. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### 3B. Set Environment Variable

In "Environment Variables" section:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://casecore-api.onrender.com` |

*(Use the actual Render URL from Step 2D)*

### 3C. Deploy

Click "Deploy". Vercel will:
1. Install npm dependencies
2. Build the React app
3. Deploy to their CDN
4. Give you a URL like: `https://casecore.vercel.app`

### 3D. Update Render CORS

Go back to Render → your casecore-api service → Environment:
- Set `FRONTEND_URL` to your Vercel URL (e.g., `https://casecore.vercel.app`)
- Render will auto-redeploy with the new CORS setting

---

## Step 4: Custom Domain (Optional)

### For Render (API):
1. Service Settings → Custom Domains
2. Add `api.casecore.io` (or your domain)
3. Add the DNS records Render provides

### For Vercel (Frontend):
1. Project Settings → Domains
2. Add `app.casecore.io` (or your domain)
3. Add the DNS records Vercel provides

---

## What to Watch For

### Render Gotchas
- **First deploy takes 2-3 minutes** — the build step installs all Python packages
- **Auto-deploy on push** — every `git push` to main triggers a new deploy
- **Health checks** — Render pings `/health` every 30 seconds. If it fails 3 times, the service restarts
- **Persistent disk** — MUST be configured before first data write, or your DB lives in ephemeral storage and gets wiped
- **WebSocket** — fully supported on Starter plan, no special config needed. The deposition real-time feature will work out of the box
- **Logs** — available in the Render dashboard under "Logs" tab. Check here first if something breaks

### Vercel Gotchas
- **Environment variables with VITE_ prefix** — Vite only exposes env vars that start with `VITE_` to the browser. The API URL MUST be `VITE_API_URL`, not just `API_URL`
- **Serverless functions** — we are NOT using Vercel serverless. The frontend is purely static (React SPA) served from Vercel's CDN. All API calls go to Render
- **Build cache** — if you change env vars, you may need to redeploy (Vercel Settings → Deployments → Redeploy)

### SQLite Limitations (Known, Planned)
- SQLite handles single-user and small-team use perfectly
- When you scale to multiple attorneys hitting the API simultaneously, migrate to PostgreSQL
- The migration is a config change: swap `DATABASE_URL` to a Postgres connection string. SQLAlchemy handles the rest
- Render offers managed PostgreSQL starting at $7/month when you're ready

---

## Migration Path to AWS/GCP

When CaseCore generates revenue and needs to scale:

### Phase 1: Render Starter ($7/month) ← YOU ARE HERE
- SQLite on persistent disk
- Single instance
- Good for: development, demos, small attorney team

### Phase 2: Render Pro ($25/month)
- Upgrade to Render PostgreSQL ($7/month)
- Auto-scaling web service
- Good for: production use with 5-10 concurrent users

### Phase 3: AWS/GCP ($200-500/month)
- Push Docker images to ECR/GCR (Dockerfile already exists)
- Deploy to ECS Fargate or GCP Cloud Run
- RDS PostgreSQL or Cloud SQL
- Add Redis for WebSocket scaling
- CloudFront/Cloud CDN for frontend
- Good for: enterprise scale, multi-case, multi-firm

The code is already containerized and cloud-portable. No rewrites needed.

---

## Directory Structure on Render

After deployment, your Render service looks like:

```
/opt/render/project/src/
├── backend/
│   ├── main.py              ← FastAPI entry point
│   ├── database.py          ← SQLAlchemy setup
│   ├── models.py            ← ORM models
│   ├── schemas.py           ← Pydantic schemas
│   ├── seed_data.py         ← Mills v. Polley case data
│   ├── requirements.txt     ← Python dependencies
│   ├── routes/
│   │   ├── cases.py
│   │   ├── weapons.py
│   │   ├── strategies.py
│   │   ├── coas.py
│   │   ├── documents.py
│   │   └── deposition.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── opposition_agent.py
│   │   ├── strategy_agent.py
│   │   ├── deposition_agent.py
│   │   └── document_agent.py
│   └── data/                ← PERSISTENT DISK mounted here
│       └── casecore.db      ← SQLite database (survives deploys)
├── frontend/
│   └── ...                  ← Deployed separately to Vercel
├── render.yaml
└── docker-compose.yml       ← For local dev only
```

---

## Quick Reference

| What | Where |
|------|-------|
| API docs | `https://YOUR-RENDER-URL/docs` |
| Health check | `https://YOUR-RENDER-URL/health` |
| Render dashboard | `dashboard.render.com` |
| Vercel dashboard | `vercel.com/dashboard` |
| Render logs | Dashboard → Service → Logs |
| Redeploy | `git push origin main` (auto-deploys both) |
| Local dev | `cd backend && uvicorn main:app --reload` |

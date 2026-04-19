# CaseCore GitHub Setup & Workflow

## Initial Repository Setup

### 1. Create the Repository

Go to github.com → New Repository:
- **Name:** `casecore`
- **Visibility:** Private
- **Do NOT** initialize with README (we have our own files)

### 2. Push the Code

Open terminal, navigate to the production folder:

```bash
cd "/path/to/AI Legal Service/casecore-runtime/production"

git init
git add .
git commit -m "Initial CaseCore platform — FastAPI backend, React frontend, AI agents"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/casecore.git
git push -u origin main
```

### 3. Create the Branch Structure

```bash
# Create dev branch (your working branch)
git checkout -b dev
git push -u origin dev

# Create staging branch (pre-production testing)
git checkout -b staging
git push -u origin staging

# Go back to dev for daily work
git checkout dev
```

---

## Branch Strategy

```
main (production)     ← auto-deploys to Render + Vercel production
  ↑ merge via PR
staging               ← auto-deploys to Render staging (optional)
  ↑ merge via PR
dev                   ← your daily working branch
  ↑ feature branches
feature/xyz           ← individual features, merged to dev via PR
```

### Rules

| Branch | Who pushes | Deploys to | Protected? |
|--------|-----------|------------|------------|
| `main` | PR merge only | Render production + Vercel production | Yes |
| `staging` | PR from dev | Render staging (optional) | Yes |
| `dev` | You + Claude | Nothing (local testing) | No |
| `feature/*` | Anyone | Nothing | No |

### Daily Workflow

```bash
# Start a new feature
git checkout dev
git pull origin dev
git checkout -b feature/deposition-websocket

# Work on it...
git add .
git commit -m "Add WebSocket deposition handler"
git push origin feature/deposition-websocket

# When ready: open PR from feature → dev on GitHub
# Review, merge, delete feature branch

# When dev is stable: open PR from dev → staging
# Test on staging environment

# When staging is verified: open PR from staging → main
# This triggers production deploy
```

---

## Connect Render to GitHub

### Production (main branch)

1. Render Dashboard → casecore-api service → Settings
2. Under "Build & Deploy":
   - **Branch:** `main`
   - **Auto-Deploy:** Yes
3. Every merge to `main` triggers production deploy

### Staging (optional — second Render service)

1. Render Dashboard → New → Web Service
2. Same repo, but:
   - **Name:** `casecore-api-staging`
   - **Branch:** `staging`
   - **Instance Type:** Free (spins down when idle — fine for testing)
3. Add same environment variables but with staging database

---

## Connect Vercel to GitHub

### Production

1. Vercel Dashboard → casecore project → Settings → Git
2. **Production Branch:** `main`
3. **Preview Deployments:** Enabled for all branches
   - Every PR gets a unique preview URL automatically
   - Share preview URLs with attorneys for feedback

### Preview Deployments (free, automatic)

When you push any branch or open a PR, Vercel creates a preview at:
`https://casecore-{branch}-{hash}.vercel.app`

This is incredibly useful:
- Push `feature/new-dashboard` → get a live preview URL
- Share with your attorney team: "Click this link to see the new dashboard"
- No extra cost, no extra config

---

## Working with a Figma Designer via GitHub

The designer does NOT need GitHub access. Here's the workflow:

1. Designer works in Figma, delivers screens
2. You (or your frontend dev) implement in React
3. Code goes into a feature branch → PR → dev → staging → main
4. Designer reviews the Vercel preview URL for their screens
5. Feedback loop happens in Figma comments, not GitHub

If the designer CAN use GitHub (some can):
- Give them read access to the repo
- They can connect Figma Dev Mode to the GitHub repo
- Dev Mode shows which components exist in code vs. need building

---

## Protecting Main Branch

After initial setup, enable branch protection on GitHub:

1. Repository → Settings → Branches → Add rule
2. **Branch name pattern:** `main`
3. Enable:
   - ✅ Require pull request before merging
   - ✅ Require 1 approval (even if it's just you reviewing your own PR)
   - ✅ Require status checks to pass (after you add CI)
   - ✅ Require branches to be up to date before merging
4. This prevents accidental pushes directly to production

---

## Environment Variables by Branch

### Render Production (main)
```
DATABASE_URL=sqlite+aiosqlite:///./data/casecore.db
ENVIRONMENT=production
FRONTEND_URL=https://casecore.vercel.app
```

### Render Staging (staging)
```
DATABASE_URL=sqlite+aiosqlite:///./data/casecore-staging.db
ENVIRONMENT=staging
FRONTEND_URL=https://casecore-staging.vercel.app
```

### Local Development
```
DATABASE_URL=sqlite+aiosqlite:///./casecore.db
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start new feature | `git checkout dev && git checkout -b feature/name` |
| Save progress | `git add . && git commit -m "message"` |
| Push feature | `git push origin feature/name` |
| Deploy to staging | Open PR: dev → staging on GitHub |
| Deploy to production | Open PR: staging → main on GitHub |
| Check what branch you're on | `git branch` |
| See recent commits | `git log --oneline -10` |
| Pull latest | `git pull origin dev` |

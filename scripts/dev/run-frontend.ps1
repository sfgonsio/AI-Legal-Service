# One-command frontend launcher.
# Starts the Vite dev server at casecore-runtime/production/frontend on :5173.
# Assumes npm install has already been run. If node_modules is missing,
# the script runs `npm ci` first.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/run-frontend.ps1

[CmdletBinding()]
param(
    [int]$Port = 5173
)

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$frontendDir = Join-Path $repoRoot 'casecore-runtime\production\frontend'

if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
    Write-Error "frontend package.json not found at: $frontendDir"
    exit 2
}

Write-Host "repo root : $repoRoot"
Write-Host "frontend  : $frontendDir"
Write-Host "port      : $Port"

# Install deps if missing (fast no-op if already installed).
if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
    Write-Host "node_modules missing — running npm ci ..."
    Push-Location $frontendDir
    try {
        & npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed ($LASTEXITCODE)" }
    } finally { Pop-Location }
}

# Vite picks up VITE_* env. If you need the frontend to hit a backend on a
# non-default port, set VITE_API_BASE or similar here.
$env:VITE_API_BASE = $env:VITE_API_BASE

Push-Location $frontendDir
try {
    Write-Host "starting vite on :$Port ..."
    & npm run dev -- --host 127.0.0.1 --port $Port
} finally { Pop-Location }

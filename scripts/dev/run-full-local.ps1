# One-command "both at once" launcher.
# Starts backend in a new PowerShell window, then frontend in a new PowerShell
# window. Windows stay open so you can see logs and Ctrl-C independently.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/run-full-local.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/run-full-local.ps1 -Kill
#
# Then open:
#   http://127.0.0.1:5173               (app shell)
#   http://127.0.0.1:5173/case/1/analysis (Analysis page)
#   http://127.0.0.1:8765/health          (backend health)
#   http://127.0.0.1:8765/legal-library/stats (library stats)

[CmdletBinding()]
param(
    [switch]$Kill,
    [int]$BackendPort = 8765,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$backendScript = Join-Path $PSScriptRoot 'run-backend.ps1'
$frontendScript = Join-Path $PSScriptRoot 'run-frontend.ps1'

$killArg = if ($Kill) { '-Kill' } else { '' }

Write-Host "repo root      : $repoRoot"
Write-Host "backend script : $backendScript"
Write-Host "frontend script: $frontendScript"
Write-Host "backend port   : $BackendPort"
Write-Host "frontend port  : $FrontendPort"
Write-Host ""

# Launch backend in a new window
Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass',
    '-File', $backendScript, '-Port', $BackendPort, $killArg
) -WorkingDirectory $repoRoot | Out-Null

# Wait for backend health before launching frontend, so the UI doesn't render before API is up.
$deadline = (Get-Date).AddSeconds(30)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 1 -ErrorAction Stop
        if ($r.status -eq 'healthy') { $healthy = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 500
}
if ($healthy) {
    Write-Host "backend healthy at http://127.0.0.1:$BackendPort/health"
} else {
    Write-Warning "backend did not report healthy within 30s — starting frontend anyway"
}

# Launch frontend in a new window
Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass',
    '-File', $frontendScript, '-Port', $FrontendPort
) -WorkingDirectory $repoRoot | Out-Null

Write-Host ""
Write-Host "Open in browser:"
Write-Host "  http://127.0.0.1:$FrontendPort/"
Write-Host "  http://127.0.0.1:$FrontendPort/case/1/analysis"
Write-Host "  http://127.0.0.1:$BackendPort/health"
Write-Host "  http://127.0.0.1:$BackendPort/legal-library/stats"

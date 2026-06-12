# One-command backend launcher.
# Starts the FastAPI app at casecore-runtime/production/backend on 127.0.0.1:8765
# (override with $env:DEV_PORT=8766 before invoking).
#
# WHY THIS SCRIPT EXISTS (not a raw `uvicorn main:app --app-dir ...`):
#   - `--app-dir` subtly breaks with `--reload` on Windows: the reload child is
#     spawned without the sys.path entry and fails with
#     "Could not import module 'main'".
#   - `--reload` also leaks zombie sockets on Windows when the process is
#     killed roughly; the parent watcher and worker child can both hold the
#     listening socket, leaving the port "bound by a non-existent PID" in
#     netstat for minutes. This launcher uses non-reload mode to avoid that.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/run-backend.ps1
#
# To restart cleanly after a crash:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev/run-backend.ps1 -Kill
# The script detects and frees port 8765 before binding.

[CmdletBinding()]
param(
    [switch]$Kill,
    [int]$Port = 0
)

if ($Port -eq 0) {
    if ($env:DEV_PORT) { $Port = [int]$env:DEV_PORT } else { $Port = 8765 }
}

$ErrorActionPreference = 'Stop'

# Resolve repo root from script location: scripts/dev/ -> repo root = parent of parent.
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$backendDir = Join-Path $repoRoot 'casecore-runtime\production\backend'
$entrypoint = Join-Path $backendDir 'dev_start_backend.py'

if (-not (Test-Path $entrypoint)) {
    Write-Error "Backend entrypoint not found at: $entrypoint"
    exit 2
}

Write-Host "repo root : $repoRoot"
Write-Host "backend   : $backendDir"
Write-Host "port      : $Port"

# Free the port if anything is already there.
$owners = @()
try {
    $owners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
              Select-Object -ExpandProperty OwningProcess -Unique
} catch { }

if ($owners.Count -gt 0) {
    Write-Host "port $Port currently held by PID(s): $($owners -join ', ')"
    if ($Kill -or $env:DEV_FORCE_KILL -eq '1') {
        foreach ($pid_ in $owners) {
            Write-Host "  taskkill /F /T /PID $pid_"
            & taskkill /F /T /PID $pid_ 2>&1 | Out-Null
        }
        Start-Sleep -Milliseconds 800
    } else {
        Write-Error "Port $Port is in use. Re-run with -Kill to reclaim, or set DEV_PORT to another port."
        exit 3
    }
}

$env:DEV_PORT = [string]$Port
Write-Host "starting backend ..."
# Run in foreground so Ctrl-C cleanly stops the server.
& python $entrypoint

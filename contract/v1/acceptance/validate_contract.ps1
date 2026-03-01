param(
  [string]$Root = "."
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "`nFAIL: $msg" -ForegroundColor Red
  exit 1
}

function Ok($msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

function Warn($msg) {
  Write-Host "WARN: $msg" -ForegroundColor Yellow
}

function Require-File($path) {
  if (!(Test-Path $path)) { Fail "Missing file: $path" }
  $len = (Get-Item $path).Length
  if ($len -le 0) { Fail "Empty file: $path" }
}

function Get-Sha256($path) {
  return (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

# -------------------------
# Paths
# -------------------------
$contractRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$manifest = Join-Path $contractRoot "contract_manifest.yaml"
$roles    = Join-Path $contractRoot "policy/roles.yaml"
$lanes    = Join-Path $contractRoot "policy/lanes.yaml"
$registry = Join-Path $contractRoot "tools/tool_registry.yaml"
$gateway  = Join-Path $contractRoot "tools/tool_gateway_contract.md"
$ddl      = Join-Path $contractRoot "data/postgres_ddl.sql"
$mapdoc   = Join-Path $contractRoot "data/data_model_mappings.md"
$orch     = Join-Path $contractRoot "orchestration/orchestrator_contract.md"

$harnessContract = Join-Path $contractRoot "harness/harness_contract.md"
$sampleToolReq   = Join-Path $contractRoot "harness/sample_payloads/tool_request.json"
$runHarnessPy    = Join-Path $contractRoot "harness/run_harness.py"

# -------------------------
# 1) Required files
# -------------------------
Require-File $manifest
Require-File $roles
Require-File $lanes
Require-File $registry
Require-File $gateway
Require-File $ddl
Require-File $mapdoc
Require-File $orch
Require-File $harnessContract
Require-File $sampleToolReq
Require-File $runHarnessPy
Ok "Required SSOT files exist and are non-empty"

# -------------------------
# 2) Single manifest enforcement
# -------------------------
$manifests = Get-ChildItem -Path $contractRoot -Recurse -Filter "contract_manifest.yaml" -File

if ($manifests.Count -eq 0) { Fail "No contract_manifest.yaml found under /contract" }
if ($manifests.Count -ne 1) { Fail "Expected exactly 1 contract_manifest.yaml, found $($manifests.Count)" }

Ok "Exactly one contract_manifest.yaml"

# -------------------------
# 3) Gateway encoding sanity
# -------------------------
$gwText = Get-Content $gateway -Raw
$replacementChar = [char]0xFFFD
if ($gwText.Contains("â") -or $gwText.Contains($replacementChar)) {
  Fail "tool_gateway_contract.md encoding corrupted."
}
Ok "Tool gateway contract encoding looks clean"

# -------------------------
# 4) Load raw docs
# -------------------------
$lanesText = Get-Content $lanes -Raw
$rolesText = Get-Content $roles -Raw
$regText   = Get-Content $registry -Raw
$ddlText   = Get-Content $ddl -Raw
$manText   = Get-Content $manifest -Raw

# -------------------------
# 5) Manifest path enforcement
# -------------------------
$pathRegex = [regex]'(?<![A-Za-z0-9_\-])\./[A-Za-z0-9_\-./]+'
$rawRefs = @($pathRegex.Matches($manText) | ForEach-Object { $_.Value.Trim() } | Sort-Object -Unique)

if ($rawRefs.Length -lt 5) {
  Fail "Too few manifest path references detected."
}

foreach ($rp in $rawRefs) {
  $relative = ($rp -replace '^\./','')
  $full = Join-Path $contractRoot $relative

  $fullResolved = Resolve-Path -LiteralPath $full -ErrorAction SilentlyContinue
  if ($null -eq $fullResolved) {
    Fail "Manifest reference missing on disk: $rp"
  }

  $fullResolvedStr = $fullResolved.Path
  $contractResolved = (Resolve-Path $contractRoot).Path

  if (-not $fullResolvedStr.StartsWith($contractResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    Fail "Manifest reference escapes contract root: $rp"
  }
}
Ok "All manifest './...' references exist and stay within contract/v1"

# -------------------------
# 6) Lanes audit table enforcement
# -------------------------
if ($lanesText -match "audit_events") {
  Fail "lanes.yaml references audit_events; canonical table is audit_ledger."
}
Ok "No audit_events drift in lanes.yaml"

# -------------------------
# 7) Required tables in DDL
# -------------------------
$requiredTables = @(
  "CREATE TABLE IF NOT EXISTS runs",
  "CREATE TABLE IF NOT EXISTS audit_ledger",
  "CREATE TABLE IF NOT EXISTS artifacts",
  "CREATE TABLE IF NOT EXISTS export_bundles",
  "CREATE TABLE IF NOT EXISTS transcripts",
  "CREATE TABLE IF NOT EXISTS interview_notes",
  "CREATE TABLE IF NOT EXISTS entities",
  "CREATE TABLE IF NOT EXISTS facts",
  "CREATE TABLE IF NOT EXISTS evidence_map",
  "CREATE TABLE IF NOT EXISTS coa_map",
  "CREATE TABLE IF NOT EXISTS shared_playbooks",
  "CREATE TABLE IF NOT EXISTS shared_heuristics",
  "CREATE TABLE IF NOT EXISTS override_events"
)

foreach ($needle in $requiredTables) {
  if ($ddlText -notmatch [regex]::Escape($needle)) {
    Fail "DDL missing required clause: $needle"
  }
}
Ok "DDL contains all required tables"

# -------------------------
# 8) Lane tools exist
# -------------------------
$toolRegex = [regex]'(?m)^\s*-\s*(?<t>[a-z0-9_]+\.[a-z0-9_.]+)\s*$'
$laneTools = @($toolRegex.Matches($lanesText) | ForEach-Object { $_.Groups["t"].Value.Trim() } | Sort-Object -Unique)

foreach ($t in $laneTools) {
  if ($regText -notmatch ("(?m)^\s*-\s*tool_name:\s*" + [regex]::Escape($t) + "\s*$")) {
    Fail "Tool in lanes.yaml not found in registry: $t"
  }
}
Ok "All lane tools exist in registry"

# -------------------------
# 9) Lane roles exist
# -------------------------
$laneRoleRegex = [regex]'roles:\s*\[(?<list>[^\]]+)\]'
$laneRoles = @()

foreach ($m in $laneRoleRegex.Matches($lanesText)) {
  $laneRoles += ($m.Groups["list"].Value -split ",") | ForEach-Object { $_.Trim() }
}

$laneRoles = @($laneRoles | Sort-Object -Unique)

foreach ($r in $laneRoles) {
  if ($rolesText -notmatch ("(?m)^\s*-\s*role_id:\s*" + [regex]::Escape($r) + "\s*$")) {
    Fail "Role in lanes.yaml not found in roles.yaml: $r"
  }
}
Ok "All lane roles exist"

# -------------------------
# 10) Hash enforcement
# -------------------------
if ($manText -match '(?m)^\s*enabled:\s*true\s*$') {

  $hashRegex = [regex]'(?m)^\s*"\./(?<p>[^"]+)"\s*:\s*"(?<h>[a-fA-F0-9]{64})"\s*$'
  $hashMatches = $hashRegex.Matches($manText)

  if ($hashMatches.Count -eq 0) {
    Fail "Hash enforcement enabled but no hashes found."
  }

  foreach ($m in $hashMatches) {
    $p = $m.Groups["p"].Value
    $expected = $m.Groups["h"].Value.ToLowerInvariant()
    $full = Join-Path $contractRoot $p

    if (!(Test-Path $full)) { Fail "Hash listed for missing file: ./$( $p )" }

    $actual = Get-Sha256 $full
    if ($actual -ne $expected) {
      Fail "Hash drift detected for ./$( $p )"
    }
  }

  Ok "Manifest hash enforcement passed"
}
else {
  Ok "Manifest hash enforcement disabled"
}

# -------------------------
# Stage 13.5 Overlay Structural Validation
# -------------------------
Write-Host "Stage 13.5 overlay pack structural validation..." -ForegroundColor Cyan

$overlayRegex = [regex]'(?m)^\s*-\s*"\./(?<p>overlays/interview/[^"]+\.ya?ml)"\s*$'
$overlayPaths = @($overlayRegex.Matches($manText) | ForEach-Object { $_.Groups["p"].Value.Trim() } | Sort-Object -Unique)

if ($overlayPaths.Length -eq 0) {
  Warn "No interview overlay packs found in manifest."
}
else {

  $requiredAnchors = @(
    "overlay_id:",
    "overlay_type:",
    "version:",
    "status:",
    "metadata:",
    "triggers:",
    "question_additions:",
    "mappings:",
    "priority_rules:"
  )

  foreach ($relPath in $overlayPaths) {

    $fullPath = Join-Path $contractRoot $relPath
    if (!(Test-Path $fullPath)) {
      Fail "Overlay listed in manifest missing: ./$( $relPath )"
    }

    $text = Get-Content -Raw $fullPath

    foreach ($a in $requiredAnchors) {
      if ($text -notmatch [regex]::Escape($a)) {
        Fail "Overlay missing required anchor '$a' in ./$( $relPath )"
      }
    }

    if ($text -notmatch '(?m)^\s*overlay_type:\s*interview_overlay_pack\s*$') {
      Fail "Invalid overlay_type in ./$( $relPath )"
    }

    if ($text -notmatch '(?m)^\s*status:\s*(active|deprecated|disabled)\s*$') {
      Fail "Invalid status in ./$( $relPath )"
    }
  }

  Ok "Stage 13.5 overlay pack structural validation passed"
}

# -------------------------
# Stage 14 Replay (opt-in)
# -------------------------
Write-Host "Stage 14 replay equivalence verification (opt-in)..." -ForegroundColor Cyan

if ($env:RUN_STAGE14_REPLAY -eq "1") {

  $replayRunner  = Join-Path $contractRoot "harness\run_replay.py"
  $replayVectors = Join-Path $contractRoot "harness\replay_vectors"

  if (!(Test-Path $replayRunner))  { Fail "Missing replay runner." }
  if (!(Test-Path $replayVectors)) { Fail "Missing replay vectors dir." }

  & python $replayRunner --contract_root $contractRoot --vectors_dir $replayVectors
  if ($LASTEXITCODE -ne 0) { Fail "Stage 14 replay equivalence failed." }

  Ok "Stage 14 replay equivalence passed"
}
else {
  Warn "Stage 14 SKIPPED. Set RUN_STAGE14_REPLAY=1 to enforce."
}

Write-Host "`nALL CHECKS PASSED ✅" -ForegroundColor Cyan
exit 0
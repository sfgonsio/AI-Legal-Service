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
# Paths (ALWAYS Root-relative)
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
$runHarnessPy     = Join-Path $contractRoot "harness/run_harness.py"

# -------------------------
# 1) Required SSOT files exist and non-empty
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
# 2) Exactly one manifest in /contract tree
# -------------------------
$manifests = @(
  Get-ChildItem -Path $contractRoot -Recurse -Filter "contract_manifest.yaml" -File -ErrorAction SilentlyContinue
)

if ($manifests.Count -eq 0) {
  Fail "No contract_manifest.yaml found under /contract"
}

if ($manifests.Count -ne 1) {
  Fail "Expected exactly 1 contract_manifest.yaml, found $($manifests.Count)"
}

Ok "Exactly one contract_manifest.yaml"

# -------------------------
# 3) Tool gateway encoding sanity (no mojibake)
# -------------------------
$gwText = Get-Content $gateway -Raw

# Detect common UTF-8->CP1252 mojibake and Unicode replacement char
$replacementChar = [char]0xFFFD
if ($gwText.Contains("â") -or $gwText.Contains($replacementChar)) {
  Fail "tool_gateway_contract.md appears encoding-corrupted (found mojibake 'â' or Unicode replacement char)."
}
Ok "Tool gateway contract encoding looks clean"

# -------------------------
# 4) Load core docs (raw)
# -------------------------
$lanesText = Get-Content $lanes -Raw
$rolesText = Get-Content $roles -Raw
$regText   = Get-Content $registry -Raw
$ddlText   = Get-Content $ddl -Raw
$manText   = Get-Content $manifest -Raw

# -------------------------
# 5) Gate 6 SSOT enforcement:
#    Every manifest-relative path "./..." must resolve under contract/v1 and exist.
# -------------------------
$pathRegex = [regex]'(?<![A-Za-z0-9_\-])\./[A-Za-z0-9_\-./]+'
$rawRefs = @()
foreach ($m in $pathRegex.Matches($manText)) {
  $rawRefs += $m.Value.Trim()
}
$rawRefs = $rawRefs | Sort-Object -Unique

if ($rawRefs.Count -lt 5) {
  Fail "Too few manifest path references detected. Expected multiple './...' entries. Check contract_manifest.yaml formatting."
}

foreach ($rp in $rawRefs) {
  $relative = ($rp -replace '^\./','')
  $full = Join-Path $contractRoot $relative

  $fullResolved = (Resolve-Path -LiteralPath $full -ErrorAction SilentlyContinue)
  if ($null -eq $fullResolved) {
    Fail "Manifest reference missing on disk: $rp -> $full"
  }

  $fullResolvedStr = $fullResolved.Path
  $contractResolved = (Resolve-Path -LiteralPath $contractRoot).Path
  if (-not $fullResolvedStr.StartsWith($contractResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    Fail "Manifest reference resolves outside contract/v1 (forbidden): $rp -> $fullResolvedStr"
  }
}
Ok "All manifest './...' references exist on disk and stay within contract/v1"

# -------------------------
# 6) Lanes must not reference audit_events (canonical is audit_ledger)
# -------------------------
if ($lanesText -match "audit_events") { Fail "lanes.yaml references audit_events; canonical table is audit_ledger." }
Ok "No audit_events drift in lanes.yaml"

# -------------------------
# 7) DDL must include required tables (string-level checks)
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
  if ($ddlText -notmatch [regex]::Escape($needle)) { Fail "DDL missing required clause: $needle" }
}
Ok "DDL contains all required tables (string check)"

# -------------------------
# 8) Tools referenced by lanes must exist in tool registry
# -------------------------
$toolLineRegex = [regex]'(?m)^\s*-\s*(?<t>[a-z0-9_]+\.[a-z0-9_.]+)\s*$'
$laneTools = @()
foreach ($m in $toolLineRegex.Matches($lanesText)) {
  $laneTools += $m.Groups["t"].Value.Trim()
}
$laneTools = $laneTools | Sort-Object -Unique

if ($laneTools.Count -eq 0) { Fail "No tools detected in lanes.yaml (expected tool lists under allowed_actions.tools)." }

foreach ($t in $laneTools) {
  if ($regText -notmatch ("(?m)^\s*-\s*tool_name:\s*" + [regex]::Escape($t) + "\s*$")) {
    Fail "Tool referenced in lanes.yaml not found in tool_registry.yaml: $t"
  }
}
Ok "All lane tools exist in tool registry"

# -------------------------
# 9) Roles referenced by lanes must exist in roles.yaml
# -------------------------
$laneRoleRegex = [regex]'roles:\s*\[(?<list>[^\]]+)\]'
$laneRoles = @()
foreach ($m in $laneRoleRegex.Matches($lanesText)) {
  $inside = $m.Groups["list"].Value
  $laneRoles += ($inside -split ",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
}
$laneRoles = $laneRoles | Sort-Object -Unique

foreach ($r in $laneRoles) {
  if ($rolesText -notmatch ("(?m)^\s*-\s*role_id:\s*" + [regex]::Escape($r) + "\s*$")) {
    Fail "Role referenced in lanes.yaml not found in roles.yaml: $r"
  }
}
Ok "All lane roles exist in roles.yaml"

# -------------------------
# 10) Hash enforcement (Gate 6 "No drift")
# -------------------------
if ($manText -match '(?m)^\s*enabled:\s*true\s*$') {
  $hashEntryRegex = [regex]'(?m)^\s*"\./(?<p>[^"]+)"\s*:\s*"(?<h>[a-fA-F0-9]{64})"\s*$'
  $hashes = @{}
  foreach ($m in $hashEntryRegex.Matches($manText)) {
    $hashes[$m.Groups["p"].Value] = $m.Groups["h"].Value.ToLowerInvariant()
  }

  if ($hashes.Count -eq 0) {
    Fail "Hash enforcement enabled but no hashes detected in manifest under integrity.file_hashes.hashes"
  }

  foreach ($k in $hashes.Keys) {
    $full = Join-Path $contractRoot $k
    if (!(Test-Path $full)) { Fail "Hash listed for missing file: ./$( $k )" }
    $actual = Get-Sha256 $full
    $expected = $hashes[$k]
    if ($actual -ne $expected) {
      Fail "Hash drift detected for ./$( $k ): expected $expected, got $actual"
    }
  }

  Ok "Manifest hash enforcement passed (no drift)"
} else {
  Ok "Manifest hash enforcement is disabled (integrity.file_hashes.enabled != true)"
}

# -------------------------
# Stage 12: Determinism & fingerprint enforcement (string checks)
# -------------------------
$fpYaml = Join-Path $contractRoot "orchestration\run_identity_fingerprints.yaml"
$fpMd   = Join-Path $contractRoot "orchestration\determinism_integrity_contract.md"

if (-not (Test-Path $fpYaml)) { Fail "Missing required determinism SSOT: $fpYaml" }
if (-not (Test-Path $fpMd))   { Fail "Missing required determinism contract: $fpMd" }

$fpText = Get-Content -Raw $fpYaml
$requiredAnchors = @(
  "inputs_fingerprint:",
  "run_fingerprint:",
  "artifact_metadata_requirements:",
  "required_on_all_canonical_artifacts:",
  "no_mixed_run_answers:",
  "algorithm: sha256"
)

foreach ($a in $requiredAnchors) {
  if ($fpText -notmatch [regex]::Escape($a)) {
    Fail "Determinism SSOT missing anchor: $a"
  }
}

Write-Host "OK: Determinism fingerprint SSOT present and well-formed (anchor checks)" -ForegroundColor Green

# -------------------------
# Stage 14: Deterministic Replay Equivalence (executably verifiable)
#   - Local dev default: SKIP (opt-in)
#   - CI: set RUN_STAGE14_REPLAY=1 to enforce
# -------------------------
Write-Host "Stage 14 replay equivalence verification (opt-in)..." -ForegroundColor Cyan

$runReplay = ($env:RUN_STAGE14_REPLAY -eq "1")
if (-not $runReplay) {
  Warn "Stage 14 SKIPPED. To enforce replay equivalence, set environment variable RUN_STAGE14_REPLAY=1."
} else {
  Write-Host "Running Stage 14 replay equivalence verification..." -ForegroundColor Cyan

  $contractRoot2 = Join-Path $PSScriptRoot ".." | Resolve-Path
  $contractRoot2 = $contractRoot2.Path

  $replayRunner  = Join-Path $contractRoot2 "harness\run_replay.py"
  $replayVectors = Join-Path $contractRoot2 "harness\replay_vectors"

  if (!(Test-Path $replayRunner))  { Fail "Missing replay runner: $replayRunner" }
  if (!(Test-Path $replayVectors)) { Fail "Missing replay vectors dir: $replayVectors" }

  # Capture output for visibility in CI logs
  $output = & python $replayRunner --contract_root $contractRoot2 --vectors_dir $replayVectors 2>&1
  $exit = $LASTEXITCODE

  if ($output) { Write-Host $output }

  if ($exit -ne 0) {
    Fail "Stage 14 replay equivalence failed (exit=$exit). If contract artifacts changed, update replay vectors or rerun vector generation."
  }

  Write-Host "OK: Stage 14 replay equivalence passed (canonical outputs match)" -ForegroundColor Green
}

Write-Host "`nALL CHECKS PASSED ✅" -ForegroundColor Cyan
exit 0
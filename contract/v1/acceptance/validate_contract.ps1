param(
  [string]$Root = "."
)

Set-StrictMode -Version Latest
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
  if (!(Test-Path -LiteralPath $path)) { Fail "Missing file: $path" }
  $len = (Get-Item -LiteralPath $path).Length
  if ($len -le 0) { Fail "Empty file: $path" }
}

function Get-Sha256($path) {
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Normalize-ManifestRelPath([string]$rel) {
  # Input examples:
  #   contract/v1/agents/x.md
  #   agents/x.md
  # Output should be contractRoot-relative (since $contractRoot is already .../contract/v1)
  $p = $rel.Trim()
  $p = $p -replace "\\", "/"
  if ($p -like "contract/v1/*") {
    $p = $p.Substring("contract/v1/".Length)
  }
  return ($p -replace "/", "\")
}

# -------------------------
# Paths
# -------------------------
# $PSScriptRoot points to contract/v1/acceptance
# contract root => contract/v1
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

$caseConfig      = Join-Path $contractRoot "config\case_config.yaml"

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
Require-File $caseConfig
Ok "Required SSOT files exist and are non-empty"

# -------------------------
# 2) Single manifest enforcement
# -------------------------
$manifests = @(Get-ChildItem -Path $contractRoot -Recurse -Filter "contract_manifest.yaml" -File)

if ($manifests.Count -eq 0) { Fail "No contract_manifest.yaml found under /contract" }
if ($manifests.Count -ne 1) { Fail "Expected exactly 1 contract_manifest.yaml, found $($manifests.Count)" }

Ok "Exactly one contract_manifest.yaml"

# -------------------------
# 3) Gateway encoding sanity
# -------------------------
$gwText = Get-Content -LiteralPath $gateway -Raw
$replacementChar = [char]0xFFFD
if ($gwText.Contains("â") -or $gwText.Contains($replacementChar)) {
  Fail "tool_gateway_contract.md encoding corrupted."
}
Ok "Tool gateway contract encoding looks clean"

# -------------------------
# 4) Load raw docs
# -------------------------
$lanesText = Get-Content -LiteralPath $lanes -Raw
$rolesText = Get-Content -LiteralPath $roles -Raw
$regText   = Get-Content -LiteralPath $registry -Raw
$ddlText   = Get-Content -LiteralPath $ddl -Raw
$manText   = Get-Content -LiteralPath $manifest -Raw
$cfgText   = Get-Content -LiteralPath $caseConfig -Raw

# -------------------------
# 5) Manifest path enforcement
# -------------------------
# Detect ./... references anywhere in manifest text
$pathRegex = [regex]'(?<![A-Za-z0-9_\-])\./[A-Za-z0-9_\-./]+'
$rawRefs = @(
  $pathRegex.Matches($manText) |
    ForEach-Object { $_.Value.Trim() } |
    Sort-Object -Unique
)

if ($rawRefs.Length -lt 5) {
  Fail "Too few manifest path references detected."
}

foreach ($rp in $rawRefs) {
  $relative = ($rp -replace '^\./','')
  $relative = Normalize-ManifestRelPath $relative

  $full = Join-Path $contractRoot $relative
  $fullResolved = Resolve-Path -LiteralPath $full -ErrorAction SilentlyContinue
  if ($null -eq $fullResolved) {
    Fail "Manifest reference missing on disk: $rp (resolved: $full)"
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
$laneTools = @(
  $toolRegex.Matches($lanesText) |
    ForEach-Object { $_.Groups["t"].Value.Trim() } |
    Sort-Object -Unique
)

if ($laneTools.Length -eq 0) { Fail "No tools detected in lanes.yaml." }

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
  $laneRoles += ($m.Groups["list"].Value -split ",") |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -ne "" }
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

  # Support BOTH:
  #   "./path": "hash"
  #   ./path: "hash"
  # Captures p without leading "./"
  $hashRegex = [regex]'(?m)^\s*("?)(\./(?<p>[A-Za-z0-9_\-./]+))\1\s*:\s*"(?<h>[a-fA-F0-9]{64})"\s*$'
  $hashMatches = $hashRegex.Matches($manText)

  if ($hashMatches.Count -eq 0) {
    Fail "Hash enforcement enabled but no hashes found."
  }

  foreach ($m in $hashMatches) {
    $pRaw = $m.Groups["p"].Value
    $expected = $m.Groups["h"].Value.ToLowerInvariant()

    $p = Normalize-ManifestRelPath $pRaw
    $full = Join-Path $contractRoot $p

    if (!(Test-Path -LiteralPath $full)) {
      Fail "Hash listed for missing file: ./$( $pRaw ) (resolved: $full)"
    }

    $actual = Get-Sha256 $full
    if ($actual -ne $expected) {
      Fail "Hash drift detected for ./$( $pRaw )"
    }
  }

  Ok "Manifest hash enforcement passed"
}
else {
  Ok "Manifest hash enforcement disabled"
}

# -------------------------
# Stage 13.5 Overlay Structural Validation (manifest-driven)
# -------------------------
Write-Host "Stage 13.5 overlay pack structural validation..." -ForegroundColor Cyan

$overlayRegex = [regex]'(?m)^\s*-\s*"\./(?<p>overlays/interview/[^"]+\.ya?ml)"\s*$'
$overlayPaths = @(
  $overlayRegex.Matches($manText) |
    ForEach-Object { $_.Groups["p"].Value.Trim() } |
    Sort-Object -Unique
)

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

    $fullPath = Join-Path $contractRoot ($relPath -replace "/", "\")
    if (!(Test-Path -LiteralPath $fullPath)) {
      Fail "Overlay listed in manifest missing: ./$( $relPath )"
    }

    $text = Get-Content -LiteralPath $fullPath -Raw

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
# Stage 13.6 Config Binding Enforcement (case_config.yaml ↔ manifest ↔ overlays ↔ schemas)
# -------------------------
Write-Host "Stage 13.6 config binding enforcement..." -ForegroundColor Cyan

# 13.6A: case_config must contain interview + overlays blocks
if ($cfgText -notmatch '(?m)^\s*interview:\s*$') {
  Fail "case_config.yaml missing required top-level block: interview:"
}
if ($cfgText -notmatch '(?m)^\s*overlays:\s*$') {
  Fail "case_config.yaml missing required block under interview: overlays:"
}

# 13.6B: Extract overlay_ids from case_config.yaml under interview.overlays
$cfgOverlayIdRegex = [regex]'(?m)^\s*-\s*overlay_id:\s*(?<id>[A-Za-z0-9_\-\.]+)\s*$'
$cfgOverlayIds = @(
  $cfgOverlayIdRegex.Matches($cfgText) |
    ForEach-Object { $_.Groups["id"].Value.Trim() } |
    Where-Object { $_ -ne "" }
)

if ($cfgOverlayIds.Length -eq 0) {
  Fail "case_config.yaml interview.overlays contains no overlay_id entries"
}

# No duplicates
$dupes = @($cfgOverlayIds | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
if ($dupes.Length -gt 0) {
  Fail "case_config.yaml contains duplicate overlay_id(s): $($dupes -join ', ')"
}

# 13.6C: Ensure each overlay_id maps to an overlay file and is listed in manifest
foreach ($oid in $cfgOverlayIds) {

  $expectedRel = "overlays/interview/$oid.yaml"
  $expectedAbs = Join-Path $contractRoot ($expectedRel -replace "/", "\")

  if (-not (Test-Path -LiteralPath $expectedAbs)) {
    Fail "case_config.yaml references overlay_id '$oid' but expected overlay file is missing: ./$( $expectedRel )"
  }

  # Must be referenced in manifest as authoritative inventory (expects quotes)
  $needle = '"./' + [regex]::Escape($expectedRel) + '"'
  if ($manText -notmatch $needle) {
    Fail "Overlay file for overlay_id '$oid' exists but is not listed in contract_manifest.yaml authoritative_files (missing: ./$expectedRel)"
  }

  # Overlay file must contain matching overlay_id:
  $ovText = Get-Content -LiteralPath $expectedAbs -Raw
  $ovIdMatch = [regex]::Match($ovText, '(?m)^\s*overlay_id:\s*(?<id>[A-Za-z0-9_\-\.]+)\s*$')
  if (-not $ovIdMatch.Success) {
    Fail "Overlay file ./$expectedRel missing overlay_id: header"
  }
  $ovId = $ovIdMatch.Groups["id"].Value.Trim()
  if ($ovId -ne $oid) {
    Fail "Overlay file ./$expectedRel overlay_id mismatch: case_config=$oid, file=$ovId"
  }

  # Require at least one enabled: line exists in config.
  if ($cfgText -notmatch '(?m)^\s*enabled:\s*(true|false)\s*$') {
    Fail "case_config.yaml missing required enabled: true|false entries under interview.overlays"
  }
}

# 13.6D: Ensure required schemas are in manifest inventory (prevents silent schema drift)
$requiredSchemaRefs = @(
  "./schemas/interview/case_strategy_mode.schema.json",
  "./schemas/interview/element_completeness_matrix.schema.json",
  "./schemas/interview/risk_flag_register.schema.json",
  "./schemas/overlays/interview_overlay_pack.schema.json"
)

foreach ($sr in $requiredSchemaRefs) {
  if ($manText -notmatch [regex]::Escape('"' + $sr + '"')) {
    Fail "contract_manifest.yaml missing required schema reference: $sr"
  }
}

Ok "Stage 13.6 config binding enforcement passed"

# -------------------------
# Stage 14 Replay (opt-in)
# -------------------------
Write-Host "Stage 14 replay equivalence verification (opt-in)..." -ForegroundColor Cyan

if ($env:RUN_STAGE14_REPLAY -eq "1") {

  $replayRunner  = Join-Path $contractRoot "harness\run_replay.py"
  $replayVectors = Join-Path $contractRoot "harness\replay_vectors"

  if (!(Test-Path -LiteralPath $replayRunner))  { Fail "Missing replay runner." }
  if (!(Test-Path -LiteralPath $replayVectors)) { Fail "Missing replay vectors dir." }

  & python $replayRunner --contract_root $contractRoot --vectors_dir $replayVectors
  if ($LASTEXITCODE -ne 0) { Fail "Stage 14 replay equivalence failed." }

  Ok "Stage 14 replay equivalence passed"
}
else {
  Warn "Stage 14 SKIPPED. Set RUN_STAGE14_REPLAY=1 to enforce."
}

Write-Host "`nALL CHECKS PASSED ✅" -ForegroundColor Cyan
exit 0
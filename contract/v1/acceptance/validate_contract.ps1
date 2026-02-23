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

function Require-File($path) {
  if (!(Test-Path $path)) { Fail "Missing file: $path" }
  $len = (Get-Item $path).Length
  if ($len -le 0) { Fail "Empty file: $path" }
}

# -------------------------
# Paths
# -------------------------
$manifest = Join-Path $Root "contract/v1/contract_manifest.yaml"
$roles    = Join-Path $Root "contract/v1/policy/roles.yaml"
$lanes    = Join-Path $Root "contract/v1/policy/lanes.yaml"
$registry = Join-Path $Root "contract/v1/tools/tool_registry.yaml"
$gateway  = Join-Path $Root "contract/v1/tools/tool_gateway_contract.md"
$ddl      = Join-Path $Root "contract/v1/data/postgres_ddl.sql"
$mapdoc   = Join-Path $Root "contract/v1/data/data_model_mappings.md"
$orch     = Join-Path $Root "contract/v1/orchestration/orchestrator_contract.md"

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
Ok "Required SSOT files exist and are non-empty"

# -------------------------
# 2) Exactly one manifest in /contract tree
# -------------------------
$manifests = Get-ChildItem (Join-Path $Root "contract") -Filter "contract_manifest.yaml" -Recurse
if ($manifests.Count -ne 1) { Fail "Expected exactly 1 contract_manifest.yaml, found $($manifests.Count)" }
Ok "Exactly one contract_manifest.yaml"

# -------------------------
# 3) Tool gateway encoding sanity (no mojibake)
$gwText = Get-Content $gateway -Raw

# Conservative, codepage-safe detection:
# - 'â' catches common UTF-8→CP1252 corruption sequences (â€ â€™ â€œ â€� â€” â€“ â€¢ â†’ etc.)
# - '�' catches Unicode replacement character
if ($gwText.Contains("â") -or $gwText.Contains("�")) {
  Fail "tool_gateway_contract.md appears encoding-corrupted (found 'â' or '�')."
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
# 5) Manifest references exist on disk (simple path extraction)
#    Looks for values like "./policy/roles.yaml"
# -------------------------
$refPaths = @()
$regex = [regex]'(?m)^\s*(roles|lanes|policy_versioning)\s*:\s*"(?<p>\./[^"]+)"\s*$'
foreach ($m in $regex.Matches($manText)) {
  $refPaths += $m.Groups["p"].Value
}
if ($refPaths.Count -lt 2) { Fail "Manifest governance references not detected (roles/lanes). Check contract_manifest.yaml." }

foreach ($rp in $refPaths) {
  $full = Join-Path (Join-Path $Root "contract/v1") ($rp -replace "^\./","")
  if (!(Test-Path $full)) { Fail "Manifest reference missing on disk: $rp -> $full" }
}
Ok "Manifest governance references resolve on disk"

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
#    Extract tool lines under allowed_actions.tools by regex pattern.
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

Write-Host "`nALL CHECKS PASSED ✅" -ForegroundColor Cyan
exit 0


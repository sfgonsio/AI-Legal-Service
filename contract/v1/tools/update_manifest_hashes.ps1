param(
  [string]$Root = ".",
  [switch]$AllowOverwriteIntegrity,
  [switch]$ForceFixRoles
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
  Write-Host "`nFAIL: $msg" -ForegroundColor Red
  exit 1
}

function Ok($msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

function Sha256Lower($path) {
  return (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$contractRoot = Join-Path $Root "contract/v1"
$manifestPath = Join-Path $contractRoot "contract_manifest.yaml"
$rolesPath    = Join-Path $contractRoot "policy/roles.yaml"

if (!(Test-Path $manifestPath)) { Fail "Missing: $manifestPath" }
if (!(Test-Path $rolesPath))    { Fail "Missing: $rolesPath" }

# -------------------------------------------------------------------
# Safety: detect 'roles.yaml' accidentally containing manifest content
# -------------------------------------------------------------------
$rolesText = Get-Content $rolesPath -Raw
$rolesLooksWrong = ($rolesText -match "(?m)^\s*contract:\s*$") -or ($rolesText -notmatch "(?m)^\s*roles:\s*$")

if ($rolesLooksWrong) {
  if ($ForceFixRoles) {
    Write-Host "roles.yaml looks wrong. Overwriting with canonical roles template (-ForceFixRoles set)." -ForegroundColor Yellow

@'
version: v1
contract_version: v1
last_updated: 2026-02-23

roles:
  - role_id: SYSTEM
    description: "Internal platform services (scheduler, audit writer, run state transitions)."
    class: system
    privileges:
      lanes: []

  - role_id: GOVERNANCE_AGENT
    description: "Manages policy enforcement and knowledge promotion workflows."
    class: system
    privileges:
      lanes:
        - PROMOTE_SHARED_KNOWLEDGE

  - role_id: INTERVIEW_AGENT
    description: "Conducts client interviews and captures narrative input."
    class: agent
    privileges:
      lanes:
        - TOOL_INTERVIEW_CAPTURE
        - WRITE_INTAKE_ARTIFACTS

  - role_id: INTAKE_AGENT
    description: "Processes intake materials and prepares structured case data."
    class: agent
    privileges:
      lanes:
        - WRITE_INTAKE_ARTIFACTS

  - role_id: MAPPING_AGENT
    description: "Maps facts and evidence to causes of action."
    class: agent
    privileges:
      lanes:
        - WRITE_MAPPING_OUTPUTS

  - role_id: ATTORNEY_ADMIN
    description: "Human authority with approval and override powers."
    class: human
    privileges:
      lanes:
        - PROMOTE_SHARED_KNOWLEDGE
        - EXPORT_CASE_DATA
        - SYSTEM_OVERRIDE
'@ | Set-Content -Encoding UTF8 $rolesPath

    Ok "roles.yaml repaired"
  } else {
    Fail "roles.yaml appears corrupted/wrong (e.g., contains 'contract:' or missing 'roles:'). Re-run with -ForceFixRoles to auto-repair."
  }
}

# -------------------------------------------------------------------
# Read manifest and extract authoritative_files entries
# -------------------------------------------------------------------
$manText = Get-Content $manifestPath -Raw

# Extract lines like: - "./policy/roles.yaml"
$authRegex = [regex]'(?m)^\s*-\s*"\./(?<p>[^"]+)"\s*$'
$authRel = @()
foreach ($m in $authRegex.Matches($manText)) {
  $authRel += $m.Groups["p"].Value.Trim()
}
$authRel = $authRel | Sort-Object -Unique

if ($authRel.Count -eq 0) {
  Fail "No authoritative_files entries found (expected lines like: - ""./policy/roles.yaml"") in $manifestPath"
}

# -------------------------------------------------------------------
# Compute hashes
# -------------------------------------------------------------------
$hashLines = @()
foreach ($rel in $authRel) {
  $full = Join-Path $contractRoot $rel
  if (!(Test-Path $full)) { Fail "Manifest authoritative file missing on disk: ./$( $rel ) -> $full" }
  $h = Sha256Lower $full
  $hashLines += "      ""./$rel"": ""$h"""
}

# -------------------------------------------------------------------
# Replace or append integrity block
# -------------------------------------------------------------------
$integrityBlock = @"
integrity:
  file_hashes:
    enabled: true
    algorithm: "sha256"
    hashes:
$($hashLines -join "`n")
"@

# If integrity block exists, replace it; otherwise append
$hasIntegrity = ($manText -match "(?m)^\s*integrity:\s*$")

if ($hasIntegrity) {
  if (-not $AllowOverwriteIntegrity) {
    Fail "Manifest already contains an integrity: block. Re-run with -AllowOverwriteIntegrity to rewrite it deterministically."
  }

  # Replace from line starting with 'integrity:' to end of file (simple, deterministic)
  $newText = [regex]::Replace($manText, '(?ms)^\s*integrity:\s*.*\z', $integrityBlock.TrimEnd() + "`n")
  Set-Content -Encoding UTF8 -Path $manifestPath -Value $newText
  Ok "Rewrote existing integrity.file_hashes block"
} else {
  $newText = $manText.TrimEnd() + "`n`n" + $integrityBlock.TrimEnd() + "`n"
  Set-Content -Encoding UTF8 -Path $manifestPath -Value $newText
  Ok "Appended integrity.file_hashes block"
}

Write-Host "`nDONE ✅ Manifest hashes updated for $($authRel.Count) file(s)." -ForegroundColor Cyan
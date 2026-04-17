$ErrorActionPreference = "Stop"

$repoRoot  = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$specRoot  = Join-Path $repoRoot "casecore-spec"
$buildRoot = Join-Path $repoRoot "casecore-build-kit"

Write-Host "=== CASECORE INTEGRATED CONSISTENCY AUDIT ===" -ForegroundColor Cyan

# -----------------------------
# 1. Required authoritative files
# -----------------------------
$requiredSpec = @(
    (Join-Path $specRoot "README.md"),
    (Join-Path $specRoot "docs\architecture\BUILD_SPEC.md"),
    (Join-Path $specRoot "docs\governance\INTEGRATION_CONTRACT.md"),
    (Join-Path $specRoot "docs\governance\RUNTIME_ENFORCEMENT_POLICY.md"),
    (Join-Path $specRoot "packages\contracts\manifest\contract_manifest.yaml"),
    (Join-Path $specRoot "validators\run_all_validations.ps1"),
    (Join-Path $specRoot "validators\runtime\validate_runtime_output.ps1")
)

foreach ($p in $requiredSpec) {
    if (!(Test-Path $p)) { throw "Missing authoritative file: $p" }
    Write-Host "PASS: $p" -ForegroundColor Green
}

# -----------------------------
# 2. Required build-kit files
# -----------------------------
$requiredBuild = @(
    (Join-Path $buildRoot "00-BUILD-KIT-INDEX.md"),
    (Join-Path $buildRoot "01-start-here\BUILD_SPEC.md"),
    (Join-Path $buildRoot "04-workflows-and-contracts\casecore.fact.schema.json"),
    (Join-Path $buildRoot "07-security-ops-and-governance\RUNTIME_ENFORCEMENT_POLICY.md"),
    (Join-Path $buildRoot "09-traceability-and-review\INTEGRATED_SYSTEM_REVIEW.md")
)

foreach ($p in $requiredBuild) {
    if (!(Test-Path $p)) { throw "Missing build-kit file: $p" }
    Write-Host "PASS: $p" -ForegroundColor Green
}

# -----------------------------
# 3. Naming drift scan
# -----------------------------
$allowedNamingFiles = @(
    (Join-Path $specRoot "docs\governance\NAMING_CONVENTIONS.md"),
    (Join-Path $specRoot "meta\gap-reports\NAMING_SCAN_REPORT.md"),
    (Join-Path $specRoot "meta\traceability\TRACEABILITY_STATUS.md"),
    (Join-Path $specRoot "meta\inventories\RUN_NAMING_SCAN.ps1")
)

$hits = Get-ChildItem $specRoot -Recurse -File |
    Where-Object { $allowedNamingFiles -notcontains $_.FullName } |
    Select-String -Pattern "TrialForge|trialforge|corecode|core code"

if ($hits) {
    $hits | ForEach-Object {
        "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
    }
    throw "Naming drift detected."
}

Write-Host "PASS: Naming drift scan clean" -ForegroundColor Green

# -----------------------------
# 4. Schema parity
# -----------------------------
$specSchemas = Get-ChildItem (Join-Path $specRoot "packages\contracts\schemas") -File |
    Select-Object -ExpandProperty Name | Sort-Object

$buildSchemas = Get-ChildItem (Join-Path $buildRoot "04-workflows-and-contracts") -File |
    Where-Object { $_.Name -like "*.schema.json" } |
    Select-Object -ExpandProperty Name | Sort-Object

$schemaDiff = Compare-Object $specSchemas $buildSchemas
if ($schemaDiff) {
    $schemaDiff
    throw "Schema parity failure between spec and build kit."
}

Write-Host "PASS: Schema parity verified" -ForegroundColor Green

# -----------------------------
# 5. Empty file check
# -----------------------------
$emptySpec = Get-ChildItem $specRoot -Recurse -File |
    Where-Object { $_.FullName -notmatch "\\_imports\\" -and $_.Length -eq 0 }

if ($emptySpec) {
    $emptySpec | Select-Object FullName
    throw "Empty authoritative files detected."
}

$emptyBuild = Get-ChildItem $buildRoot -Recurse -File |
    Where-Object { $_.Length -eq 0 }

if ($emptyBuild) {
    $emptyBuild | Select-Object FullName
    throw "Empty build-kit files detected."
}

Write-Host "PASS: No empty files detected" -ForegroundColor Green

# -----------------------------
# 6. Run consolidated validators
# -----------------------------
$runAll = Join-Path $specRoot "validators\run_all_validations.ps1"
& $runAll
if ($LASTEXITCODE -ne 0) {
    throw "Consolidated validation entrypoint failed."
}

$runtime = Join-Path $specRoot "validators\runtime\validate_runtime_output.ps1"
& $runtime
if ($LASTEXITCODE -ne 0) {
    throw "Runtime validation failed."
}

Write-Host "PASS: All validator layers passed" -ForegroundColor Green
Write-Host "CASECORE INTEGRATED CONSISTENCY AUDIT PASSED" -ForegroundColor Green

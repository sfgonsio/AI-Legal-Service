$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$specRoot = Join-Path $repoRoot "casecore-spec"

Write-Host "=== CASECORE VALIDATION ENTRYPOINT ===" -ForegroundColor Cyan

$schemaValidation = Join-Path $specRoot "validators\validate_schema_examples.ps1"
$pipelineValidation = Join-Path $specRoot "validators\pipeline\validate_pipeline_outputs.ps1"

if (!(Test-Path $schemaValidation)) {
    throw "Missing validation script: $schemaValidation"
}

if (!(Test-Path $pipelineValidation)) {
    throw "Missing validation script: $pipelineValidation"
}

Write-Host "Running schema example validation..." -ForegroundColor Yellow
& $schemaValidation
if ($LASTEXITCODE -ne 0) {
    throw "Schema example validation failed."
}

Write-Host "Running pipeline output validation..." -ForegroundColor Yellow
& $pipelineValidation
if ($LASTEXITCODE -ne 0) {
    throw "Pipeline validation failed."
}

Write-Host "ALL CASECORE VALIDATIONS PASSED" -ForegroundColor Green

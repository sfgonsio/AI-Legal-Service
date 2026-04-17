$ErrorActionPreference = "Stop"

$repoRoot  = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$specRoot  = Join-Path $repoRoot "casecore-spec"
$schemaDir = Join-Path $specRoot "packages\contracts\schemas"
$toolPath  = Join-Path $specRoot "validators\validate_json_artifact.py"
$exampleDir = Join-Path $specRoot "validators\examples"

# Resolve Python
$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    throw "Python not found."
}

# Ensure jsonschema exists
$check = & $pythonExe -c "import jsonschema; print('ok')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing jsonschema..." -ForegroundColor Yellow
    & $pythonExe -m pip install jsonschema
}

# Validate schema files parse as JSON
Write-Host "Validating schema file JSON parse..." -ForegroundColor Cyan
Get-ChildItem $schemaDir -Filter *.json | ForEach-Object {
    try {
        Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null
        Write-Host "PASS: Parsed $($_.Name)" -ForegroundColor Green
    } catch {
        throw "FAIL: Invalid JSON schema file: $($_.FullName)"
    }
}

# Mapping of schema -> example
$map = @(
    @{ Schema = "casecore.fact.schema.json"; Example = "fact.valid.json" },
    @{ Schema = "casecore.event.schema.json"; Example = "event.valid.json" },
    @{ Schema = "casecore.entity.schema.json"; Example = "entity.valid.json" },
    @{ Schema = "casecore.tag.schema.json"; Example = "tag.valid.json" },
    @{ Schema = "casecore.proposal-envelope.schema.json"; Example = "proposal-envelope.valid.json" },
    @{ Schema = "casecore.coa-element-coverage.schema.json"; Example = "coa-element-coverage.valid.json" }
)

Write-Host "Validating schema examples..." -ForegroundColor Cyan
foreach ($pair in $map) {
    $schemaPath = Join-Path $schemaDir $pair.Schema
    $examplePath = Join-Path $exampleDir $pair.Example
    & $pythonExe $toolPath $schemaPath $examplePath
    if ($LASTEXITCODE -ne 0) {
        throw "Validation failed for $($pair.Example)"
    }
}

Write-Host "ALL SCHEMA VALIDATIONS PASSED" -ForegroundColor Green

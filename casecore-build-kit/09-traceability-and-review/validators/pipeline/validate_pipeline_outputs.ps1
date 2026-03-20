$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$toolPath = Join-Path $repoRoot "casecore-spec\validators\pipeline\validate_pipeline_outputs.py"

$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    throw "Python not found."
}

$check = & $pythonExe -c "import jsonschema; print('ok')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing jsonschema..." -ForegroundColor Yellow
    & $pythonExe -m pip install jsonschema
}

& $pythonExe $toolPath
if ($LASTEXITCODE -ne 0) {
    throw "Pipeline output validation failed."
}

Write-Host "PIPELINE VALIDATION PASSED" -ForegroundColor Green

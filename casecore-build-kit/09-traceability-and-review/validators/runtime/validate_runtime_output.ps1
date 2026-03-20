$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$specRoot = Join-Path $repoRoot "casecore-spec"
$toolPath = Join-Path $specRoot "validators\runtime\validate_runtime_output.py"

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
    throw "Runtime enforcement validation failed."
}

Write-Host "RUNTIME ENFORCEMENT PASSED" -ForegroundColor Green

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$apiRoot = Join-Path $repoRoot "casecore-runtime\apps\api"
$testPath = Join-Path $apiRoot "tests\smoke_test_api.py"

$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    throw "Python not found."
}

& $pythonExe -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing FastAPI..." -ForegroundColor Yellow
    & $pythonExe -m pip install fastapi uvicorn
}

& $pythonExe $testPath
if ($LASTEXITCODE -ne 0) {
    throw "Runtime API smoke test failed."
}

Write-Host "RUNTIME API PACKAGE PASSED" -ForegroundColor Green

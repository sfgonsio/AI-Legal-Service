$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$testPath = Join-Path $repoRoot "casecore-runtime\packages\validators\tests\smoke_test_validators.py"

$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    throw "Python not found."
}

& $pythonExe $testPath
if ($LASTEXITCODE -ne 0) {
    throw "Runtime validators smoke test failed."
}

Write-Host "RUNTIME VALIDATORS PACKAGE PASSED" -ForegroundColor Green

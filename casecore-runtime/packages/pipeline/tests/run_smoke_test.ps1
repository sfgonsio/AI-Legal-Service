$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$testPath = Join-Path $repoRoot "casecore-runtime\packages\pipeline\tests\smoke_test_pipeline.py"

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
    throw "Runtime pipeline smoke test failed."
}

Write-Host "RUNTIME PIPELINE PACKAGE PASSED" -ForegroundColor Green

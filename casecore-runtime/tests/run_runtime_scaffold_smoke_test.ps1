$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\sfgon\Documents\GitHub\AI Legal Service"
$runtimeRoot = Join-Path $repoRoot "casecore-runtime"

$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
} else {
    throw "Python not found."
}

$tests = @(
    (Join-Path $runtimeRoot "services\audit-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\artifact-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\workflow-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\review-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\ingestion-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\persistence-service\tests\smoke_test.py"),
    (Join-Path $runtimeRoot "services\security-service\tests\smoke_test.py")
)

foreach ($test in $tests) {
    & $pythonExe $test
    if ($LASTEXITCODE -ne 0) {
        throw "Runtime scaffold smoke test failed: $test"
    }
}

Write-Host "CASECORE RUNTIME SERVICE SCAFFOLD PASSED" -ForegroundColor Green

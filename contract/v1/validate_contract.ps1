$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$realValidator = Join-Path $scriptDir "acceptance\validate_contract.ps1"

if (-not (Test-Path $realValidator)) {
    throw "Missing validator target: $realValidator"
}

& $realValidator
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
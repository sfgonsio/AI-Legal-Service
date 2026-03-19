$ErrorActionPreference = "Stop"

$root = "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec"

$allowed = @(
  "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec\docs\governance\NAMING_CONVENTIONS.md",
  "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec\meta\gap-reports\NAMING_SCAN_REPORT.md",
  "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec\meta\traceability\TRACEABILITY_STATUS.md",
  "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-spec\meta\inventories\RUN_NAMING_SCAN.ps1"
)

$hits = Get-ChildItem -Path $root -Recurse -File |
  Where-Object { $allowed -notcontains $_.FullName } |
  Select-String -Pattern 'TrialForge|trialforge|corecode|core code'

if ($hits) {
  $hits | ForEach-Object {
    "{0}:{1}: {2}" -f $_.Path, $_.LineNumber, $_.Line.Trim()
  }
}

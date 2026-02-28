<#
contract_module_scaffold.ps1
Governance utility to provision Contract v1 modules deterministically.

Principles:
- SSOT artifacts are authoritative; this script is tooling.
- No silent overwrite unless -Force.
- Refuses to run on dirty working tree unless -AllowDirty.
- UTF-8 no BOM output.
- Idempotent manifest insertion.

Usage examples:

# 1) Create an empty module skeleton with README
.\contract\v1\acceptance\contract_module_scaffold.ps1 -Module orchestration -Name "example_module" -CreateReadme

# 2) Provision Stage-11-style orchestration SSOT files (template)
.\contract\v1\acceptance\contract_module_scaffold.ps1 -Preset "orchestration_rerun_ssot" -Validate

# 3) Same as above + commit and push
.\contract\v1\acceptance\contract_module_scaffold.ps1 -Preset "orchestration_rerun_ssot" -Validate -CommitAndPush
#>

[CmdletBinding()]
param(
  # Generic mode
  [Parameter(Mandatory=$false)]
  [ValidateSet("orchestration","agents","taxonomies","schemas","tools","harness","acceptance","other")]
  [string]$Module,

  [Parameter(Mandatory=$false)]
  [string]$Name,

  [Parameter(Mandatory=$false)]
  [switch]$CreateReadme,

  # Preset mode (recommended)
  [Parameter(Mandatory=$false)]
  [ValidateSet("orchestration_rerun_ssot")]
  [string]$Preset,

  # Governance switches
  [Parameter(Mandatory=$false)]
  [switch]$Validate,

  [Parameter(Mandatory=$false)]
  [switch]$CommitAndPush,

  [Parameter(Mandatory=$false)]
  [switch]$Force,

  [Parameter(Mandatory=$false)]
  [switch]$AllowDirty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ----------------------------
# Helpers
# ----------------------------
function Assert-InRepoRoot {
  if (-not (Test-Path ".git")) { throw "Not in repo root ('.git' not found). cd to repo root and rerun." }
  if (-not (Test-Path ".\contract\v1\contract_manifest.yaml")) { throw "Missing .\contract\v1\contract_manifest.yaml." }
}

function Assert-GitClean {
  if ($AllowDirty) { return }
  $status = (git status --porcelain)
  if ($status -and $status.Trim().Length -gt 0) {
    throw "Working tree not clean. Commit/stash changes or rerun with -AllowDirty (not recommended)."
  }
}

function Ensure-Dir([string]$path) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Write-Utf8NoBom([string]$path, [string]$content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  $full = (Resolve-Path -LiteralPath (Split-Path -Parent $path) -ErrorAction Stop).Path
  $file = Join-Path $full (Split-Path -Leaf $path)
  [System.IO.File]::WriteAllText($file, $content, $utf8NoBom)
}

function Write-File([string]$path, [string]$content) {
  $parent = Split-Path -Parent $path
  if ($parent -and -not (Test-Path $parent)) { Ensure-Dir $parent }

  if ((Test-Path $path) -and (-not $Force)) {
    throw "Refusing to overwrite existing file: $path (use -Force to overwrite)"
  }

  if (-not (Test-Path $path)) {
    New-Item -ItemType File -Force -Path $path | Out-Null
  }

  Write-Utf8NoBom $path $content
}

function Ensure-ManifestEntries {
  param(
    [string]$manifestPath,
    [string[]]$entries
  )

  $text = Get-Content -Raw -LiteralPath $manifestPath

  # Idempotent: add only missing
  $missing = @()
  foreach ($e in $entries) {
    if ($text -notmatch [regex]::Escape($e)) { $missing += $e }
  }
  if ($missing.Count -eq 0) { return }

  # Conservative insertion:
  # If orchestration: exists, insert under it with 2-space indent.
  # Otherwise append a block at end (explicitly marked).
  if ($text -match "(?m)^(orchestration:\s*)$") {
    $insert = ($missing | ForEach-Object { "  - $_" }) -join "`r`n"
    $text = [regex]::Replace($text, "(?m)^(orchestration:\s*)$",
      ("`$1`r`n" + $insert),
      1
    )
  } else {
    $append = "`r`n# Provisioned entries (relocate if your manifest is grouped)`r`n" +
              (($missing | ForEach-Object { "- $_" }) -join "`r`n") + "`r`n"
    $text = $text + $append
  }

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $manifestPath).Path, $text, $utf8NoBom)
}

function Invoke-ContractValidation {
  $validator = ".\contract\v1\acceptance\validate_contract.ps1"
  if (-not (Test-Path $validator)) { throw "Validator not found: $validator" }
  & $validator
}

function Git-CommitPush([string[]]$paths, [string]$message) {
  git add -- $paths
  git commit -m $message
  git push
}

# ----------------------------
# Presets
# ----------------------------
function Provision-OrchestrationRerunSSOT {
  $orchDir = ".\contract\v1\orchestration"
  Ensure-Dir $orchDir

  # Files (A–D)
  $rerunLevelsPath = ".\contract\v1\orchestration\rerun_levels.yaml"
  $stateMachinePath = ".\contract\v1\orchestration\state_machine.yaml"
  $approvalGatesPath = ".\contract\v1\orchestration\approval_gates.yaml"
  $invalidationGraphPath = ".\contract\v1\orchestration\invalidation_graph.yaml"

  $rerunLevels = @'
version: v1
authoritative: true

rerun_levels:
  R0:
    name: STORE_ONLY
    requires_attorney_approval: false
    executes: []
    audit_event: UPLOAD_STORED_PENDING_REVIEW
    invalidates: []
    notes: "Raw uploads stored only. No canonical artifacts generated."
  R1:
    name: PROCESSING_ONLY
    requires_attorney_approval: false
    executes: [program_PROCESSING]
    audit_event: RERUN_R1_PROCESSING_COMPLETE
    invalidates: [DOCUMENTS, CHUNKS]
  R2:
    name: FACT_NORMALIZATION
    requires_attorney_approval: false
    executes: [program_PROCESSING, program_FACT_NORMALIZATION]
    audit_event: RERUN_R2_FACTS_COMPLETE
    invalidates: [EVIDENCE_FACTS]
  R3:
    name: TAGGING
    requires_attorney_approval: false
    executes: [program_PROCESSING, program_FACT_NORMALIZATION, program_TAGGING]
    audit_event: RERUN_R3_TAGGING_COMPLETE
    invalidates: [TAG_ASSIGNMENTS]
  R4:
    name: COMPOSITE_ENGINE
    requires_attorney_approval: false
    executes: [program_PROCESSING, program_FACT_NORMALIZATION, program_TAGGING, program_COMPOSITE_ENGINE]
    audit_event: RERUN_R4_COMPOSITE_COMPLETE
    invalidates: [EVENT_CANDIDATES]
  R5:
    name: MAPPING_REFRESH
    requires_attorney_approval: true
    executes: [program_PROCESSING, program_FACT_NORMALIZATION, program_TAGGING, program_COMPOSITE_ENGINE, agent_MAPPING]
    audit_event: RERUN_R5_MAPPING_COMPLETE
    invalidates: [MAPPINGS]
  R6:
    name: COA_ENGINE_REFRESH
    requires_attorney_approval: true
    executes: [program_PROCESSING, program_FACT_NORMALIZATION, program_TAGGING, program_COMPOSITE_ENGINE, agent_MAPPING, program_COA_ENGINE]
    audit_event: RERUN_R6_COA_COMPLETE
    invalidates: [COA_COVERAGE]
  R7:
    name: DOWNSTREAM_PROPOSALS
    requires_attorney_approval: true
    executes: [program_PROCESSING, program_FACT_NORMALIZATION, program_TAGGING, program_COMPOSITE_ENGINE, agent_MAPPING, program_COA_ENGINE, agent_COA_REASONER]
    audit_event: RERUN_R7_REASONER_COMPLETE
    invalidates: [ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]

rules:
  cumulative_only: true
  no_skipping_intermediate_layers: true
'@

  $stateMachine = @'
version: v1
authoritative: true

states:
  - STATE_IDLE
  - STATE_PROCESSING
  - STATE_FACTS_READY
  - STATE_TAGGED
  - STATE_COMPOSITE_READY
  - STATE_MAPPED
  - STATE_COA_EVALUATED
  - STATE_REASONED
  - STATE_SUPERSEDED
  - STATE_BLOCKED
  - STATE_IDLE_PENDING_DECISION

events:
  - EVT_UPLOAD_STORED
  - EVT_RERUN_REQUESTED
  - EVT_RERUN_APPROVED
  - EVT_RERUN_DECLINED
  - EVT_RERUN_COMPLETED
  - EVT_RUN_SUPERSEDED
  - EVT_FAILURE_BLOCKING

transitions:
  - from: STATE_IDLE
    event: EVT_RERUN_REQUESTED
    to: STATE_PROCESSING

  - from: STATE_PROCESSING
    event: EVT_RERUN_COMPLETED
    to: STATE_FACTS_READY

  - from: STATE_FACTS_READY
    event: EVT_RERUN_COMPLETED
    to: STATE_TAGGED

  - from: STATE_TAGGED
    event: EVT_RERUN_COMPLETED
    to: STATE_COMPOSITE_READY

  - from: STATE_COMPOSITE_READY
    event: EVT_RERUN_COMPLETED
    to: STATE_MAPPED

  - from: STATE_MAPPED
    event: EVT_RERUN_COMPLETED
    to: STATE_COA_EVALUATED

  - from: STATE_COA_EVALUATED
    event: EVT_RERUN_COMPLETED
    to: STATE_REASONED

  - from: STATE_COA_EVALUATED
    event: EVT_UPLOAD_STORED
    to: STATE_IDLE_PENDING_DECISION

  - from: STATE_IDLE_PENDING_DECISION
    event: EVT_RERUN_APPROVED
    to: STATE_PROCESSING

  - from: STATE_IDLE_PENDING_DECISION
    event: EVT_RERUN_DECLINED
    to: STATE_IDLE

  - from: "*"
    event: EVT_FAILURE_BLOCKING
    to: STATE_BLOCKED
'@

  $approvalGates = @'
version: v1
authoritative: true

approval_required_for_rerun_levels: [R5, R6, R7]
approval_optional_for_rerun_levels: [R2, R3, R4]
approval_not_required_for_rerun_levels: [R0, R1]

required_audit_events:
  approve: ATTORNEY_APPROVED_RERUN
  decline: ATTORNEY_DECLINED_RERUN

legal_artifact_impact_gate:
  required_for_impacts:
    - FILED_PLEADINGS
    - DISCOVERY_RESPONSES
    - PRODUCED_REPORTS
  required_ack_event: ATTORNEY_ACKNOWLEDGED_LEGAL_ARTIFACT_IMPACT
'@

  $invalidationGraph = @'
version: v1
authoritative: true

invalidation_rules:
  - upstream: DOCUMENTS
    downstream: [CHUNKS, EVIDENCE_FACTS, TAG_ASSIGNMENTS, EVENT_CANDIDATES, MAPPINGS, COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: CHUNKS
    downstream: [EVIDENCE_FACTS, TAG_ASSIGNMENTS, EVENT_CANDIDATES, MAPPINGS, COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: EVIDENCE_FACTS
    downstream: [TAG_ASSIGNMENTS, EVENT_CANDIDATES, MAPPINGS, COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: TAG_ASSIGNMENTS
    downstream: [EVENT_CANDIDATES, MAPPINGS, COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: EVENT_CANDIDATES
    downstream: [MAPPINGS, COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: MAPPINGS
    downstream: [COA_COVERAGE, ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]
  - upstream: COA_COVERAGE
    downstream: [ADVISORY_MEMOS, DISCOVERY_PLANS, DEPOSITION_PROPOSALS]

active_query_rule:
  latest_run_only: true
  no_mixed_run_answers: true
  superseded_excluded_by_default: true
  historical_run_requires_explicit_selection: true
'@

  Write-File $rerunLevelsPath $rerunLevels
  Write-File $stateMachinePath $stateMachine
  Write-File $approvalGatesPath $approvalGates
  Write-File $invalidationGraphPath $invalidationGraph

  # Manifest entries
  $manifestPath = ".\contract\v1\contract_manifest.yaml"
  $entries = @(
    "./contract/v1/orchestration/rerun_levels.yaml",
    "./contract/v1/orchestration/state_machine.yaml",
    "./contract/v1/orchestration/approval_gates.yaml",
    "./contract/v1/orchestration/invalidation_graph.yaml"
  )
  Ensure-ManifestEntries -manifestPath $manifestPath -entries $entries

  return @($rerunLevelsPath, $stateMachinePath, $approvalGatesPath, $invalidationGraphPath, $manifestPath)
}

# ----------------------------
# MAIN
# ----------------------------
Assert-InRepoRoot
Assert-GitClean

$changedPaths = @()

if ($Preset) {
  switch ($Preset) {
    "orchestration_rerun_ssot" {
      $changedPaths = Provision-OrchestrationRerunSSOT
    }
  }
}
else {
  if (-not $Module -or -not $Name) {
    throw "Provide -Preset or (-Module and -Name)."
  }

  $base = ".\contract\v1\$Module\$Name"
  Ensure-Dir $base

  if ($CreateReadme) {
    $readmePath = Join-Path $base "README.md"
    $readme = @"
# $Name
(Contract Module)

Purpose:
- Describe this module's role in Contract v1.

Authoritative:
- Define whether this module is authoritative SSOT.
"@
    Write-File $readmePath $readme
    $changedPaths += $readmePath
  }

  $changedPaths += $base
}

if ($Validate) {
  Invoke-ContractValidation
}

if ($CommitAndPush) {
  # Only add real files, not directories
  $pathsToAdd = $changedPaths | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -Unique
  if ($pathsToAdd.Count -eq 0) { throw "Nothing to commit." }
  Git-CommitPush -paths $pathsToAdd -message "Provision contract module artifacts (governance tooling)"
}

Write-Host "OK: contract module scaffold actions completed." -ForegroundColor Green
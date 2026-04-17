$ErrorActionPreference = "Stop"

$base = "C:\Users\sfgon\Documents\GitHub\AI Legal Service\casecore-runtime\legal"
$canon = Join-Path $base "canonical\evidence_code"
$ref   = Join-Path $base "reference\evidence_code"

New-Item -ItemType Directory -Force -Path $canon | Out-Null
New-Item -ItemType Directory -Force -Path $ref   | Out-Null

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

# --- JSON ---
Write-Utf8NoBom -Path (Join-Path $canon "EVID_550.json") -Content @'
{
  "code": "EVID",
  "section": "550",
  "title": "Burden of Producing Evidence",
  "text": "(a) The burden of producing evidence as to a particular fact is on the party against whom a finding on that fact would be required in the absence of further evidence.\n(b) The burden of producing evidence as to a particular fact is initially on the party with the burden of proof as to that fact.",
  "category": "burden_of_production",
  "canonical_type": "source",
  "structure": {
    "division": "5",
    "division_title": "Burden of Proof; Burden of Producing Evidence; Presumptions and Inferences",
    "chapter": "2",
    "chapter_title": "Burden of Producing Evidence",
    "article": null,
    "article_title": null
  },
  "source": {
    "type": "ca_legislature",
    "jurisdiction": "California",
    "url": "https://leginfo.legislature.ca.gov",
    "editorial_note": "(Enacted by Stats. 1965, Ch. 299.)"
  },
  "tags": [
    "burden of production",
    "evidence threshold",
    "prima facie",
    "shifting burden",
    "fact determination"
  ],
  "notes": "Defines which party must produce evidence to avoid an adverse finding and how that burden initially aligns with burden of proof."
}
'@

# --- MD ---
Write-Utf8NoBom -Path (Join-Path $ref "EVID_550_burden_of_producing_evidence.md") -Content @'
# EVID 550 — Burden of Producing Evidence

## Text
(a) The burden of producing evidence as to a particular fact is on the party against whom a finding on that fact would be required in the absence of further evidence.

(b) The burden of producing evidence as to a particular fact is initially on the party with the burden of proof as to that fact.

## Why it Matters
This section governs who must come forward with evidence on a particular fact to avoid losing on that issue.

## War Room Use
- Determines who must produce evidence first on each fact
- Identifies when burden shifts during litigation
- Critical for deposition sequencing and questioning strategy
- Helps identify gaps where opposing party has failed to meet production burden

## Related CACI
- Works in conjunction with all CACI elements by determining who must produce evidence supporting each required element

## Notes
This is distinct from burden of proof (EVID 500) and operates at the evidence production level.
'@

Write-Host "EVID 550 written successfully." -ForegroundColor Green
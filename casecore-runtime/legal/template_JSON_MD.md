#Convert this into:

## 1. JSON using canonical template
## 2. Markdown using reference template

##Also generate PowerShell script to create both files in:

## casecore-runtime/legal/

# JSON
{
  "code": "EVID",
  "section": "",
  "title": "",
  "text": "",
  "category": "",
  "canonical_type": "source",
  "source": {
    "type": "ca_legislature",
    "url": ""
  },
  "tags": [],
  "notes": ""
}

# MD
# EVID ___ — [TITLE]

## Text
[PASTE]

## Why it Matters
-

## War Room Use
-

## Related CACI
-

## Notes
-

# Tier 1 — Required now

EVID — admissibility, burden, presumptions, authentication, hearsay, witness credibility
CCP — procedural hooks that affect pleadings, discovery, deposition, motions
CIV — many substantive civil claims and remedies live here
BPC — especially important because your active matter touches cannabis/business issues
CACI — not in that code list, but still required because it defines what the jury must decide
# Tier 2 — Add as claim/remedy demands
CORP — ownership, fiduciary, entity governance, authority
COM — transactions, commercial instruments, sales-related issues
GOV — public agency overlays, if any
HSC — cannabis/regulatory/public health angles
INS, LAB, PEN only if a claim/defense or evidentiary theory actually touches them
# Tier 3 — Later or case-specific
CONST
PROB
RTC
VEH
WIC

#Practical rule
Your initial authoritative legal layer should be:
CACI
EVID
CCP
CIV
BPC
optionally HSC and CORP depending on the current claims
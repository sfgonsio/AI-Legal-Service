# program_CA_BPC_DIV10_SECTION_SYNC
(Authoritative Program Contract — v1 | Authority Section Harvest Layer)

## 1. Purpose

Harvests the full statutory section text for California Business and Professions Code Division 10 (Cannabis)
from the California Legislative Information site by following chapter/article links captured in toc.json.

Outputs canonical section artifacts for downstream use by:
- LAW_NORMALIZATION
- burden mapping
- COA reasoning
- deposition targeting

## 2. Inputs

Required:
- authority_store/ca/bpc/division_10_cannabis/current/toc.json
- authority_store/ca/bpc/division_10_cannabis/current/division_manifest.json

Optional:
- prior run manifests under authority_store/ca/bpc/division_10_cannabis/runs/

## 3. Outputs

Primary:
- authority_store/ca/bpc/division_10_cannabis/current/sections/*.json

Supporting:
- authority_store/ca/bpc/division_10_cannabis/current/pages/*.html
- authority_store/ca/bpc/division_10_cannabis/current/section_sync_manifest.json
- authority_store/ca/bpc/division_10_cannabis/runs/<run_id>/run_manifest.json

## 4. Canonical Section Shape

{
  "authority_id": "CA_BPC_DIV10_CANNABIS",
  "section_id": "BPC_26000",
  "section_number": "26000",
  "citation": "BPC § 26000",
  "title": "",
  "text": "",
  "source_url": "",
  "source_label": "",
  "captured_at": "",
  "html_sha256": "",
  "text_sha256": "",
  "run_id": ""
}

## 5. Determinism Rules

- toc.json is the navigation source of truth for discovery
- all fetched page URLs must be logged
- all page HTML must be hashable and reproducible
- every section must retain source_url and run_id
- output filenames must be deterministic by section number

## 6. Parsing Rules

- follow only codes_displayText.xhtml links associated with Division 10 Cannabis
- parse fetched HTML into visible text
- identify statutory sections by section number pattern 26000–26325 including decimals
- persist one file per section
- de-duplicate by section number

## 7. Failure Modes

- missing toc.json -> fail
- no fetchable section pages -> fail
- page fetch error -> log and continue
- section parse miss on page -> log page as unparsed
- duplicate section number -> keep first canonical record, log duplicate

## 8. Auditability

System must be able to answer:
- which TOC link produced this page
- which page produced this section
- what run generated this artifact
- what hashes correspond to source HTML and extracted text

## 9. Versioning

Bound to contract_manifest.yaml

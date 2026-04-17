# Pattern Pack Bundle Runner (Brain v1)

This runner creates a deterministic bundle folder and emits:
- input snapshot
- authority coverage result
- burden_map (json)
- coverage_report (stub, schema-valid)
- bundle_manifest.json with sha256 hashes

## Usage (PowerShell)

```powershell
python .\contract\v1\runner\run_pattern_pack_bundle.py `
  --contract_root .\contract\v1 `
  --run_id poc_polley_001 `
  --jurisdiction CA `
  --mode neutral_diagnostic `
  --case_signal_profile .\docs\poc\case_signal_profile_placeholder.json `
  --selected_archetype_id partnership_brand_ownership_ca_v1
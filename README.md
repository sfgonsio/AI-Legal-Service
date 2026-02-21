# AI Legal Service — GOLD Spec (Static Site)

This repository contains the authoritative **AI Legal Service GOLD** specification and a deterministic conversion tool that generates a static, web-readable version of the spec for review, sharing, and governed iteration.

## Repository Structure

- `input/`
  - Authoritative source document(s)
  - `AI Legal Service GOLD.docx` (SSOT for spec content)
- `src/`
  - Conversion tooling
  - `convert_docx_to_html.py`
- `site/`
  - Generated static artifacts (commit these)
  - `ai-legal-spec.html`
  - `ai-legal-spec.css`

## Deterministic Workflow (SSOT → Artifact)

1. Edit the authoritative source:
   - `input/AI Legal Service GOLD.docx`
2. Regenerate the static site artifacts:
   ```bash
   python src\convert_docx_to_html.py "input\AI Legal Service GOLD.docx"
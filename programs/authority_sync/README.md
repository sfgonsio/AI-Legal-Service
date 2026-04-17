# California Code Scraper for CaseCore

A production-grade Python scraper that extracts all California legal code sections from `leginfo.legislature.ca.gov` and generates canonical JSON files for the CaseCore legal platform.

## Quick Start

### Installation

```bash
# Dependencies are already installed:
# - requests (HTTP library)
# - beautifulsoup4 (HTML parsing)
# - lxml (XML/HTML processing)

# Just clone/download and you're ready to go!
```

### Basic Usage

Scrape a single California code:

```bash
python canonical_scraper.py CIV
```

Scrape all 29 California codes:

```bash
./scrape_all_codes.sh
```

## Overview

This project provides a complete solution for scraping California legal codes with:

- **Automated scraping** from leginfo.legislature.ca.gov
- **Canonical JSON generation** for CaseCore legal platform
- **Rate limiting** (1 request/second) for responsible crawling
- **Resume capability** to continue interrupted scrapes
- **Dry-run mode** to preview before executing
- **Error handling** with detailed logging
- **Automatic tagging** based on legal domain keywords
- **Division filtering** to process codes in stages
- **Parallel execution** support for faster scraping

## Files

### Core Scripts

| File | Purpose |
|------|---------|
| `canonical_scraper.py` | Main Python scraper for individual codes |
| `scrape_all_codes.sh` | Bash orchestration script for all 29 codes |
| `leginfo_parser.py` | HTML parsing utilities for leginfo structure |
| `validate_output.py` | Output validation and statistics tool |
| `test_scraper.py` | Unit tests for parsing and JSON generation |
| `generate_section_configs.py` | Config file generator |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `CONFIG.md` | Detailed configuration guide |

### Data

| Directory | Purpose |
|-----------|---------|
| `section_configs/` | Per-code configuration files (29 codes) |

## California Legal Codes (29)

The scraper supports all 29 official California legal codes:

```
BPC    Business and Professions Code
CIV    Civil Code
CCP    Code of Civil Procedure
COM    Commercial Code
CORP   Corporations Code
EDC    Education Code
ELEC   Elections Code
EVID   Evidence Code
FAM    Family Code
FIN    Financial Code
FGC    Fish and Game Code
FAC    Food and Agricultural Code
GOV    Government Code
HNC    Health and Nursing Code
HSC    Health and Safety Code
INS    Insurance Code
LAB    Labor Code
MVC    Military and Veterans Code
PEN    Penal Code
PROB   Probate Code
PCC    Professional Conduct Code
PRC    Public Records Code
PUC    Public Utilities Code
RTC    Revenue and Taxation Code
SHC    Streets and Highways Code
UIC    Unemployment Insurance Code
VEH    Vehicle Code
WAT    Water Code
WIC    Welfare and Institutions Code
```

## Features

### Single Code Scraping

```bash
# Basic scrape
python canonical_scraper.py CIV

# Dry-run (see what would be created)
python canonical_scraper.py CIV --dry-run

# Resume (skip already-downloaded files)
python canonical_scraper.py CIV --resume

# Scrape specific division only
python canonical_scraper.py CIV --division 3

# Custom output directory
python canonical_scraper.py PEN --base-path /data/legal

# Verbose logging
python canonical_scraper.py CIV --verbose
```

### All Codes Scraping

```bash
# Sequential (default)
./scrape_all_codes.sh

# Dry-run
./scrape_all_codes.sh --dry-run

# Parallel (4 at a time)
./scrape_all_codes.sh --parallel 4

# Resume
./scrape_all_codes.sh --resume

# Single code via master script
./scrape_all_codes.sh --code CIV

# Custom output path
./scrape_all_codes.sh --base-path /data/legal
```

### Validation

```bash
# Validate all output
python validate_output.py

# Validate specific code
python validate_output.py --code CIV

# Verbose error reporting
python validate_output.py --verbose

# Custom base path
python validate_output.py --dir /data/legal
```

## Output Format

Each section is written as a canonical JSON file:

```json
{
  "code": "CIV",
  "section": "1550",
  "title": "Essential Elements of Contract",
  "text": "Full text of the statute section...",
  "tags": ["contracts", "formation", "elements"],
  "structure": {
    "division": "3",
    "division_title": "Division 3 - Obligations",
    "chapter": "1",
    "chapter_title": "Chapter 1 - Definition",
    "article": null,
    "article_title": null
  },
  "source": {
    "type": "ca_legislature",
    "jurisdiction": "California",
    "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1550.&lawCode=CIV",
    "editorial_note": "Auto-scraped from leginfo.legislature.ca.gov",
    "scraped_at": "2026-04-08T12:34:56.789123"
  }
}
```

### Directory Structure

```
{base-path}/
  casecore-runtime/
    legal/
      canonical/
        civ/
          CIV_1.json
          CIV_2.json
          ...
          civ_manifest.json      (manifest file)
        pen/
          PEN_187.json
          ...
          pen_manifest.json
        ... (other 27 codes)
```

### File Naming

Files use the format `{CODE}_{SECTION}.json`:

- `CIV_1.json` - Civil Code section 1
- `CIV_1550.json` - Civil Code section 1550
- `CIV_1550_1.json` - Civil Code section 1550.1
- `PEN_187a.json` - Penal Code section 187(a)

## Automatic Tagging

The scraper generates tags automatically based on content keywords:

- `contract` - Contracts and agreements
- `liability` - Liability and damages
- `property` - Property law
- `formation` - Formation and requirements
- `remedies` - Remedies and relief
- `procedure` - Procedural law
- `evidence` - Evidence law
- `family` - Family law
- `criminal` - Criminal law
- `probate` - Estate and probate

Custom tags can be added by editing `LEGAL_KEYWORDS` in `canonical_scraper.py`.

## Rate Limiting

The scraper enforces a 1 second delay between requests to be respectful to the server:

- Civil Code (~3000 sections): ~50 minutes
- All 29 codes sequentially: ~40+ hours
- Use `--parallel` flag for faster execution

## Error Handling

The scraper includes comprehensive error handling:

- Network errors are logged and skipped
- Invalid sections continue to next section
- Partial results are preserved
- Resume capability allows retrying failed sections
- Detailed logging helps troubleshoot issues

## Testing

Run the test suite:

```bash
python test_scraper.py
```

Tests cover:
- Section number extraction
- HTML title parsing
- Text extraction
- Tag generation
- JSON structure validation
- File naming
- Unicode handling

## Logging

All operations are logged with timestamps and severity levels:

```
2026-04-08 12:34:56,789 - canonical_scraper - INFO - Starting scrape for code CIV
2026-04-08 12:34:57,890 - canonical_scraper - INFO - Fetching TOC for CIV
2026-04-08 12:34:58,901 - canonical_scraper - INFO - Found 3049 sections in TOC
```

Enable verbose logging with `--verbose` flag for debug information.

## Integration with CaseCore

The canonical JSON files are ready for CaseCore ingestion:

```python
from pathlib import Path
import json

# Iterate all canonical files
canonical_dir = Path("casecore-runtime/legal/canonical")
for code_dir in canonical_dir.iterdir():
    for json_file in code_dir.glob("*.json"):
        if json_file.name.endswith("_manifest.json"):
            continue
        
        with open(json_file) as f:
            section = json.load(f)
            # Feed to CaseCore ingestion pipeline
            casecore.ingest_canonical_section(section)
```

## Configuration

See `CONFIG.md` for detailed configuration options including:

- Custom output paths
- Division filtering
- Parallel execution
- Resume capability
- Logging configuration
- Performance tuning

## Requirements

- Python 3.7+
- requests (HTTP library)
- beautifulsoup4 (HTML parsing)
- lxml (XML processing)
- bash (for master script)

All are already installed.

## Performance

Typical scraping times (sequential, 1 req/sec):

| Code | Sections | Time |
|------|----------|------|
| CIV | ~3000 | ~50 min |
| PEN | ~1000 | ~17 min |
| FAM | ~500 | ~8 min |
| All 29 | ~15000 | ~40 hours |

Use parallel execution for significant speed improvements:

```bash
./scrape_all_codes.sh --parallel 4
# Roughly 4x faster, but respect server limits
```

## Troubleshooting

### Network Errors

```bash
# Check connectivity
curl https://leginfo.legislature.ca.gov

# Try with verbose logging
python canonical_scraper.py CIV --verbose

# Resume to retry failures
python canonical_scraper.py CIV --resume
```

### Missing Sections

The leginfo website may have changed its HTML structure. Update selectors in:

1. `leginfo_parser.py` - Update CSS selectors in `extract_*` methods
2. `canonical_scraper.py` - Update fallback parsing logic

### Disk Space

Large codes generate many JSON files (GB+). Check available space:

```bash
df -h
du -sh casecore-runtime/
```

## Advanced Usage

### Custom Section Lists

Pre-populate `section_configs/{code}_sections.json` with known sections to speed up scraping or use as fallback when network access is limited.

### Modified Tagging

Edit `LEGAL_KEYWORDS` in `canonical_scraper.py` to add domain-specific tags for your use case.

### Offline Mode

With pre-configured section lists in `section_configs/`, the scraper can work in offline mode by implementing a fallback data source.

## License

This scraper accesses publicly available information from California Legislature's official website (leginfo.legislature.ca.gov). The scraped content is public domain.

The scraper includes metadata identifying the source:
- `source.type: "ca_legislature"`
- `source.jurisdiction: "California"`
- `source.editorial_note: "Auto-scraped from leginfo.legislature.ca.gov"`

## Support

For issues or questions:

1. Check `CONFIG.md` for detailed documentation
2. Review verbose logging (`--verbose` flag)
3. Run test suite (`python test_scraper.py`)
4. Validate output (`python validate_output.py`)
5. Inspect leginfo.legislature.ca.gov to verify HTML structure

## Contributing

To improve the scraper:

1. Update HTML parsing in `leginfo_parser.py`
2. Add new tests to `test_scraper.py`
3. Run full test suite before submitting changes
4. Validate output with `validate_output.py`

---

**Built for CaseCore Legal Platform**
California Code Scraper v1.0 - 2026-04-08

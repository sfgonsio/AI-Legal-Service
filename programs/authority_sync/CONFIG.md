# California Code Scraper Configuration Guide

## Overview

This directory contains a production-grade Python scraper for California legal codes from `leginfo.legislature.ca.gov`, designed to generate canonical JSON files compatible with the CaseCore legal platform.

## Files

### Core Scripts

- **`canonical_scraper.py`** - Main scraper script
  - Pulls individual code sections from leginfo
  - Generates canonical JSON files
  - Handles rate limiting, error handling, resume capability
  - Supports dry-run and division filtering

- **`scrape_all_codes.sh`** - Master bash script
  - Orchestrates scraping of all 29 California codes
  - Supports sequential or parallel execution
  - Comprehensive logging and error handling
  - Resume capability for interrupted runs

- **`leginfo_parser.py`** - Utility module
  - Specialized HTML parsing for leginfo.legislature.ca.gov
  - Section number extraction
  - Structural hierarchy parsing
  - Table of contents parsing

- **`generate_section_configs.py`** - Config generator
  - Creates skeleton configuration files for all codes
  - Can be extended to populate with real section data

### Configuration Files

- **`section_configs/{code}_sections.json`** - Per-code configuration
  - Stores known section information
  - Fallback data source when live fetch fails
  - Can be pre-populated with section lists

## Installation

The scripts require Python 3.7+ and three external packages:

```bash
pip install --break-system-packages requests beautifulsoup4 lxml
```

All three are already installed in the environment.

## California Legal Codes (29 Total)

```
BPC   - Business and Professions Code
CIV   - Civil Code
CCP   - Code of Civil Procedure
COM   - Commercial Code
CORP  - Corporations Code
EDC   - Education Code
ELEC  - Elections Code
EVID  - Evidence Code
FAM   - Family Code
FIN   - Financial Code
FGC   - Fish and Game Code
FAC   - Food and Agricultural Code
GOV   - Government Code
HNC   - Health and Nursing Code
HSC   - Health and Safety Code
INS   - Insurance Code
LAB   - Labor Code
MVC   - Military and Veterans Code
PEN   - Penal Code
PROB  - Probate Code
PCC   - Professional Conduct Code
PRC   - Public Records Code
PUC   - Public Utilities Code
RTC   - Revenue and Taxation Code
SHC   - Streets and Highways Code
UIC   - Unemployment Insurance Code
VEH   - Vehicle Code
WAT   - Water Code
WIC   - Welfare and Institutions Code
```

## Usage

### Single Code Scrape

```bash
python canonical_scraper.py CIV
```

Options:
- `--dry-run` - Report what would be created without writing
- `--resume` - Skip already-existing files
- `--division DIV` - Scrape only a specific division
- `--base-path PATH` - Output base directory (default: `.`)
- `--verbose` - Enable debug logging

Examples:

```bash
# Dry run to see what will be created
python canonical_scraper.py CIV --dry-run

# Resume interrupted scraping
python canonical_scraper.py CIV --resume

# Scrape only Division 3 of Civil Code
python canonical_scraper.py CIV --division 3

# Use custom output directory
python canonical_scraper.py PEN --base-path /home/user/legal-data
```

### All Codes Scrape

```bash
./scrape_all_codes.sh
```

Options:
- `--dry-run` - Report what would be created without writing
- `--resume` - Skip already-existing files
- `--code CODE` - Scrape only one code (e.g., `--code CIV`)
- `--parallel N` - Run N scrapers in parallel (default: 1, sequential)
- `--base-path PATH` - Output base directory
- `--verbose` - Enable verbose logging
- `--help` - Show help message

Examples:

```bash
# Scrape all codes sequentially
./scrape_all_codes.sh

# Dry run to see what would be created
./scrape_all_codes.sh --dry-run

# Scrape only Penal Code
./scrape_all_codes.sh --code PEN

# Scrape all codes in parallel (4 at a time)
./scrape_all_codes.sh --parallel 4

# Resume previous interrupted scrape
./scrape_all_codes.sh --resume

# Custom base path
./scrape_all_codes.sh --base-path /data/legal
```

## Output Format

Each section is written as a canonical JSON file with the following structure:

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

### File Naming

Files are named `{CODE}_{SECTION}.json` with decimal points replaced by underscores:

- `CIV_1550.json` - Civil Code section 1550
- `CIV_1550_1.json` - Civil Code section 1550.1
- `PEN_187_a.json` - Penal Code section 187(a)

### Output Directory Structure

```
{base-path}/
  casecore-runtime/
    legal/
      canonical/
        civ/
          CIV_1.json
          CIV_2.json
          ...
          civ_manifest.json
        pen/
          PEN_187.json
          ...
          pen_manifest.json
        ...
```

### Manifest Files

A manifest JSON file is created for each code:

```json
{
  "code": "CIV",
  "total_sections": 3049,
  "scraped_at": "2026-04-08T12:34:56.789123",
  "sections": [
    {
      "section": "1",
      "title": "Application of code",
      "filename": "CIV_1.json"
    },
    ...
  ]
}
```

## Automatic Tagging

The scraper automatically generates tags based on keyword matching:

- `contract` - Contract, agreement, offer, acceptance, consideration
- `liability` - Liable, damages, negligence, tort, injury
- `property` - Property, ownership, possession, chattel
- `formation` - Formation, validity, requirements, elements
- `remedies` - Remedy, injunction, damages, relief
- `procedure` - Procedure, pleading, motion, discovery
- `evidence` - Evidence, witness, testimony, admissible
- `family` - Marriage, divorce, custody, child, adoption
- `criminal` - Crime, felony, misdemeanor, offense
- `probate` - Estate, probate, will, heir, succession

Add custom keywords by modifying the `LEGAL_KEYWORDS` dictionary in `canonical_scraper.py`.

## Features

### Rate Limiting

- Enforces 1 second delay between requests to be respectful to the server
- Configurable via `REQUEST_DELAY` constant

### Error Handling

- Graceful handling of network errors
- Detailed error logging with problem identification
- Continues scraping even if individual sections fail

### Resume Capability

- `--resume` flag skips already-downloaded sections
- Useful for continuing interrupted runs
- Checks file existence before fetching

### Dry-Run Mode

- `--dry-run` shows exactly what would be created without writing files
- Useful for validation before running full scrapes

### Logging

- Structured logging with timestamps
- Log file saved to `scrape_all_codes.log` when using master script
- Debug logging available with `--verbose`

## Advanced Configuration

### Custom Output Path

The output directory is configurable via `--base-path`. By default, files are written to:

```
./casecore-runtime/legal/canonical/{code_lowercase}/
```

To use a different location:

```bash
python canonical_scraper.py CIV --base-path /path/to/data
```

This will create:

```
/path/to/data/casecore-runtime/legal/canonical/civ/
```

### Division Filtering

Scrape only a specific division of a code:

```bash
python canonical_scraper.py CIV --division 3
```

This is useful for large codes where you want to process them in stages.

### Parallel Execution

The master script supports parallel scraping:

```bash
./scrape_all_codes.sh --parallel 4
```

This runs 4 scrapers simultaneously. Adjust based on your system resources and to avoid overloading the server.

## Troubleshooting

### Network Errors

If you get connection errors:
1. Check your network connectivity
2. Verify leginfo.legislature.ca.gov is accessible
3. Try with `--verbose` to see detailed error messages
4. Use `--resume` to retry failed sections

### Missing Sections

If sections are not found:
1. The leginfo website may have changed its structure
2. Check `leginfo_parser.py` and update selectors if needed
3. The section may not exist in that code
4. Try `--verbose` to see what's being parsed

### Disk Space

Large codes like CIV or PEN can generate thousands of JSON files (GB+ of data). Ensure sufficient disk space available.

## Performance Characteristics

- Rate limited to 1 request/second (respectful to server)
- Civil Code (~3000 sections) takes ~50 minutes sequentially
- All 29 codes sequentially would take ~40+ hours
- Use `--parallel` flag with master script for faster execution
- Memory usage is minimal (streams data)

## Integration with CaseCore

The JSON files are formatted for direct ingestion into CaseCore's canonical store:

```python
# Example CaseCore integration
from pathlib import Path
import json

# Find all canonical files
canonical_dir = Path("casecore-runtime/legal/canonical")
for json_file in canonical_dir.glob("*/*.json"):
    if json_file.name != f"{json_file.parent.name}_manifest.json":
        with open(json_file) as f:
            section = json.load(f)
            # Feed to CaseCore ingestion pipeline
            casecore.ingest_section(section)
```

## Development

### Adding New Parsers

To support additional legal code sources:

1. Create a new parser class in `leginfo_parser.py`
2. Inherit from or follow the `LegInfoParser` interface
3. Update the scraper to support the new source with a `--source` flag

### Custom Tagging

Modify the `LEGAL_KEYWORDS` dictionary in `canonical_scraper.py` to add domain-specific tags.

### Testing

Create a test file with mock HTML:

```python
from canonical_scraper import CaliforniaCodeScraper
from bs4 import BeautifulSoup

html = "<html>...</html>"
soup = BeautifulSoup(html, 'lxml')

scraper = CaliforniaCodeScraper("TEST")
title = scraper._extract_title(soup)
text = scraper._extract_section_text(soup)
```

## License & Attribution

This scraper accesses publicly available information from California Legislature's official website (leginfo.legislature.ca.gov).

The scraper metadata includes:
- `source.type: "ca_legislature"`
- `source.jurisdiction: "California"`
- `source.editorial_note: "Auto-scraped from leginfo.legislature.ca.gov"`

## Support

For issues or enhancements:

1. Check the troubleshooting section
2. Review verbose logging output (`--verbose`)
3. Verify leginfo.legislature.ca.gov is accessible
4. Check that HTML structure hasn't changed (inspect website manually)

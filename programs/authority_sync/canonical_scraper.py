#!/usr/bin/env python3
"""
California Code Scraper and Canonical JSON Generator
Pulls California code sections from leginfo.legislature.ca.gov and generates
canonical JSON files for the CaseCore legal platform.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    from leginfo_parser import LegInfoParser
except ImportError:
    LegInfoParser = None
    logger = logging.getLogger(__name__)
    logger.warning("leginfo_parser module not available, using inline parsing")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://leginfo.legislature.ca.gov"
TOC_URL_TEMPLATE = f"{BASE_URL}/faces/codes_displayexpandedbranch.xhtml?tocCode={{CODE}}"
SECTION_URL_TEMPLATE = f"{BASE_URL}/faces/codes_displaySection.xhtml?sectionNum={{NUM}}.&lawCode={{CODE}}"

# Rate limiting
REQUEST_DELAY = 1.0  # seconds

# Legal domain keywords for automatic tagging
LEGAL_KEYWORDS = {
    'contract': ['contract', 'agreement', 'offer', 'acceptance', 'consideration', 'terms', 'party'],
    'liability': ['liable', 'liability', 'damages', 'negligence', 'tort', 'injury'],
    'property': ['property', 'real property', 'chattel', 'possession', 'ownership'],
    'formation': ['formation', 'validity', 'requirements', 'essential', 'elements'],
    'remedies': ['remedy', 'remedies', 'injunction', 'damages', 'relief'],
    'procedure': ['procedure', 'pleading', 'motion', 'discovery', 'trial', 'judgment'],
    'evidence': ['evidence', 'witness', 'testimony', 'admissible', 'hearsay'],
    'family': ['marriage', 'divorce', 'custody', 'child', 'parent', 'adoption'],
    'criminal': ['crime', 'criminal', 'felony', 'misdemeanor', 'sentence', 'offense'],
    'probate': ['estate', 'probate', 'will', 'heir', 'succession', 'testator'],
}


class CaliforniaCodeScraper:
    """Scrapes California codes from leginfo.legislature.ca.gov"""

    def __init__(
        self,
        code: str,
        base_path: str = ".",
        dry_run: bool = False,
        division: Optional[str] = None,
        resume: bool = False,
        verbose: bool = False
    ):
        """
        Initialize the scraper.

        Args:
            code: Code abbreviation (e.g., 'CIV', 'PEN')
            base_path: Base output directory
            dry_run: If True, don't write files
            division: Only scrape specified division
            resume: Skip already-existing files
            verbose: Enable verbose logging
        """
        self.code = code.upper()
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.target_division = division
        self.resume = resume
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        if verbose:
            logger.setLevel(logging.DEBUG)

        # Set up output directory
        self.output_dir = self.base_path / "casecore-runtime" / "legal" / "canonical" / self.code.lower()
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {self.output_dir}")

        self.sections_data = []
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page."""
        self._rate_limit()
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _extract_section_number(self, text: str) -> Optional[str]:
        """Extract section number from text."""
        # Match patterns like "1550", "1550.1", "1550.2(a)", etc.
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        return match.group(1) if match else None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract section title/heading."""
        if LegInfoParser:
            title = LegInfoParser.extract_title(soup)
            if title:
                return title

        # Fallback inline parsing
        heading = soup.find('h2') or soup.find('h3') or soup.find('h4')
        if heading:
            return heading.get_text(strip=True)
        return None

    def _extract_section_text(self, soup: BeautifulSoup) -> str:
        """Extract the full text of a section."""
        if LegInfoParser:
            text = LegInfoParser.extract_section_text(soup)
            if text:
                return text

        # Fallback inline parsing
        content = soup.find('div', {'class': re.compile(r'content|body|article')})
        if not content:
            content = soup.find('main') or soup.body

        if content:
            # Remove scripts and styles
            for tag in content.find_all(['script', 'style']):
                tag.decompose()

            # Get text and clean it up
            text = content.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)

        return ""

    def _extract_structure(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract structural information (division, chapter, article)."""
        if LegInfoParser:
            return LegInfoParser.extract_structure(soup)

        # Fallback inline parsing
        structure = {
            "division": None,
            "division_title": None,
            "chapter": None,
            "chapter_title": None,
            "article": None,
            "article_title": None
        }

        # Try to find breadcrumbs or navigation elements
        nav = soup.find('nav') or soup.find('ol', {'class': re.compile(r'breadcrumb')})
        if nav:
            items = nav.find_all(['li', 'a'])
            for i, item in enumerate(items):
                text = item.get_text(strip=True)
                # Parse structure from breadcrumb
                if 'Division' in text or 'Div' in text:
                    match = re.search(r'Division\s+(\w+)', text, re.IGNORECASE)
                    if match:
                        structure['division'] = match.group(1)
                        structure['division_title'] = text
                if 'Chapter' in text:
                    match = re.search(r'Chapter\s+(\w+)', text, re.IGNORECASE)
                    if match:
                        structure['chapter'] = match.group(1)
                        structure['chapter_title'] = text

        return structure

    def _generate_tags(self, title: str, text: str) -> List[str]:
        """Generate tags based on content keywords."""
        content = (title + " " + text[:1000]).lower()  # Use title + first 1000 chars
        tags = set()

        for tag_name, keywords in LEGAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    tags.add(tag_name)
                    break

        return sorted(list(tags))

    def _build_canonical_json(
        self,
        section_num: str,
        title: str,
        text: str,
        structure: Dict,
        url: str
    ) -> Dict:
        """Build canonical JSON structure."""
        tags = self._generate_tags(title, text)

        return {
            "code": self.code,
            "section": section_num,
            "title": title,
            "text": text,
            "tags": tags,
            "structure": {
                "division": structure.get('division'),
                "division_title": structure.get('division_title'),
                "chapter": structure.get('chapter'),
                "chapter_title": structure.get('chapter_title'),
                "article": structure.get('article'),
                "article_title": structure.get('article_title')
            },
            "source": {
                "type": "ca_legislature",
                "jurisdiction": "California",
                "url": url,
                "editorial_note": "Auto-scraped from leginfo.legislature.ca.gov",
                "scraped_at": datetime.now().isoformat()
            }
        }

    def _get_section_filename(self, section_num: str) -> str:
        """Generate filename from section number."""
        # Replace decimal points with underscores, remove parentheses
        clean_section = section_num.replace('.', '_').replace('(', '').replace(')', '')
        return f"{self.code}_{clean_section}.json"

    def _fetch_toc(self) -> Optional[List[Tuple[str, str]]]:
        """Fetch table of contents and extract section links."""
        url = TOC_URL_TEMPLATE.format(CODE=self.code)
        logger.info(f"Fetching TOC for {self.code} from {url}")

        soup = self._fetch_page(url)
        if not soup:
            logger.warning("Could not fetch TOC page")
            return None

        sections = []

        if LegInfoParser:
            # Use the parser utility
            sections = LegInfoParser.extract_toc_links(soup, self.code)
        else:
            # Fallback inline parsing
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Match section links
                if 'codes_displaySection.xhtml' in href or 'sectionNum=' in href:
                    section_num = self._extract_section_number(text)
                    if section_num:
                        # Build full URL
                        if href.startswith('http'):
                            full_url = href
                        else:
                            full_url = urljoin(BASE_URL, href)
                        sections.append((section_num, full_url))

        if sections:
            logger.info(f"Found {len(sections)} sections in TOC")
        return sections if sections else None

    def _load_sections_from_config(self) -> Optional[List[Tuple[str, str]]]:
        """
        Load pre-configured section lists from a local config file.
        This allows offline operation when network is unavailable.
        """
        config_file = Path(__file__).parent / "section_configs" / f"{self.code.lower()}_sections.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    sections = [(str(item['num']), item['url']) for item in data.get('sections', [])]
                    logger.info(f"Loaded {len(sections)} sections from config")
                    return sections
            except Exception as e:
                logger.warning(f"Could not load section config: {e}")
        return None

    def _fetch_sections_from_api(self) -> Optional[List[Tuple[str, str]]]:
        """
        Fallback: Try to construct section URLs directly.
        California code sections are typically numbered sequentially.
        """
        logger.info(f"Using heuristic section discovery for {self.code}")
        sections = []

        # Try common section ranges (this is a heuristic)
        # Most California codes have sections numbered 1-10000
        for i in range(1, 5000):
            section_num = str(i)
            url = SECTION_URL_TEMPLATE.format(NUM=section_num, CODE=self.code)
            sections.append((section_num, url))

        logger.warning(f"Generated {len(sections)} potential section URLs (will validate during fetch)")
        return sections

    def scrape(self) -> bool:
        """Main scraping method."""
        logger.info(f"Starting scrape for code {self.code}")
        if self.target_division:
            logger.info(f"Limited to division: {self.target_division}")

        # Try to get TOC first
        sections = self._fetch_toc()
        if not sections:
            logger.warning("Could not fetch TOC, attempting fallback methods")
            # Try loading from local config
            sections = self._load_sections_from_config()

        if not sections:
            logger.warning("No sections found via TOC or config, using heuristic discovery")
            # Use heuristic section discovery
            sections = self._fetch_sections_from_api()

        if not sections:
            logger.error("Could not discover sections via any method")
            return False

        logger.info(f"Will process {len(sections)} sections")

        successful = 0
        failed = 0

        for idx, (section_num, url) in enumerate(sections, 1):
            logger.info(f"[{idx}/{len(sections)}] Processing section {section_num}")

            # Check resume condition
            if self.resume:
                filename = self._get_section_filename(section_num)
                output_file = self.output_dir / filename
                if output_file.exists():
                    logger.debug(f"Skipping existing section {section_num}")
                    successful += 1
                    continue

            # Fetch section
            soup = self._fetch_page(url)
            if not soup:
                logger.warning(f"Failed to fetch section {section_num}")
                failed += 1
                continue

            # Extract data
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"Could not extract title for section {section_num}")
                failed += 1
                continue

            text = self._extract_section_text(soup)
            if not text:
                logger.warning(f"Could not extract text for section {section_num}")
                failed += 1
                continue

            structure = self._extract_structure(soup, url)

            # Build canonical JSON
            canonical_json = self._build_canonical_json(section_num, title, text, structure, url)

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would create: {self._get_section_filename(section_num)}")
            else:
                # Write JSON file
                filename = self._get_section_filename(section_num)
                output_file = self.output_dir / filename
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(canonical_json, f, indent=2, ensure_ascii=False)
                    logger.debug(f"Wrote {output_file}")
                except IOError as e:
                    logger.error(f"Failed to write {output_file}: {e}")
                    failed += 1
                    continue

            self.sections_data.append(canonical_json)
            successful += 1

        # Write manifest
        if not self.dry_run and self.sections_data:
            self._write_manifest(successful)

        logger.info(f"Scrape complete: {successful} successful, {failed} failed")
        return failed == 0

    def _write_manifest(self, count: int):
        """Write manifest file listing all scraped sections."""
        manifest = {
            "code": self.code,
            "total_sections": count,
            "scraped_at": datetime.now().isoformat(),
            "sections": [
                {
                    "section": item['section'],
                    "title": item['title'],
                    "filename": self._get_section_filename(item['section'])
                }
                for item in self.sections_data
            ]
        }

        manifest_file = self.output_dir / f"{self.code.lower()}_manifest.json"
        try:
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"Wrote manifest to {manifest_file}")
        except IOError as e:
            logger.error(f"Failed to write manifest: {e}")

    def report(self):
        """Print summary report."""
        if self.dry_run:
            print(f"\n[DRY-RUN REPORT]")
            print(f"Code: {self.code}")
            print(f"Would create: {len(self.sections_data)} canonical JSON files")
            if self.target_division:
                print(f"Division filter: {self.target_division}")
        else:
            print(f"\n[SCRAPE REPORT]")
            print(f"Code: {self.code}")
            print(f"Created: {len(self.sections_data)} canonical JSON files")
            print(f"Output directory: {self.output_dir}")
            if self.target_division:
                print(f"Division filter: {self.target_division}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape California codes and generate canonical JSON files"
    )
    parser.add_argument(
        'code',
        help='California code abbreviation (e.g., CIV, PEN, FAM)'
    )
    parser.add_argument(
        '--base-path',
        default='.',
        help='Base output directory (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report what would be created without writing files'
    )
    parser.add_argument(
        '--division',
        help='Only scrape a specific division'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Skip already-existing files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    scraper = CaliforniaCodeScraper(
        code=args.code,
        base_path=args.base_path,
        dry_run=args.dry_run,
        division=args.division,
        resume=args.resume,
        verbose=args.verbose
    )

    success = scraper.scrape()
    scraper.report()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

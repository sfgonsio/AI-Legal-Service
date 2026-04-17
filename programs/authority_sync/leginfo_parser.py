#!/usr/bin/env python3
"""
California Legislative Information Website Parser
Provides utilities for parsing leginfo.legislature.ca.gov content.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LegInfoParser:
    """Parser for leginfo.legislature.ca.gov content"""

    # Section number patterns
    SECTION_PATTERN = re.compile(r'§?\s*(\d+(?:\.\d+)?)', re.IGNORECASE)
    DIVISION_PATTERN = re.compile(r'Division\s+(\w+)', re.IGNORECASE)
    CHAPTER_PATTERN = re.compile(r'Chapter\s+(\w+)', re.IGNORECASE)
    ARTICLE_PATTERN = re.compile(r'Article\s+(\w+)', re.IGNORECASE)

    @staticmethod
    def extract_section_number(text: str) -> Optional[str]:
        """Extract section number from text."""
        match = LegInfoParser.SECTION_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> Optional[str]:
        """Extract section title from page."""
        # Try common heading selectors
        selectors = [
            'h1.statute-title',
            'h2.statute-heading',
            'h3.statute-heading',
            'h1',
            'h2',
            'h3'
        ]

        for selector in selectors:
            heading = soup.select_one(selector)
            if heading:
                title = heading.get_text(strip=True)
                if title and len(title) > 3:  # Avoid very short text
                    return title

        return None

    @staticmethod
    def extract_section_text(soup: BeautifulSoup) -> str:
        """Extract the full text content of a statute section."""
        # Priority order for content containers
        content_selectors = [
            'div.statute-text',
            'div.body',
            'div.content',
            'article',
            'main'
        ]

        content_div = None
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            # Fallback to body
            content_div = soup.body if soup.body else soup

        if content_div:
            # Remove unwanted elements
            for tag in content_div.find_all(['script', 'style', 'nav', 'footer']):
                tag.decompose()

            # Get text with preserved line structure
            text = content_div.get_text(separator='\n', strip=True)
            # Normalize whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)

        return ""

    @staticmethod
    def extract_structure(
        soup: BeautifulSoup,
        breadcrumb_text: str = ""
    ) -> Dict[str, Optional[str]]:
        """Extract hierarchical structure (division, chapter, article)."""
        structure = {
            "division": None,
            "division_title": None,
            "chapter": None,
            "chapter_title": None,
            "article": None,
            "article_title": None
        }

        # Try to find breadcrumb navigation
        breadcrumb = soup.find('nav') or soup.find('ol', {'class': re.compile(r'breadcrumb')})
        if breadcrumb:
            breadcrumb_text = breadcrumb.get_text(' ')

        if breadcrumb_text:
            # Extract division
            div_match = LegInfoParser.DIVISION_PATTERN.search(breadcrumb_text)
            if div_match:
                structure['division'] = div_match.group(1)

            # Extract chapter
            ch_match = LegInfoParser.CHAPTER_PATTERN.search(breadcrumb_text)
            if ch_match:
                structure['chapter'] = ch_match.group(1)

            # Extract article
            art_match = LegInfoParser.ARTICLE_PATTERN.search(breadcrumb_text)
            if art_match:
                structure['article'] = art_match.group(1)

        return structure

    @staticmethod
    def parse_section_page(soup: BeautifulSoup, url: str = "") -> Dict:
        """Parse a complete section page and extract all metadata."""
        breadcrumb_text = soup.get_text() if soup else ""

        return {
            'section_number': LegInfoParser.extract_section_number(url),
            'title': LegInfoParser.extract_title(soup),
            'text': LegInfoParser.extract_section_text(soup),
            'structure': LegInfoParser.extract_structure(soup, breadcrumb_text)
        }

    @staticmethod
    def extract_toc_links(soup: BeautifulSoup, code: str) -> List[Tuple[str, str]]:
        """Extract all section links from a table of contents page."""
        sections = []

        if not soup:
            return sections

        # Look for all links that reference section display
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Check if this looks like a section link
            if 'codes_displaySection' in href or 'sectionNum=' in href:
                section_num = LegInfoParser.extract_section_number(text)
                if section_num:
                    # Construct full URL if needed
                    if not href.startswith('http'):
                        href = f"https://leginfo.legislature.ca.gov{href}" if href.startswith('/') else \
                               f"https://leginfo.legislature.ca.gov/faces/{href}"

                    sections.append((section_num, href))

        return sections

    @staticmethod
    def is_valid_section_page(soup: BeautifulSoup) -> bool:
        """Check if the page appears to be a valid statute section page."""
        # Check for characteristic elements of a statute page
        has_title = LegInfoParser.extract_title(soup) is not None
        has_text = len(LegInfoParser.extract_section_text(soup)) > 50

        return has_title and has_text

    @staticmethod
    def extract_all_section_numbers(text: str) -> List[str]:
        """Extract all section numbers from text."""
        matches = LegInfoParser.SECTION_PATTERN.findall(text)
        return list(set(matches))  # Remove duplicates

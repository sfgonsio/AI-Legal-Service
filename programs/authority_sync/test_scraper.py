#!/usr/bin/env python3
"""
Test suite for the California Code Scraper.
Tests parsing, JSON generation, and output validation.
"""

import json
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup

from canonical_scraper import CaliforniaCodeScraper
from leginfo_parser import LegInfoParser


def test_section_number_extraction():
    """Test section number extraction."""
    test_cases = [
        ("Section 1550", "1550"),
        ("§ 1550.1", "1550.1"),
        ("Section 187(a)", "187"),
        ("§ 1(b)(2)", "1"),
    ]

    for text, expected in test_cases:
        result = LegInfoParser.extract_section_number(text)
        assert result == expected, f"Expected {expected}, got {result} for '{text}'"
        print(f"✓ Section extraction: '{text}' -> '{result}'")


def test_title_extraction():
    """Test title extraction from HTML."""
    html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <h2 class="statute-title">Section 1550. Essential Elements of Contract</h2>
        <div class="statute-text">Some content</div>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'lxml')
    title = LegInfoParser.extract_title(soup)
    assert title is not None
    assert "1550" in title or "Essential" in title
    print(f"✓ Title extraction: {title}")


def test_text_extraction():
    """Test full text extraction."""
    html = """
    <html>
    <body>
        <div class="statute-text">
            <p>Full text of the statute.</p>
            <p>With multiple paragraphs.</p>
        </div>
        <script>alert('ignored');</script>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, 'lxml')
    text = LegInfoParser.extract_section_text(soup)
    assert "Full text" in text
    assert "statute" in text
    assert "alert" not in text  # Script should be removed
    print(f"✓ Text extraction ({len(text)} chars)")


def test_tag_generation():
    """Test automatic tag generation."""
    scraper = CaliforniaCodeScraper("TEST")

    # Test with contract-related content
    title = "Contract Formation and Acceptance"
    text = "This section covers the formation of contracts and acceptance of offers."

    tags = scraper._generate_tags(title, text)
    assert "contract" in tags
    assert "formation" in tags
    print(f"✓ Tag generation: {tags}")


def test_canonical_json_generation():
    """Test canonical JSON structure generation."""
    scraper = CaliforniaCodeScraper("CIV")

    canonical = scraper._build_canonical_json(
        section_num="1550",
        title="Essential Elements of Contract",
        text="Full text here",
        structure={
            "division": "3",
            "division_title": "Obligations",
            "chapter": "1",
            "chapter_title": "Definition",
            "article": None,
            "article_title": None
        },
        url="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1550.&lawCode=CIV"
    )

    # Validate structure
    assert canonical["code"] == "CIV"
    assert canonical["section"] == "1550"
    assert canonical["title"] == "Essential Elements of Contract"
    assert isinstance(canonical["tags"], list)
    assert canonical["source"]["type"] == "ca_legislature"
    assert canonical["source"]["jurisdiction"] == "California"
    assert "scraped_at" in canonical["source"]

    print("✓ Canonical JSON structure valid")
    print(f"  - Code: {canonical['code']}")
    print(f"  - Section: {canonical['section']}")
    print(f"  - Tags: {canonical['tags']}")


def test_filename_generation():
    """Test filename generation from section numbers."""
    scraper = CaliforniaCodeScraper("CIV")

    test_cases = [
        ("1550", "CIV_1550.json"),
        ("1550.1", "CIV_1550_1.json"),
        ("187", "CIV_187.json"),
        ("187(a)", "CIV_187a.json"),
    ]

    for section, expected in test_cases:
        filename = scraper._get_section_filename(section)
        assert filename == expected, f"Expected {expected}, got {filename}"
        print(f"✓ Filename: {section} -> {filename}")


def test_output_directory_structure():
    """Test output directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scraper = CaliforniaCodeScraper(
            "CIV",
            base_path=tmpdir,
            dry_run=False
        )

        # Check directory structure
        expected_dir = Path(tmpdir) / "casecore-runtime" / "legal" / "canonical" / "civ"
        assert scraper.output_dir == expected_dir
        assert scraper.output_dir.exists()
        print(f"✓ Output directory created: {scraper.output_dir}")


def test_json_serialization():
    """Test JSON serialization with special characters."""
    scraper = CaliforniaCodeScraper("CIV")

    canonical = scraper._build_canonical_json(
        section_num="1550",
        title="Section with special chars: § • → ∆",
        text="Text with unicode: é à ñ ü 中文",
        structure={
            "division": "3",
            "division_title": "Division Title",
            "chapter": None,
            "chapter_title": None,
            "article": None,
            "article_title": None
        },
        url="https://example.com"
    )

    # Should not raise exception
    json_str = json.dumps(canonical, ensure_ascii=False, indent=2)
    assert len(json_str) > 100
    print(f"✓ JSON serialization with unicode ({len(json_str)} chars)")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("CALIFORNIA CODE SCRAPER - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Section number extraction", test_section_number_extraction),
        ("Title extraction", test_title_extraction),
        ("Text extraction", test_text_extraction),
        ("Tag generation", test_tag_generation),
        ("Canonical JSON generation", test_canonical_json_generation),
        ("Filename generation", test_filename_generation),
        ("Output directory structure", test_output_directory_structure),
        ("JSON serialization", test_json_serialization),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

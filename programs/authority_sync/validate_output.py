#!/usr/bin/env python3
"""
Validation script for canonical JSON output files.
Checks format compliance, integrity, and provides statistics.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

CANONICAL_DIR = Path("casecore-runtime/legal/canonical")

REQUIRED_FIELDS = {
    "code": str,
    "section": str,
    "title": str,
    "text": str,
    "tags": list,
    "structure": dict,
    "source": dict
}

REQUIRED_SOURCE_FIELDS = {
    "type": str,
    "jurisdiction": str,
    "url": str,
    "editorial_note": str
}

REQUIRED_STRUCTURE_FIELDS = {
    "division": (type(None), str),
    "division_title": (type(None), str),
    "chapter": (type(None), str),
    "chapter_title": (type(None), str)
}


def validate_json_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Validate a single canonical JSON file."""
    errors = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except Exception as e:
        return False, [f"Read error: {e}"]

    # Check required top-level fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Field '{field}' has wrong type (expected {expected_type.__name__}, got {type(data[field]).__name__})")

    # Validate code format
    if "code" in data and not data["code"].isupper():
        errors.append(f"Code should be uppercase: {data['code']}")

    # Validate section format
    if "section" in data:
        section = str(data["section"])
        if not section[0].isdigit():
            errors.append(f"Section should start with digit: {section}")

    # Validate text length
    if "text" in data and len(data["text"]) < 10:
        errors.append(f"Text is too short ({len(data['text'])} chars)")

    # Validate tags
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append("Tags should be a list")
        elif any(not isinstance(t, str) for t in data["tags"]):
            errors.append("All tags should be strings")

    # Validate structure
    if "structure" in data:
        structure = data["structure"]
        if not isinstance(structure, dict):
            errors.append("Structure should be a dict")
        else:
            for field, expected_types in REQUIRED_STRUCTURE_FIELDS.items():
                if field not in structure:
                    errors.append(f"Missing structure field: {field}")
                elif not isinstance(structure[field], expected_types):
                    errors.append(f"Structure field '{field}' has wrong type")

    # Validate source
    if "source" in data:
        source = data["source"]
        if not isinstance(source, dict):
            errors.append("Source should be a dict")
        else:
            for field, expected_type in REQUIRED_SOURCE_FIELDS.items():
                if field not in source:
                    errors.append(f"Missing source field: {field}")
                elif not isinstance(source[field], expected_type):
                    errors.append(f"Source field '{field}' has wrong type")

            if "url" in source:
                url = source["url"]
                if not url.startswith("https://leginfo.legislature.ca.gov"):
                    errors.append(f"URL doesn't match expected pattern: {url}")

    return len(errors) == 0, errors


def validate_directory(code: str = None) -> Dict:
    """Validate all canonical files in directory."""
    if code:
        code_dir = CANONICAL_DIR / code.lower()
        codes_to_check = [(code, code_dir)]
    else:
        codes_to_check = [(d.name.upper(), d) for d in CANONICAL_DIR.iterdir() if d.is_dir()]

    results = {
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "errors_by_file": {},
        "error_summary": {},
        "codes": {}
    }

    for code, code_dir in sorted(codes_to_check):
        if not code_dir.exists():
            print(f"Code directory not found: {code_dir}")
            continue

        json_files = list(code_dir.glob("*.json"))
        # Exclude manifest files
        json_files = [f for f in json_files if not f.name.endswith("_manifest.json")]

        code_stats = {
            "total": len(json_files),
            "valid": 0,
            "invalid": 0,
            "errors": {}
        }

        print(f"\nValidating {code} ({len(json_files)} files)...")

        for filepath in sorted(json_files):
            results["total_files"] += 1
            is_valid, errors = validate_json_file(filepath)

            if is_valid:
                results["valid_files"] += 1
                code_stats["valid"] += 1
            else:
                results["invalid_files"] += 1
                code_stats["invalid"] += 1
                results["errors_by_file"][str(filepath)] = errors
                code_stats["errors"][filepath.name] = errors

                # Track error types
                for error in errors:
                    error_type = error.split(":")[0].strip()
                    results["error_summary"][error_type] = results["error_summary"].get(error_type, 0) + 1

        results["codes"][code] = code_stats

        if code_stats["valid"] > 0:
            pct = 100 * code_stats["valid"] / code_stats["total"]
            print(f"  {code_stats['valid']}/{code_stats['total']} valid ({pct:.1f}%)")
        if code_stats["invalid"] > 0:
            print(f"  {code_stats['invalid']} invalid files")

    return results


def print_summary(results: Dict):
    """Print validation summary."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    total = results["total_files"]
    valid = results["valid_files"]
    invalid = results["invalid_files"]

    if total == 0:
        print("No files found to validate")
        return

    pct = 100 * valid / total if total > 0 else 0
    print(f"\nTotal files: {total}")
    print(f"Valid: {valid} ({pct:.1f}%)")
    print(f"Invalid: {invalid}")

    if results["codes"]:
        print("\nBy code:")
        for code in sorted(results["codes"].keys()):
            stats = results["codes"][code]
            pct = 100 * stats["valid"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {code}: {stats['valid']}/{stats['total']} valid ({pct:.1f}%)")

    if results["error_summary"]:
        print("\nMost common errors:")
        for error_type, count in sorted(results["error_summary"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {error_type}: {count}")

    if results["invalid_files"] > 0 and results["errors_by_file"]:
        print("\nSample invalid files (first 5):")
        for filepath in list(results["errors_by_file"].keys())[:5]:
            print(f"\n  {filepath}")
            for error in results["errors_by_file"][filepath][:3]:
                print(f"    - {error}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate canonical JSON files"
    )
    parser.add_argument(
        '--code',
        help='Validate only a specific code'
    )
    parser.add_argument(
        '--dir',
        default='.',
        help='Base directory (default: current)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show all errors'
    )

    args = parser.parse_args()

    # Check if canonical directory exists
    canonical_path = Path(args.dir) / "casecore-runtime" / "legal" / "canonical"
    if not canonical_path.exists():
        print(f"Canonical directory not found: {canonical_path}")
        print("Make sure you have output files from the scraper.")
        sys.exit(1)

    # Change to base directory for relative paths
    if args.dir != '.':
        import os
        os.chdir(args.dir)

    # Validate
    results = validate_directory(args.code)

    # Print summary
    print_summary(results)

    # Print details if verbose
    if args.verbose and results["errors_by_file"]:
        print("\n" + "=" * 70)
        print("DETAILED ERRORS")
        print("=" * 70)
        for filepath, errors in sorted(results["errors_by_file"].items())[:20]:
            print(f"\n{filepath}")
            for error in errors:
                print(f"  - {error}")

    # Exit code
    sys.exit(0 if results["invalid_files"] == 0 else 1)


if __name__ == '__main__':
    main()

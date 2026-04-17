import json
import os
import re
import argparse
from pathlib import Path

DIVISION_MAP = {
    "1":  {"title": "Preliminary Provisions and Construction"},
    "2":  {"title": "Words and Phrases Defined"},
    "3":  {"title": "General Provisions"},
    "4":  {"title": "Judicial Notice"},
    "5":  {"title": "Burden of Proof; Burden of Producing Evidence; Presumptions and Inferences"},
    "6":  {"title": "Witnesses"},
    "7":  {"title": "Opinion Testimony and Scientific Evidence"},
    "8":  {"title": "Privileges"},
    "9":  {"title": "Evidence Affected or Excluded by Extrinsic Policies"},
    "10": {"title": "Hearsay Evidence"},
    "11": {"title": "Writings"},
}

SECTION_DIVISION_RANGES = [
    (1,    99,   "1"),
    (100,  299,  "2"),
    (300,  449,  "3"),
    (450,  460,  "4"),
    (500,  699,  "5"),
    (700,  999,  "6"),
    (1000, 1199, "8"),
    (1200, 1399, "10"),
    (1400, 1999, "11"),
    (2000, 2999, "3"),
]

def section_to_division(section_num):
    for low, high, div in SECTION_DIVISION_RANGES:
        if low <= section_num <= high:
            return div
    return "unknown"

def normalize_tag(tag):
    tag = tag.strip().lower()
    tag = re.sub(r"[\s\-]+", "_", tag)
    tag = re.sub(r"[^a-z0-9_]", "", tag)
    return tag

RULE_TYPE_KEYWORDS = {
    "admissibility":     ["inadmissible", "admissible", "excluded", "admitted"],
    "hearsay_exception": ["hearsay", "out-of-court", "declarant", "statement"],
    "authentication":    ["authenticate", "authentication", "genuineness", "original", "copy"],
    "privilege":         ["privilege", "confidential", "attorney", "physician", "spousal"],
    "presumption":       ["presumption", "presumed", "inference", "inferred"],
    "burden":            ["burden of proof", "burden of producing", "preponderance", "clear and convincing"],
    "relevance":         ["relevant", "relevance", "material", "probative", "prejudicial"],
    "judicial_notice":   ["judicial notice", "court shall", "court may notice"],
    "expert_opinion":    ["expert", "opinion", "qualified", "scientific"],
    "best_evidence":     ["original", "duplicate", "secondary evidence", "best evidence"],
}

def infer_rule_type(text, tags):
    text_lower = text.lower()
    tag_str = " ".join(tags).lower()
    combined = text_lower + " " + tag_str
    scores = {}
    for rule_type, keywords in RULE_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[rule_type] = score
    if not scores:
        return "general"
    return max(scores, key=scores.get)

def normalize_record(raw, source_filename):
    section_str = str(raw.get("section", "")).strip()
    try:
        section_num = int(float(section_str))
    except (ValueError, TypeError):
        section_num = 0

    section_id = f"EC-{section_num}" if section_num else f"EC-{source_filename}"
    existing_structure = raw.get("structure", {})
    division = existing_structure.get("division") or section_to_division(section_num)
    division_title = (
        existing_structure.get("division_title")
        or DIVISION_MAP.get(division, {}).get("title", "Unknown Division")
    )

    structure = {
        "division":       division,
        "division_title": division_title,
        "chapter":        existing_structure.get("chapter", None),
        "chapter_title":  existing_structure.get("chapter_title", None),
        "article":        existing_structure.get("article", None),
        "article_title":  existing_structure.get("article_title", None),
    }

    raw_tags = raw.get("tags", [])
    tags = list(dict.fromkeys(normalize_tag(t) for t in raw_tags if t))

    raw_source = raw.get("source", {})
    source = {
        "type":           raw_source.get("type", "ca_legislature"),
        "jurisdiction":   raw_source.get("jurisdiction", "California"),
        "url":            raw_source.get("url", "https://leginfo.legislature.ca.gov"),
        "editorial_note": raw_source.get("editorial_note", None),
    }

    text = raw.get("text", "")
    rule_type_inferred = infer_rule_type(text, tags)

    normalized = {
        "section_id":              section_id,
        "code":                    raw.get("code", "EVID"),
        "section":                 section_str,
        "title":                   raw.get("title", "").strip(),
        "text":                    text.strip(),
        "notes":                   raw.get("notes", None),
        "rule_type":               rule_type_inferred,
        "rule_type_confidence":    "heuristic",
        "applies_to":              [],
        "evidentiary_standard":    None,
        "foundation_requirements": [],
        "cross_refs":              [],
        "coa_relevance":           [],
        "exclusion_grounds":       [],
        "tags":                    tags,
        "structure":               structure,
        "canonical_type":          raw.get("canonical_type", "source"),
        "source":                  source,
        "effective_date":          raw.get("effective_date", None),
        "schema_version":          "1.0",
        "pass1_complete":          True,
        "pass2_complete":          False,
        "source_file":             source_filename,
    }
    return normalized

def main():
    parser = argparse.ArgumentParser(description="CAEC Pass 1 Normalize")
    parser.add_argument("--input",   required=True)
    parser.add_argument("--output",  required=True)
    parser.add_argument("--pattern", default="EVID_*.json")
    args = parser.parse_args()

    input_dir  = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob(args.pattern))
    if not files:
        print(f"No files matching '{args.pattern}' in {input_dir}")
        return

    results = {"processed": 0, "errors": 0, "rule_type_counts": {}}

    for fp in files:
        try:
            raw = json.loads(fp.read_text(encoding="utf-8-sig"))
            normalized = normalize_record(raw, fp.name)
            out_path = output_dir / (fp.stem + "_normalized.json")
            out_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
            rt = normalized["rule_type"]
            results["rule_type_counts"][rt] = results["rule_type_counts"].get(rt, 0) + 1
            results["processed"] += 1
            print(f"  OK  {fp.name:45s} rule_type: {rt}")
        except Exception as e:
            results["errors"] += 1
            print(f"  ERR {fp.name}: {e}")

    print(f"\n── Pass 1 complete ──────────────────────")
    print(f"   Processed : {results['processed']}")
    print(f"   Errors    : {results['errors']}")
    print(f"   Rule types:")
    for rt, count in sorted(results["rule_type_counts"].items(), key=lambda x: -x[1]):
        print(f"     {rt:30s} {count}")
    print(f"\nOutput: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
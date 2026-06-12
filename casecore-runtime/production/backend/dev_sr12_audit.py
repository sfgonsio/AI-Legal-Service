"""
SR-12 audit: the ingest surface must not import authority-resolution modules.

Scans the ingest-side files for forbidden imports. Exits non-zero on any
violation so CI can enforce it.

Run:
  python casecore-runtime/production/backend/dev_sr12_audit.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)

INGEST_SURFACE = [
    "brain/ingest_pipeline.py",
    "brain/actor_extractor.py",
    "brain/content_extractors.py",
    "brain/interview_processor.py",
    "brain/timeline_extractor.py",
    "brain/timeline_builder.py",
    "brain/timeline_legal_mapper.py",
    "routes/documents.py",
    "routes/actors.py",
    "routes/interviews.py",
    "routes/timeline.py",
]

FORBIDDEN_SUBSTRINGS = [
    "authority_resolver",
    "brain.recompute",
    "from recompute",
    "resolve_authority",
    "case_authority",  # decision-write helpers
    "COAEngine", "burden_builder", "remedy_derivation", "complaint_parse",
]


def main() -> int:
    violations = []
    for rel in INGEST_SURFACE:
        path = HERE / rel
        if not path.is_file():
            violations.append(f"{rel}: MISSING FILE")
            continue
        src = path.read_text(encoding="utf-8")
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle in src:
                # allow the string to appear inside comment lines that note SR-12
                # explicitly, so the contract note itself doesn't trigger a false
                # positive.
                ok_lines = 0
                bad_lines = 0
                for line in src.splitlines():
                    if needle in line:
                        stripped = line.strip()
                        if stripped.startswith("#") and "SR-" in stripped:
                            ok_lines += 1
                        else:
                            bad_lines += 1
                if bad_lines:
                    violations.append(f"{rel}: forbidden '{needle}' ({bad_lines} non-comment line(s))")

    if violations:
        print("FAIL: SR-12 violations detected")
        for v in violations:
            print("  -", v)
        return 1
    print("PASS: SR-12 audit clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())

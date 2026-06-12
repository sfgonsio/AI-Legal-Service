"""
Burden mapping — per COA, per element.

For each COA element, assign:
  - burden_of_production      (who must come forward with evidence)
  - burden_of_persuasion      (who must convince the factfinder)
  - standard                  (preponderance | clear and convincing | beyond reasonable doubt)

Follows settled California civil-practice defaults. Where a statute shifts
the burden (e.g. CACI 1900 pattern, or Civ. Code §3294 "clear and convincing"
for punitive), the defaults here reflect that.

No authority-resolver calls. This module computes burdens deterministically
from the COA element catalog (brain.coa_engine._COA_DEFS).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


# Default allocation: plaintiff carries both BoP and BoPP on all elements of
# an affirmative claim. Standard is preponderance of the evidence. Known
# exceptions are listed below.
_DEFAULT_BOP = "plaintiff"
_DEFAULT_BOPP = "plaintiff"
_DEFAULT_STANDARD = "preponderance of the evidence"

# Known exceptions (Cal. civil).
# CACI 1900 Intentional Misrepresentation: plaintiff carries all five
# elements; standard remains preponderance for liability, BUT punitive
# damages against same defendant require clear and convincing evidence
# (Civ. Code §3294). That's handled in remedies, not here.
# CACI 4100 Breach of Fiduciary Duty: plaintiff carries all elements.
# CACI 2100 Conversion: plaintiff carries all elements; "substantial factor"
# causation is implicit in harm element.
# No affirmative defenses are represented in v1 (e.g. statute of limitations,
# contributory negligence). Those carry defendant's burden and would be
# added alongside defenses in a later pass.


@dataclass
class ElementBurden:
    element_id: str
    label: str
    burden_of_production: str           # plaintiff | defendant | either
    burden_of_persuasion: str           # plaintiff | defendant | shifting
    standard: str
    supporting_event_ids: List[str] = field(default_factory=list)
    supporting_document_ids: List[int] = field(default_factory=list)
    status: str = "UNSUPPORTED"
    rationale: str = ""


@dataclass
class CoaBurdenMap:
    caci_id: str
    name: str
    authority_reference: str
    element_burdens: List[ElementBurden]


def map_burdens(coa_candidates) -> List[CoaBurdenMap]:
    """
    Build burden maps from CoaCandidate objects (see coa_engine).
    """
    out: List[CoaBurdenMap] = []
    for c in coa_candidates:
        elems: List[ElementBurden] = []
        for s in c.elements:
            eb = ElementBurden(
                element_id=s.element_id,
                label=s.label,
                burden_of_production=_DEFAULT_BOP,
                burden_of_persuasion=_DEFAULT_BOPP,
                standard=_DEFAULT_STANDARD,
                supporting_event_ids=list(s.supporting_event_ids),
                supporting_document_ids=list(s.supporting_document_ids),
                status=s.status,
                rationale=(
                    f"{_DEFAULT_BOP.capitalize()} carries burden of production and persuasion "
                    f"on element '{s.element_id}' by {_DEFAULT_STANDARD}; "
                    f"element status: {s.status}."
                ),
            )
            elems.append(eb)
        out.append(CoaBurdenMap(
            caci_id=c.caci_id,
            name=c.name,
            authority_reference=c.authority["reference"],
            element_burdens=elems,
        ))
    return out


def serialize(maps: List[CoaBurdenMap]) -> List[Dict[str, Any]]:
    return [asdict(m) for m in maps]

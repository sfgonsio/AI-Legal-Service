"""
COA Engine — Cause of Action Matching & Burden Tracking

Core legal intelligence layer that:
  1. Maps client narrative to candidate Causes of Action
  2. Retrieves burden elements for each COA from canonical authority store
  3. Tracks evidence strength per burden element
  4. Generates targeted questions to fill burden gaps
  5. Assesses overall COA viability

Uses the canonical store:
  - CACI (jury instructions) → COA elements, burden of proof
  - EVID (evidence code) → admissibility rules, presumptions
  - BPC/CIV/CCP/etc. → statutory authority

Architecture:
  COAMatcher  → identifies candidate COAs from narrative
  BurdenTracker → tracks elements per COA, maps evidence
  QuestionGenerator → creates legally-targeted questions
"""

import json
import os
import glob
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from src.utils.ids import new_id


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class EvidenceStrength(str, Enum):
    STRONG = "strong"           # Client has clear, admissible evidence
    MODERATE = "moderate"       # Evidence exists but may need corroboration
    WEAK = "weak"               # Minimal or circumstantial evidence
    GAP = "gap"                 # No evidence identified yet
    CONTRADICTED = "contradicted"  # Evidence conflicts with this element
    NOT_ASSESSED = "not_assessed"


class BurdenElement(BaseModel):
    """A single element that must be proven for a COA."""
    element_id: str
    coa_id: str
    element_number: int
    description: str
    legal_standard: str = "preponderance"  # "preponderance", "clear_and_convincing", "beyond_reasonable_doubt"
    evidence_strength: EvidenceStrength = EvidenceStrength.NOT_ASSESSED
    supporting_facts: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    authority_refs: list[str] = Field(default_factory=list)  # CACI/EVID section refs


class Remedy(BaseModel):
    """An available remedy for a COA."""
    remedy_id: str
    remedy_type: str  # "compensatory", "punitive", "injunctive", "declaratory", "statutory"
    description: str
    statutory_basis: Optional[str] = None
    estimated_range: Optional[str] = None
    conditions: list[str] = Field(default_factory=list)


class CauseOfAction(BaseModel):
    """A candidate Cause of Action with burden elements and remedies."""
    coa_id: str
    case_id: str
    name: str
    description: str
    caci_instruction_id: Optional[str] = None
    statutory_basis: list[str] = Field(default_factory=list)  # e.g., ["CIV 1550", "CCP 340"]
    burden_elements: list[BurdenElement] = Field(default_factory=list)
    remedies: list[Remedy] = Field(default_factory=list)
    viability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = "candidate"  # "candidate", "viable", "strong", "weak", "dismissed"
    identified_at: datetime
    notes: Optional[str] = None


class COAAssessment(BaseModel):
    """Overall assessment of all COAs for a case."""
    assessment_id: str
    case_id: str
    causes_of_action: list[CauseOfAction] = Field(default_factory=list)
    strongest_coa: Optional[str] = None
    total_burden_elements: int = 0
    elements_with_evidence: int = 0
    critical_gaps: list[str] = Field(default_factory=list)
    assessed_at: datetime


# ---------------------------------------------------------------------------
# COA Matcher — maps narrative to candidate COAs
# ---------------------------------------------------------------------------

class COAMatcher:
    """
    Matches client narrative against the canonical authority store
    to identify candidate Causes of Action.

    Uses LLM + authority store lookup for intelligent matching.
    """

    def __init__(self, canonical_base_path: str, llm_provider=None):
        self.canonical_base = canonical_base_path
        self.llm = llm_provider
        self._caci_index: dict[str, dict] = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy-load the CACI index for COA matching."""
        if self._loaded:
            return

        caci_path = os.path.join(self.canonical_base, "caci")
        if os.path.isdir(caci_path):
            for fpath in glob.glob(os.path.join(caci_path, "CACI_*.json")):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    iid = data.get("instruction_id", "")
                    if iid:
                        self._caci_index[iid] = data
                except Exception:
                    continue

        self._loaded = True

    def match_narrative(self, narrative: str, case_context: Optional[dict] = None) -> list[dict]:
        """
        Analyze narrative and return candidate COAs with burden elements.

        Uses LLM to interpret narrative, then cross-references CACI
        instructions and statutory authority to build structured COAs.

        Returns list of COA dicts ready for CauseOfAction model creation.
        """
        self._ensure_loaded()

        # Build context about available authority
        available_series = self._get_available_series_summary()

        system_prompt = f"""You are the COA Engine for CaseCore, a legal case management platform.

Analyze the client narrative and identify all viable Causes of Action (COAs).

For each COA, provide:
1. The COA name and CACI instruction number (if applicable)
2. The specific burden elements that must be proven
3. Available remedies
4. Statutory basis (California codes)

AVAILABLE CACI SERIES IN OUR AUTHORITY STORE:
{available_series}

RULES:
- Only identify COAs supported by the facts in the narrative
- Each burden element must be specific and actionable
- Map to actual CACI instruction numbers where possible
- Include both primary and alternative/secondary COAs
- Consider statute of limitations implications
- All assessments are preliminary — characterize as "candidate"

OUTPUT FORMAT: Return valid JSON:
{{
  "causes_of_action": [
    {{
      "name": "Negligence",
      "description": "Defendant's failure to exercise reasonable care...",
      "caci_instruction_id": "400",
      "statutory_basis": ["CIV 1714"],
      "burden_elements": [
        {{"element_number": 1, "description": "Defendant owed a duty of care to plaintiff", "legal_standard": "preponderance"}},
        {{"element_number": 2, "description": "Defendant breached that duty", "legal_standard": "preponderance"}},
        {{"element_number": 3, "description": "Defendant's breach was a substantial factor in causing harm", "legal_standard": "preponderance"}},
        {{"element_number": 4, "description": "Plaintiff suffered damages", "legal_standard": "preponderance"}}
      ],
      "remedies": [
        {{"remedy_type": "compensatory", "description": "Economic and non-economic damages", "statutory_basis": "CIV 3333"}},
        {{"remedy_type": "punitive", "description": "Punitive damages if malice, oppression, or fraud", "statutory_basis": "CIV 3294", "conditions": ["Must prove malice, oppression, or fraud by clear and convincing evidence"]}}
      ],
      "viability_notes": "Strong if client can establish duty and causation"
    }}
  ],
  "preliminary_assessment": "Brief overall assessment of the case strength",
  "statute_of_limitations_concerns": ["Any SOL issues identified"],
  "recommended_priority": ["COA names in priority order"]
}}"""

        user_msg = f"CLIENT NARRATIVE:\n\n{narrative}"
        if case_context:
            user_msg += f"\n\nCASE CONTEXT:\n{json.dumps(case_context, indent=2, default=str)}"

        raw = self.llm.complete(system_prompt=system_prompt, user_message=user_msg)
        return self._parse_json(raw)

    def get_caci_instruction(self, instruction_id: str) -> Optional[dict]:
        """Look up a CACI instruction from the canonical store."""
        self._ensure_loaded()
        return self._caci_index.get(instruction_id)

    def get_evid_section(self, section: str) -> Optional[dict]:
        """Look up an Evidence Code section from the canonical store."""
        evid_path = os.path.join(self.canonical_base, "evidence_code", f"EVID_{section}.json")
        if os.path.isfile(evid_path):
            with open(evid_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _get_available_series_summary(self) -> str:
        """Build a summary of available CACI series for the LLM."""
        series_map = {}
        for iid in self._caci_index:
            # Extract series number (first digits before any letter)
            num = ""
            for ch in iid:
                if ch.isdigit():
                    num += ch
                else:
                    break
            if num:
                series = (int(num) // 100) * 100
                if series not in series_map:
                    series_map[series] = 0
                series_map[series] += 1

        lines = []
        series_names = {
            100: "Pretrial", 200: "Contracts", 300: "Negligence Elements",
            400: "Negligence", 500: "Medical Negligence", 600: "Motor Vehicle",
            700: "Intentional Torts", 800: "Defamation", 900: "Common Carriers",
            1000: "Premises Liability", 1100: "Products Liability",
            1200: "Dangerous Condition of Public Property", 1300: "Employment",
            1400: "Assault & Battery", 1500: "Sexual Harassment",
            1700: "Wrongful Death", 1800: "Fraud & Deceit",
            1900: "Wrongful Termination", 2000: "Insurance",
            2100: "Public Entity", 2200: "Civil Rights (Constitutional)",
            2400: "Elder Abuse", 2500: "FEHA",
            2600: "Whistleblower", 2700: "Labor Code",
            2800: "Unfair Business Practices", 2900: "Real Property",
            3000: "Civil Rights (Statutory)", 3100: "Trespass & Conversion",
            3500: "Construction", 3600: "Eminent Domain",
            3700: "Damages", 3900: "Damages (cont.)", 3950: "Punitive Damages",
            4000: "Fiduciary Duty", 4100: "Legal Malpractice",
            4300: "Unlawful Detainer", 4500: "Workers Comp",
            4700: "Privacy", 5000: "Concluding Instructions",
        }
        for series in sorted(series_map):
            name = series_names.get(series, f"Series {series}")
            lines.append(f"  Series {series}: {name} ({series_map[series]} instructions)")

        return "\n".join(lines) if lines else "CACI index not loaded"

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_fence = False
            for line in lines:
                if line.strip().startswith("```") and not in_fence:
                    in_fence = True
                    continue
                elif line.strip() == "```" and in_fence:
                    break
                elif in_fence:
                    json_lines.append(line)
            text = "\n".join(json_lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse", "raw": raw[:500]}


# ---------------------------------------------------------------------------
# Burden Tracker — tracks element satisfaction per COA
# ---------------------------------------------------------------------------

class BurdenTracker:
    """
    Tracks burden element satisfaction across all COAs for a case.

    As the interview progresses, evidence and facts are mapped to
    specific burden elements. The tracker maintains a live scorecard
    of what's proven, what's weak, and what's missing.
    """

    def __init__(self):
        self._assessments: dict[str, COAAssessment] = {}

    def create_assessment(self, case_id: str, matched_coas: dict) -> COAAssessment:
        """
        Build a COAAssessment from COAMatcher output.
        """
        now = datetime.now(timezone.utc)
        coas = []

        for coa_data in matched_coas.get("causes_of_action", []):
            coa_id = new_id()
            elements = []
            for elem in coa_data.get("burden_elements", []):
                elements.append(BurdenElement(
                    element_id=new_id(),
                    coa_id=coa_id,
                    element_number=elem.get("element_number", 0),
                    description=elem.get("description", ""),
                    legal_standard=elem.get("legal_standard", "preponderance"),
                ))

            remedies = []
            for rem in coa_data.get("remedies", []):
                remedies.append(Remedy(
                    remedy_id=new_id(),
                    remedy_type=rem.get("remedy_type", "compensatory"),
                    description=rem.get("description", ""),
                    statutory_basis=rem.get("statutory_basis"),
                    conditions=rem.get("conditions", []),
                ))

            coas.append(CauseOfAction(
                coa_id=coa_id,
                case_id=case_id,
                name=coa_data.get("name", "Unknown"),
                description=coa_data.get("description", ""),
                caci_instruction_id=coa_data.get("caci_instruction_id"),
                statutory_basis=coa_data.get("statutory_basis", []),
                burden_elements=elements,
                remedies=remedies,
                status="candidate",
                identified_at=now,
                notes=coa_data.get("viability_notes"),
            ))

        total_elements = sum(len(c.burden_elements) for c in coas)
        assessment = COAAssessment(
            assessment_id=new_id(),
            case_id=case_id,
            causes_of_action=coas,
            total_burden_elements=total_elements,
            elements_with_evidence=0,
            assessed_at=now,
        )

        self._assessments[case_id] = assessment
        return assessment

    def update_element(
        self,
        case_id: str,
        element_id: str,
        strength: EvidenceStrength,
        facts: Optional[list[str]] = None,
        evidence_ids: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> Optional[BurdenElement]:
        """Update the evidence strength for a specific burden element."""
        assessment = self._assessments.get(case_id)
        if not assessment:
            return None

        for coa in assessment.causes_of_action:
            for elem in coa.burden_elements:
                if elem.element_id == element_id:
                    elem.evidence_strength = strength
                    if facts:
                        elem.supporting_facts.extend(facts)
                    if evidence_ids:
                        elem.supporting_evidence_ids.extend(evidence_ids)
                    if notes:
                        elem.notes = notes
                    self._recalculate_viability(assessment)
                    return elem
        return None

    def map_response_to_elements(
        self, case_id: str, response_text: str, llm_provider=None
    ) -> list[dict]:
        """
        Use LLM to map a client response to specific burden elements.

        Returns list of element updates: [{"element_id": ..., "strength": ..., "facts": [...]}]
        """
        assessment = self._assessments.get(case_id)
        if not assessment or not llm_provider:
            return []

        # Build element map for the LLM
        element_map = []
        for coa in assessment.causes_of_action:
            for elem in coa.burden_elements:
                element_map.append({
                    "element_id": elem.element_id,
                    "coa": coa.name,
                    "element_number": elem.element_number,
                    "description": elem.description,
                    "current_strength": elem.evidence_strength.value,
                })

        system_prompt = """You are the Evidence Mapper for CaseCore.

Given a client's response during intake interview, determine which burden elements
the response provides evidence for (or against).

RULES:
- Only map evidence that directly relates to a specific element
- Assess strength honestly: "strong" only if the response provides clear, direct evidence
- Note any contradictions
- Extract specific factual statements that support each element

OUTPUT FORMAT: Return valid JSON:
{
  "element_updates": [
    {"element_id": "...", "strength": "strong|moderate|weak|contradicted", "facts": ["specific fact extracted"], "notes": "why this maps to this element"}
  ]
}"""

        user_msg = (
            f"CLIENT RESPONSE:\n{response_text}\n\n"
            f"BURDEN ELEMENTS TO MAP AGAINST:\n{json.dumps(element_map, indent=2)}"
        )

        raw = llm_provider.complete(system_prompt=system_prompt, user_message=user_msg)
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            # Handle code fences
            if isinstance(raw, str) and raw.strip().startswith("```"):
                lines = raw.strip().split("\n")
                json_text = "\n".join(l for l in lines if not l.strip().startswith("```"))
                parsed = json.loads(json_text)

            updates = parsed.get("element_updates", [])

            # Apply updates
            for update in updates:
                try:
                    strength = EvidenceStrength(update.get("strength", "not_assessed"))
                except ValueError:
                    strength = EvidenceStrength.NOT_ASSESSED

                self.update_element(
                    case_id=case_id,
                    element_id=update["element_id"],
                    strength=strength,
                    facts=update.get("facts", []),
                    notes=update.get("notes"),
                )

            return updates
        except Exception:
            return []

    def get_assessment(self, case_id: str) -> Optional[COAAssessment]:
        return self._assessments.get(case_id)

    def get_gap_elements(self, case_id: str) -> list[BurdenElement]:
        """Get all burden elements that still need evidence."""
        assessment = self._assessments.get(case_id)
        if not assessment:
            return []

        gaps = []
        for coa in assessment.causes_of_action:
            for elem in coa.burden_elements:
                if elem.evidence_strength in (EvidenceStrength.GAP, EvidenceStrength.NOT_ASSESSED):
                    gaps.append(elem)
        return gaps

    def get_scorecard(self, case_id: str) -> dict:
        """Get a summary scorecard of COA coverage."""
        assessment = self._assessments.get(case_id)
        if not assessment:
            return {}

        scorecard = {"coas": []}
        for coa in assessment.causes_of_action:
            total = len(coa.burden_elements)
            proven = len([e for e in coa.burden_elements if e.evidence_strength in (EvidenceStrength.STRONG, EvidenceStrength.MODERATE)])
            gaps = len([e for e in coa.burden_elements if e.evidence_strength in (EvidenceStrength.GAP, EvidenceStrength.NOT_ASSESSED)])
            weak = len([e for e in coa.burden_elements if e.evidence_strength == EvidenceStrength.WEAK])
            contradicted = len([e for e in coa.burden_elements if e.evidence_strength == EvidenceStrength.CONTRADICTED])

            scorecard["coas"].append({
                "coa_id": coa.coa_id,
                "name": coa.name,
                "viability_score": coa.viability_score,
                "status": coa.status,
                "elements_total": total,
                "elements_proven": proven,
                "elements_gap": gaps,
                "elements_weak": weak,
                "elements_contradicted": contradicted,
                "coverage_pct": round((proven / total * 100) if total else 0, 1),
                "remedies_count": len(coa.remedies),
            })

        return scorecard

    def _recalculate_viability(self, assessment: COAAssessment):
        """Recalculate viability scores and status for all COAs."""
        total_with_evidence = 0

        for coa in assessment.causes_of_action:
            total = len(coa.burden_elements)
            if total == 0:
                coa.viability_score = 0.0
                continue

            score = 0.0
            for elem in coa.burden_elements:
                if elem.evidence_strength == EvidenceStrength.STRONG:
                    score += 1.0
                elif elem.evidence_strength == EvidenceStrength.MODERATE:
                    score += 0.7
                elif elem.evidence_strength == EvidenceStrength.WEAK:
                    score += 0.3
                elif elem.evidence_strength == EvidenceStrength.CONTRADICTED:
                    score -= 0.5

                if elem.evidence_strength not in (EvidenceStrength.GAP, EvidenceStrength.NOT_ASSESSED):
                    total_with_evidence += 1

            coa.viability_score = round(max(0.0, min(1.0, score / total)), 2)

            # Update status
            if coa.viability_score >= 0.7:
                coa.status = "strong"
            elif coa.viability_score >= 0.4:
                coa.status = "viable"
            elif coa.viability_score > 0.0:
                coa.status = "weak"
            else:
                coa.status = "candidate"

        assessment.elements_with_evidence = total_with_evidence
        assessment.assessed_at = datetime.now(timezone.utc)

        # Identify strongest COA
        if assessment.causes_of_action:
            strongest = max(assessment.causes_of_action, key=lambda c: c.viability_score)
            assessment.strongest_coa = strongest.coa_id

        # Identify critical gaps
        assessment.critical_gaps = []
        for coa in assessment.causes_of_action:
            if coa.status in ("strong", "viable"):
                for elem in coa.burden_elements:
                    if elem.evidence_strength in (EvidenceStrength.GAP, EvidenceStrength.NOT_ASSESSED):
                        assessment.critical_gaps.append(
                            f"{coa.name} Element {elem.element_number}: {elem.description}"
                        )


# ---------------------------------------------------------------------------
# Question Generator — creates legally-targeted questions
# ---------------------------------------------------------------------------

class QuestionGenerator:
    """
    Generates interview questions targeted at specific burden elements.

    Unlike generic intake questions, these are designed to elicit evidence
    and facts that directly support (or refute) specific legal elements.
    """

    def __init__(self, llm_provider=None):
        self.llm = llm_provider

    def generate_targeted_questions(
        self,
        gap_elements: list[BurdenElement],
        coa_context: list[CauseOfAction],
        conversation_history: list[dict],
        max_questions: int = 3,
    ) -> list[dict]:
        """
        Generate questions targeting specific burden element gaps.

        Returns: [{"question": str, "target_element_id": str, "target_coa": str, "priority": str}]
        """
        if not self.llm or not gap_elements:
            return []

        # Build element context
        element_context = []
        for elem in gap_elements[:10]:  # Limit to top 10 gaps
            coa_name = "Unknown"
            for coa in coa_context:
                if coa.coa_id == elem.coa_id:
                    coa_name = coa.name
                    break
            element_context.append({
                "element_id": elem.element_id,
                "coa_name": coa_name,
                "element_number": elem.element_number,
                "description": elem.description,
                "legal_standard": elem.legal_standard,
            })

        system_prompt = f"""You are a legal intake interviewer for CaseCore.

Generate {max_questions} targeted questions to ask the client. Each question should
directly target a specific burden element that currently lacks evidence.

RULES:
- Questions must be conversational and empathetic, not interrogatory
- Each question should target ONE specific burden element
- Questions should elicit concrete, admissible evidence (dates, documents, witnesses, communications)
- Prioritize elements from the strongest COAs first
- Don't repeat questions already asked in the conversation
- Frame questions to reveal EVIDENCE, not just narrative

GOOD: "Do you have any emails or text messages from your supervisor discussing the safety concern?"
BAD: "Tell me more about what happened."

OUTPUT FORMAT: Return valid JSON:
{{
  "questions": [
    {{
      "question": "...",
      "target_element_id": "...",
      "target_coa": "COA name",
      "target_element_desc": "what this question helps prove",
      "evidence_type_sought": "documents|testimony|records|communications|physical",
      "priority": "critical|high|medium"
    }}
  ]
}}"""

        user_msg = (
            f"BURDEN ELEMENTS NEEDING EVIDENCE:\n{json.dumps(element_context, indent=2)}\n\n"
            f"RECENT CONVERSATION:\n{json.dumps(conversation_history[-6:], indent=2, default=str)}"
        )

        raw = self.llm.complete(system_prompt=system_prompt, user_message=user_msg)

        try:
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                json_lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(json_lines)
            parsed = json.loads(text)
            return parsed.get("questions", [])
        except Exception:
            # Fallback: generate basic questions from element descriptions
            fallback = []
            for elem in gap_elements[:max_questions]:
                fallback.append({
                    "question": f"Can you tell me more about: {elem.description}? Do you have any documents, communications, or witnesses that relate to this?",
                    "target_element_id": elem.element_id,
                    "target_coa": elem.coa_id,
                    "target_element_desc": elem.description,
                    "priority": "high",
                })
            return fallback

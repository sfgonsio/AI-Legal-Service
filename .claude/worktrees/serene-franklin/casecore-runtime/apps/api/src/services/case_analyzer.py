"""
Case Analyzer — P4/P5 Pipeline: Evidence → Facts → COA → Burden Mapping

Bridges the Evidence Vault (P3) to Legal Mapping (P5) by:
  P4 — Fact Derivation: Extract candidate facts from vault derivations
  P5 — Legal Mapping:   Match facts to COAs, map burden elements, score coverage

This is the "brain" pipeline that takes raw evidence artifacts and
produces the ELEMENT_COVERAGE_MATRIX the attorney reviews.

Flow:
  vault.list_derivations(case_id)
    → extract_facts()        # P4: derive FACT_CANDIDATES from transcripts/text
    → identify_coas()        # P5a: match facts to COAs via CACI
    → map_burdens()          # P5b: map facts to burden elements
    → score_coverage()       # P5c: produce ELEMENT_COVERAGE_MATRIX
    → identify_gaps()        # Gap analysis for attorney review

All outputs are PROPOSAL-layer — attorney approval required before
promotion to canonical/trusted status.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from src.utils.ids import new_id
from src.services.evidence_vault import (
    EvidenceVault, get_evidence_vault,
    DerivationMethod, DerivationRecord, SourceRecord, TheoryType,
)
from src.services.coa_engine import (
    COAMatcher, BurdenTracker, QuestionGenerator,
    COAAssessment, CauseOfAction, BurdenElement, Remedy,
    EvidenceStrength,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# P4 Models — Fact Derivation
# ---------------------------------------------------------------------------

class FactCandidate(BaseModel):
    """A candidate fact derived from evidence. Not canonical until promoted."""
    fact_id: str
    case_id: str
    statement: str  # The factual assertion
    source_evidence_id: str  # Vault evidence ID
    source_derivation_id: Optional[str] = None  # Which derivation produced this
    source_type: str  # "transcript", "document", "image_ocr", "metadata"
    source_location: Optional[str] = None  # timestamp, page number, etc.
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    entities_mentioned: list[str] = Field(default_factory=list)
    temporal_reference: Optional[str] = None  # date/time mentioned
    tags: list[str] = Field(default_factory=list)
    status: str = "candidate"  # "candidate", "promoted", "rejected", "disputed"
    derived_at: str


class EventCandidate(BaseModel):
    """A candidate event on the case timeline."""
    event_id: str
    case_id: str
    description: str
    date_reference: Optional[str] = None
    date_precision: str = "unknown"  # "exact", "day", "month", "approximate", "unknown"
    location: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    source_evidence_ids: list[str] = Field(default_factory=list)
    event_type: str = "general"  # "incident", "communication", "agreement", "breach", "discovery"
    tags: list[str] = Field(default_factory=list)
    status: str = "candidate"


class CoverageMatrix(BaseModel):
    """
    Element Coverage Matrix — the key artifact attorneys review.
    Shows each COA, its burden elements, and evidence coverage status.
    """
    matrix_id: str
    case_id: str
    run_id: str
    generated_at: str
    coas: list[dict] = Field(default_factory=list)
    # Each COA: {coa_id, name, caci_id, viability_score, status, elements: [...]}
    # Each element: {element_id, description, strength, supporting_facts, supporting_evidence, gaps}
    total_elements: int = 0
    elements_covered: int = 0
    elements_gap: int = 0
    critical_gaps: list[dict] = Field(default_factory=list)
    fact_count: int = 0
    event_count: int = 0
    source_evidence_count: int = 0
    status: str = "proposal"  # "proposal", "attorney_reviewed", "approved"


# ---------------------------------------------------------------------------
# Case Analyzer Service
# ---------------------------------------------------------------------------

class CaseAnalyzer:
    """
    Orchestrates P4 → P5 pipeline for a case.

    Takes evidence from the vault, derives facts, identifies COAs,
    maps burden elements, and produces the coverage matrix.
    """

    def __init__(
        self,
        vault: EvidenceVault,
        coa_matcher: COAMatcher,
        burden_tracker: BurdenTracker,
        question_generator: QuestionGenerator,
        llm_provider=None,
    ):
        self.vault = vault
        self.coa_matcher = coa_matcher
        self.burden_tracker = burden_tracker
        self.question_gen = question_generator
        self.llm = llm_provider

        # Case-scoped storage
        self._facts: dict[str, list[FactCandidate]] = {}  # case_id → facts
        self._events: dict[str, list[EventCandidate]] = {}  # case_id → events
        self._matrices: dict[str, CoverageMatrix] = {}  # case_id → latest matrix

    # ------------------------------------------------------------------
    # P4 — Fact Derivation
    # ------------------------------------------------------------------

    def derive_facts(self, case_id: str) -> list[FactCandidate]:
        """
        Extract candidate facts from all evidence derivations in the vault.

        Processes transcripts, text extractions, and metadata to produce
        structured fact candidates with source links.
        """
        sources = self.vault.list_sources(case_id)
        if not sources:
            logger.warning(f"No evidence in vault for case {case_id}")
            return []

        all_facts = []

        for source in sources:
            derivations = self.vault.list_derivations(
                source_evidence_id=source.evidence_id
            )

            # Gather all text content from derivations
            for deriv in derivations:
                text_content = None
                source_type = deriv.artifact_type

                if deriv.artifact_type in ("transcript", "extracted_text"):
                    text_content = deriv.artifact_inline
                    if not text_content and deriv.artifact_path:
                        art_path = self.vault.get_derivation_artifact_path(
                            deriv.derivation_id
                        )
                        if art_path:
                            try:
                                with open(art_path, "r", encoding="utf-8") as f:
                                    text_content = f.read()
                            except Exception:
                                pass

                elif deriv.artifact_type == "video_metadata":
                    # Extract useful metadata facts (duration, etc.)
                    if deriv.artifact_inline:
                        try:
                            meta = json.loads(deriv.artifact_inline)
                            all_facts.append(FactCandidate(
                                fact_id=new_id(),
                                case_id=case_id,
                                statement=f"Video file '{source.original_filename}' is {meta.get('duration', 0):.1f} seconds long, {meta.get('width', 0)}x{meta.get('height', 0)} resolution",
                                source_evidence_id=source.evidence_id,
                                source_derivation_id=deriv.derivation_id,
                                source_type="metadata",
                                confidence=1.0,
                                tags=["metadata", "video"],
                                derived_at=datetime.now(timezone.utc).isoformat(),
                            ))
                        except Exception:
                            pass
                    continue

                if not text_content or len(text_content.strip()) < 20:
                    continue

                # Use LLM to extract structured facts from text
                facts = self._extract_facts_from_text(
                    text=text_content,
                    source_evidence_id=source.evidence_id,
                    source_derivation_id=deriv.derivation_id,
                    source_type=source_type,
                    source_filename=source.original_filename,
                    case_id=case_id,
                    time_start=deriv.source_time_start,
                    time_end=deriv.source_time_end,
                )
                all_facts.extend(facts)

        self._facts[case_id] = all_facts
        logger.info(f"Derived {len(all_facts)} fact candidates for case {case_id}")
        return all_facts

    def _extract_facts_from_text(
        self,
        text: str,
        source_evidence_id: str,
        source_derivation_id: str,
        source_type: str,
        source_filename: str,
        case_id: str,
        time_start: Optional[float] = None,
        time_end: Optional[float] = None,
    ) -> list[FactCandidate]:
        """Use LLM to extract structured facts from text content."""
        if not self.llm:
            # Fallback: treat the whole text as a single fact
            return [FactCandidate(
                fact_id=new_id(),
                case_id=case_id,
                statement=text[:1000],
                source_evidence_id=source_evidence_id,
                source_derivation_id=source_derivation_id,
                source_type=source_type,
                confidence=0.5,
                derived_at=datetime.now(timezone.utc).isoformat(),
            )]

        system_prompt = """You are the Fact Derivation engine for CaseCore, a legal case management platform.

Extract individual factual statements from the provided text. Each fact should be:
1. A single, specific, testable assertion
2. Relevant to potential legal claims
3. Tagged with entities (people, places, organizations) mentioned
4. Tagged with any temporal references (dates, times, durations)
5. Assessed for confidence based on specificity and clarity

Focus on facts that relate to:
- Who did what to whom
- When events occurred
- What was communicated (threats, promises, agreements)
- Physical evidence described (injuries, property damage, documents)
- Relationships and roles
- Financial information (amounts, transactions)

DO NOT invent facts. Only extract what is explicitly stated or clearly implied.

OUTPUT FORMAT: Return valid JSON:
{
  "facts": [
    {
      "statement": "specific factual assertion",
      "entities": ["Person A", "Company X"],
      "temporal_reference": "March 2024" or null,
      "tags": ["injury", "workplace", "communication"],
      "confidence": 0.8,
      "event_type": "incident|communication|agreement|breach|discovery|general"
    }
  ],
  "events": [
    {
      "description": "what happened",
      "date_reference": "specific date or range" or null,
      "date_precision": "exact|day|month|approximate|unknown",
      "location": "where" or null,
      "participants": ["Person A"],
      "event_type": "incident|communication|agreement|breach|discovery"
    }
  ]
}"""

        # Truncate very long text but keep it meaningful
        text_for_llm = text[:8000]
        time_context = ""
        if time_start is not None:
            time_context = f"\n\nThis content spans from {time_start:.1f}s to {time_end:.1f}s in the source media."

        user_msg = (
            f"SOURCE FILE: {source_filename}\n"
            f"CONTENT TYPE: {source_type}{time_context}\n\n"
            f"TEXT TO ANALYZE:\n{text_for_llm}"
        )

        try:
            raw = self.llm.complete(system_prompt=system_prompt, user_message=user_msg)
            parsed = self._parse_json(raw)

            facts = []
            now = datetime.now(timezone.utc).isoformat()

            for f_data in parsed.get("facts", []):
                facts.append(FactCandidate(
                    fact_id=new_id(),
                    case_id=case_id,
                    statement=f_data.get("statement", ""),
                    source_evidence_id=source_evidence_id,
                    source_derivation_id=source_derivation_id,
                    source_type=source_type,
                    source_location=f"{time_start:.1f}s-{time_end:.1f}s" if time_start is not None else None,
                    confidence=f_data.get("confidence", 0.5),
                    entities_mentioned=f_data.get("entities", []),
                    temporal_reference=f_data.get("temporal_reference"),
                    tags=f_data.get("tags", []),
                    derived_at=now,
                ))

            # Also extract events
            events = self._events.get(case_id, [])
            for e_data in parsed.get("events", []):
                events.append(EventCandidate(
                    event_id=new_id(),
                    case_id=case_id,
                    description=e_data.get("description", ""),
                    date_reference=e_data.get("date_reference"),
                    date_precision=e_data.get("date_precision", "unknown"),
                    location=e_data.get("location"),
                    participants=e_data.get("participants", []),
                    source_evidence_ids=[source_evidence_id],
                    event_type=e_data.get("event_type", "general"),
                ))
            self._events[case_id] = events

            return facts

        except Exception as e:
            logger.error(f"Fact extraction error: {e}")
            return [FactCandidate(
                fact_id=new_id(),
                case_id=case_id,
                statement=text[:500],
                source_evidence_id=source_evidence_id,
                source_derivation_id=source_derivation_id,
                source_type=source_type,
                confidence=0.3,
                derived_at=datetime.now(timezone.utc).isoformat(),
            )]

    # ------------------------------------------------------------------
    # P5 — Legal Mapping
    # ------------------------------------------------------------------

    def identify_coas(self, case_id: str) -> COAAssessment:
        """
        Run COA identification on all derived facts for a case.

        Combines all fact statements into a narrative and runs
        through COAMatcher against the CACI authority store.
        """
        facts = self._facts.get(case_id, [])
        if not facts:
            facts = self.derive_facts(case_id)

        # Build a consolidated narrative from all facts
        narrative_parts = []
        for fact in facts:
            entry = fact.statement
            if fact.temporal_reference:
                entry = f"[{fact.temporal_reference}] {entry}"
            if fact.entities_mentioned:
                entry += f" (Involves: {', '.join(fact.entities_mentioned)})"
            narrative_parts.append(entry)

        combined_narrative = "\n".join(narrative_parts)

        # Build case context from events
        events = self._events.get(case_id, [])
        case_context = {
            "fact_count": len(facts),
            "event_count": len(events),
            "source_evidence_count": len(self.vault.list_sources(case_id)),
            "entities": list(set(
                e for f in facts for e in f.entities_mentioned
            )),
            "event_types": list(set(e.event_type for e in events)),
            "temporal_range": self._get_temporal_range(events),
        }

        # Run COA matching
        logger.info(f"Running COA identification on {len(facts)} facts for case {case_id}")
        matched = self.coa_matcher.match_narrative(combined_narrative, case_context)

        # Create assessment
        assessment = self.burden_tracker.create_assessment(case_id, matched)
        logger.info(
            f"Identified {len(assessment.causes_of_action)} COAs with "
            f"{assessment.total_burden_elements} burden elements"
        )
        return assessment

    def map_evidence_to_burdens(self, case_id: str) -> list[dict]:
        """
        Map all derived facts to specific burden elements.

        For each fact, determine which burden element(s) it supports
        and at what strength level. Updates the BurdenTracker.
        """
        facts = self._facts.get(case_id, [])
        assessment = self.burden_tracker.get_assessment(case_id)
        if not assessment or not facts:
            return []

        # Build a consolidated text from all facts for mapping
        fact_text = "\n".join(
            f"[{f.fact_id[:8]}] {f.statement}" for f in facts
        )

        # Map through LLM
        updates = self.burden_tracker.map_response_to_elements(
            case_id=case_id,
            response_text=fact_text,
            llm_provider=self.llm,
        )

        # Also link evidence IDs to burden elements
        for update in updates:
            elem_id = update.get("element_id")
            if elem_id:
                # Find which facts were mapped to this element
                fact_notes = update.get("notes", "")
                matched_facts = [
                    f for f in facts
                    if any(keyword in f.statement.lower()
                           for keyword in fact_notes.lower().split()[:5])
                ] if fact_notes else []

                evidence_ids = list(set(
                    f.source_evidence_id for f in matched_facts
                ))
                if evidence_ids:
                    self.burden_tracker.update_element(
                        case_id=case_id,
                        element_id=elem_id,
                        strength=EvidenceStrength(update.get("strength", "not_assessed")),
                        evidence_ids=evidence_ids,
                    )

        logger.info(f"Mapped {len(updates)} fact-to-burden links for case {case_id}")
        return updates

    def generate_coverage_matrix(self, case_id: str) -> CoverageMatrix:
        """
        Produce the ELEMENT_COVERAGE_MATRIX — the key attorney-facing artifact.

        Combines COA assessment, burden scores, evidence links, and gap analysis
        into a single reviewable structure.
        """
        assessment = self.burden_tracker.get_assessment(case_id)
        if not assessment:
            raise ValueError(f"No COA assessment found for case {case_id}")

        scorecard = self.burden_tracker.get_scorecard(case_id)
        gaps = self.burden_tracker.get_gap_elements(case_id)
        facts = self._facts.get(case_id, [])
        events = self._events.get(case_id, [])
        sources = self.vault.list_sources(case_id)

        # Build detailed COA entries
        coa_entries = []
        for coa in assessment.causes_of_action:
            elements = []
            for elem in coa.burden_elements:
                # Find supporting facts
                supporting = [
                    {"fact_id": f.fact_id, "statement": f.statement,
                     "source": f.source_evidence_id, "confidence": f.confidence}
                    for f in facts
                    if f.fact_id in elem.supporting_facts
                    or f.source_evidence_id in elem.supporting_evidence_ids
                ]

                elements.append({
                    "element_id": elem.element_id,
                    "element_number": elem.element_number,
                    "description": elem.description,
                    "legal_standard": elem.legal_standard,
                    "strength": elem.evidence_strength.value,
                    "supporting_facts": supporting,
                    "supporting_evidence_ids": elem.supporting_evidence_ids,
                    "authority_refs": elem.authority_refs,
                    "notes": elem.notes,
                    "is_gap": elem.evidence_strength in (
                        EvidenceStrength.GAP, EvidenceStrength.NOT_ASSESSED
                    ),
                })

            coa_entries.append({
                "coa_id": coa.coa_id,
                "name": coa.name,
                "description": coa.description,
                "caci_instruction_id": coa.caci_instruction_id,
                "statutory_basis": coa.statutory_basis,
                "viability_score": coa.viability_score,
                "status": coa.status,
                "elements": elements,
                "remedies": [r.model_dump() for r in coa.remedies],
                "notes": coa.notes,
            })

        total_elements = assessment.total_burden_elements
        covered = assessment.elements_with_evidence
        gap_count = total_elements - covered

        critical_gaps = [
            {
                "coa_name": next(
                    (c.name for c in assessment.causes_of_action if c.coa_id == g.coa_id),
                    "Unknown"
                ),
                "element_number": g.element_number,
                "description": g.description,
                "element_id": g.element_id,
            }
            for g in gaps
        ]

        matrix = CoverageMatrix(
            matrix_id=new_id(),
            case_id=case_id,
            run_id=new_id(),
            generated_at=datetime.now(timezone.utc).isoformat(),
            coas=coa_entries,
            total_elements=total_elements,
            elements_covered=covered,
            elements_gap=gap_count,
            critical_gaps=critical_gaps,
            fact_count=len(facts),
            event_count=len(events),
            source_evidence_count=len(sources),
        )

        self._matrices[case_id] = matrix
        logger.info(
            f"Coverage matrix for {case_id}: "
            f"{covered}/{total_elements} elements covered, "
            f"{len(critical_gaps)} critical gaps"
        )
        return matrix

    # ------------------------------------------------------------------
    # Full Pipeline
    # ------------------------------------------------------------------

    def run_full_analysis(self, case_id: str) -> dict:
        """
        Run the complete P4 → P5 pipeline for a case.

        Returns a summary dict with all artifacts produced.
        Each phase has error handling — partial results are still returned
        so the attorney can see what worked and what needs attention.
        """
        logger.info(f"Starting full case analysis for {case_id}")
        errors = []
        assessment = None
        matrix = None
        burden_updates = []
        questions = []

        # P4: Fact Derivation
        try:
            facts = self.derive_facts(case_id)
            logger.info(f"P4 complete: {len(facts)} fact candidates derived")
        except Exception as e:
            logger.error(f"P4 Fact Derivation failed: {e}", exc_info=True)
            facts = []
            errors.append({"phase": "P4-FactDerivation", "error": str(e)})

        # P5a: COA Identification
        if facts:
            try:
                assessment = self.identify_coas(case_id)
                logger.info(f"P5a complete: {len(assessment.causes_of_action)} COAs identified")
            except Exception as e:
                logger.error(f"P5a COA Identification failed: {e}", exc_info=True)
                errors.append({"phase": "P5a-COAIdentification", "error": str(e)})
                # Fallback: try keyword-based COA matching without LLM
                try:
                    assessment = self._fallback_coa_identification(case_id, facts)
                    if assessment:
                        errors.append({
                            "phase": "P5a-Fallback",
                            "error": "Used keyword matching (LLM unavailable). Results are preliminary."
                        })
                except Exception as e2:
                    logger.error(f"P5a fallback also failed: {e2}")
        else:
            errors.append({"phase": "P5a-COAIdentification", "error": "Skipped — no facts derived in P4"})

        # P5b: Evidence-to-Burden Mapping
        if assessment and assessment.causes_of_action:
            try:
                burden_updates = self.map_evidence_to_burdens(case_id)
                logger.info(f"P5b complete: {len(burden_updates)} burden mappings")
            except Exception as e:
                logger.error(f"P5b Burden Mapping failed: {e}", exc_info=True)
                errors.append({"phase": "P5b-BurdenMapping", "error": str(e)})
        else:
            errors.append({"phase": "P5b-BurdenMapping", "error": "Skipped — no COAs identified in P5a"})

        # P5c: Coverage Matrix
        if assessment and assessment.causes_of_action:
            try:
                matrix = self.generate_coverage_matrix(case_id)
                logger.info(f"P5c complete: {matrix.elements_covered}/{matrix.total_elements} elements covered")
            except Exception as e:
                logger.error(f"P5c Coverage Matrix failed: {e}", exc_info=True)
                errors.append({"phase": "P5c-CoverageMatrix", "error": str(e)})
        else:
            errors.append({"phase": "P5c-CoverageMatrix", "error": "Skipped — no COAs for matrix"})

        # Record theory mappings in vault for provenance
        if matrix:
            try:
                for coa_entry in matrix.coas:
                    for elem in coa_entry.get("elements", []):
                        if elem.get("supporting_evidence_ids"):
                            deriv_ids = []
                            for eid in elem["supporting_evidence_ids"]:
                                derivs = self.vault.list_derivations(source_evidence_id=eid)
                                text_derivs = [
                                    d for d in derivs
                                    if d.artifact_type in ("transcript", "extracted_text")
                                ]
                                deriv_ids.extend(d.derivation_id for d in text_derivs)

                            if deriv_ids:
                                self.vault.add_theory(
                                    case_id=case_id,
                                    theory_type=TheoryType.BURDEN_ELEMENT,
                                    theory_code=f"{coa_entry['caci_instruction_id'] or 'UNKNOWN'}-element-{elem['element_number']}",
                                    theory_description=elem["description"],
                                    supporting_derivation_ids=deriv_ids,
                                    strength=elem.get("strength", "not_assessed"),
                                    relevant_excerpt=elem.get("notes"),
                                    mapped_by="system",
                                )
            except Exception as e:
                logger.error(f"Theory mapping failed: {e}", exc_info=True)
                errors.append({"phase": "TheoryMapping", "error": str(e)})

        # Generate targeted questions for gaps
        if assessment and assessment.causes_of_action:
            try:
                gap_elements = self.burden_tracker.get_gap_elements(case_id)
                questions = self.question_gen.generate_targeted_questions(
                    gap_elements=gap_elements,
                    coa_context=assessment.causes_of_action,
                    conversation_history=[],
                ) if gap_elements else []
            except Exception as e:
                logger.error(f"Question generation failed: {e}")
                errors.append({"phase": "QuestionGeneration", "error": str(e)})

        events = self._events.get(case_id, [])

        status = "analysis_complete" if not errors else "analysis_partial"

        result = {
            "case_id": case_id,
            "status": status,
            "label": "PROPOSAL — Attorney Review Required",
            "facts": {
                "count": len(facts),
                "items": [f.model_dump() for f in facts],
            },
            "events": {
                "count": len(events),
                "items": [e.model_dump() for e in events],
            },
            "coa_assessment": {
                "coas_identified": len(assessment.causes_of_action) if assessment else 0,
                "strongest_coa": assessment.strongest_coa if assessment else None,
                "total_burden_elements": assessment.total_burden_elements if assessment else 0,
                "elements_with_evidence": assessment.elements_with_evidence if assessment else 0,
            },
            "coverage_matrix": matrix.model_dump() if matrix else None,
            "gap_analysis": {
                "critical_gaps": len(matrix.critical_gaps) if matrix else 0,
                "targeted_questions": questions,
            },
            "vault_stats": self.vault.stats(),
        }

        if errors:
            result["errors"] = errors

        return result

    # ------------------------------------------------------------------
    # Fallback: Keyword-based COA identification (no LLM required)
    # ------------------------------------------------------------------

    def _fallback_coa_identification(
        self, case_id: str, facts: list[FactCandidate]
    ) -> Optional[COAAssessment]:
        """
        When LLM is unavailable, use keyword matching against CACI index
        to identify candidate COAs from fact text. Less precise but allows
        the pipeline to produce partial results for attorney review.
        """
        combined_text = " ".join(f.statement.lower() for f in facts)

        # Keyword-to-COA mapping for common California claims
        keyword_coa_map = [
            {
                "keywords": ["terminate", "fired", "wrongful", "retaliat", "whistleblow"],
                "name": "Wrongful Termination in Violation of Public Policy",
                "caci_id": "2430",
                "description": "Employer terminated employee for reasons that violate public policy",
                "elements": [
                    "Plaintiff was employed by defendant",
                    "Defendant discharged plaintiff",
                    "The violation of public policy was a substantial motivating reason for the discharge",
                    "Plaintiff was harmed",
                    "The discharge was a substantial factor in causing harm",
                ],
            },
            {
                "keywords": ["negligent", "negligence", "duty", "breach", "reasonable care"],
                "name": "Negligence",
                "caci_id": "400",
                "description": "Defendant failed to exercise reasonable care causing harm",
                "elements": [
                    "Defendant owed a duty of care to plaintiff",
                    "Defendant breached that duty",
                    "Defendant's breach was a substantial factor in causing harm",
                    "Plaintiff suffered damages",
                ],
            },
            {
                "keywords": ["fraud", "misrepresent", "deceiv", "false", "induc"],
                "name": "Intentional Misrepresentation (Fraud)",
                "caci_id": "1900",
                "description": "Defendant made false representations to induce plaintiff's reliance",
                "elements": [
                    "Defendant represented a material fact as true",
                    "The representation was false",
                    "Defendant knew the representation was false",
                    "Defendant intended plaintiff to rely on the representation",
                    "Plaintiff reasonably relied on the representation",
                    "Plaintiff was harmed by the reliance",
                ],
            },
            {
                "keywords": ["breach", "contract", "agreement", "promise", "violat"],
                "name": "Breach of Contract",
                "caci_id": "303",
                "description": "Defendant failed to perform obligations under a contract",
                "elements": [
                    "A contract existed between plaintiff and defendant",
                    "Plaintiff performed or was excused from performing",
                    "Defendant failed to perform under the contract",
                    "Plaintiff was harmed by the breach",
                ],
            },
            {
                "keywords": ["cannabis", "license", "dispensary", "cultivat", "marijuana", "weed"],
                "name": "Cannabis Regulatory Violation",
                "caci_id": None,
                "description": "Violations related to California cannabis regulations (BPC 26000+)",
                "elements": [
                    "Defendant held or was required to hold a cannabis license",
                    "Defendant violated specific regulatory requirements",
                    "The violation caused harm to plaintiff",
                    "Plaintiff suffered damages as a result",
                ],
            },
            {
                "keywords": ["assault", "batter", "hit", "struck", "attack", "threaten"],
                "name": "Assault and Battery",
                "caci_id": "1300",
                "description": "Defendant intentionally caused harmful or offensive contact",
                "elements": [
                    "Defendant intentionally touched plaintiff",
                    "The touching was harmful or offensive",
                    "Plaintiff did not consent",
                    "Plaintiff was harmed",
                    "Defendant's conduct was a substantial factor in causing harm",
                ],
            },
        ]

        matched_coas = []
        now = datetime.now(timezone.utc)

        for entry in keyword_coa_map:
            hits = sum(1 for kw in entry["keywords"] if kw in combined_text)
            if hits >= 2:  # Need at least 2 keyword matches
                coa_id = new_id()
                elements = [
                    BurdenElement(
                        element_id=new_id(),
                        coa_id=coa_id,
                        element_number=i + 1,
                        description=desc,
                        legal_standard="preponderance",
                    )
                    for i, desc in enumerate(entry["elements"])
                ]
                matched_coas.append(CauseOfAction(
                    coa_id=coa_id,
                    case_id=case_id,
                    name=entry["name"],
                    description=entry["description"],
                    caci_instruction_id=entry["caci_id"],
                    statutory_basis=[],
                    burden_elements=elements,
                    remedies=[],
                    status="candidate",
                    identified_at=now,
                    notes=f"Keyword match ({hits} hits) — LLM refinement needed",
                ))

        if not matched_coas:
            return None

        total_elements = sum(len(c.burden_elements) for c in matched_coas)
        assessment = COAAssessment(
            assessment_id=new_id(),
            case_id=case_id,
            causes_of_action=matched_coas,
            total_burden_elements=total_elements,
            elements_with_evidence=0,
            assessed_at=now,
        )
        self.burden_tracker._assessments[case_id] = assessment
        logger.info(
            f"Fallback COA: {len(matched_coas)} COAs via keyword matching "
            f"({total_elements} elements)"
        )
        return assessment

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_facts(self, case_id: str) -> list[FactCandidate]:
        return self._facts.get(case_id, [])

    def get_events(self, case_id: str) -> list[EventCandidate]:
        return self._events.get(case_id, [])

    def get_matrix(self, case_id: str) -> Optional[CoverageMatrix]:
        return self._matrices.get(case_id)

    def _get_temporal_range(self, events: list[EventCandidate]) -> Optional[dict]:
        dated = [e for e in events if e.date_reference]
        if not dated:
            return None
        return {
            "earliest_reference": dated[0].date_reference,
            "latest_reference": dated[-1].date_reference,
            "dated_events": len(dated),
            "total_events": len(events),
        }

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
# Global instance
# ---------------------------------------------------------------------------

_analyzer: Optional[CaseAnalyzer] = None


def get_case_analyzer(
    canonical_base: Optional[str] = None,
    llm_provider=None,
) -> CaseAnalyzer:
    """Get or create the global case analyzer."""
    global _analyzer
    if _analyzer is None:
        import os
        vault = get_evidence_vault()
        base = canonical_base or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "legal", "canonical"
        )
        matcher = COAMatcher(canonical_base_path=base, llm_provider=llm_provider)
        tracker = BurdenTracker()
        qgen = QuestionGenerator(llm_provider=llm_provider)
        _analyzer = CaseAnalyzer(
            vault=vault,
            coa_matcher=matcher,
            burden_tracker=tracker,
            question_generator=qgen,
            llm_provider=llm_provider,
        )
    return _analyzer

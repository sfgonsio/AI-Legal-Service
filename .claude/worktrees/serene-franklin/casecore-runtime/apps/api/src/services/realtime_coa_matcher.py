"""
Real-Time COA Matching Engine

Watches accumulating transcript in real-time and:
  1. Every ~10 seconds (or on sentence boundary), runs narrative against COA patterns
  2. Uses existing CACI jury instruction data from authority store
  3. Identifies preliminary Causes of Action, burden elements, and evidence needs
  4. Emits COA match events to frontend in real-time
  5. Generates suggested follow-up questions based on gaps

Key class: RealtimeCOAMatcher
  Methods:
    - on_transcript_update(text: str) — Called when transcript changes
    - get_current_matches() — Returns current COA assessments
    - get_suggested_questions() — Returns follow-up questions based on gaps

Uses Anthropic Claude for AI reasoning layer (already configured in project).
Does NOT give legal advice — prepares material for attorney review.

Requires: pip install anthropic
"""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional, Callable
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from src.utils.ids import new_id


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class COAMatch(BaseModel):
    """A single COA candidate identified in the transcript."""
    coa_id: str
    name: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: str = "candidate"  # "candidate", "viable", "strong", "weak"
    evidence_gaps: list[str] = Field(default_factory=list)
    identified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    supporting_text_snippets: list[str] = Field(default_factory=list)


class SuggestedQuestion(BaseModel):
    """A follow-up question generated based on current gaps."""
    question_id: str
    question: str
    target_coa_id: Optional[str] = None
    target_burden_element: Optional[str] = None
    question_type: str = "evidence"  # "evidence", "timeline", "parties", "damages", "causation"
    priority: str = "medium"  # "high", "medium", "low"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RealtimeCOAUpdate(BaseModel):
    """Update event emitted when COAs change."""
    update_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    new_matches: list[COAMatch] = Field(default_factory=list)
    updated_matches: list[COAMatch] = Field(default_factory=list)
    removed_matches: list[str] = Field(default_factory=list)
    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# COA Pattern Definitions
# ---------------------------------------------------------------------------

COA_PATTERNS = {
    "negligence": {
        "caci_instruction": "400-402",
        "keywords": [
            "negligent", "breach of duty", "failure to",
            "failed to warn", "inadequate", "unsafe",
            "dangerous condition", "foreseeable"
        ],
        "required_elements": [
            "duty of care",
            "breach of duty",
            "causation",
            "damages"
        ],
        "evidence_needs": [
            "standard of care in industry",
            "defendant's actions/inactions",
            "plaintiff's injuries",
            "causal connection"
        ]
    },
    "premises_liability": {
        "caci_instruction": "1001-1003",
        "keywords": [
            "fell", "slip", "trip", "hazard", "dangerous condition",
            "property owner", "premises", "invitee", "trespasser",
            "open and obvious", "notice"
        ],
        "required_elements": [
            "dangerous condition existed",
            "owner knew or should have known",
            "plaintiff injured by condition",
            "damages"
        ],
        "evidence_needs": [
            "photographs of premises",
            "prior complaints",
            "maintenance records",
            "medical records"
        ]
    },
    "breach_of_contract": {
        "caci_instruction": "303-307",
        "keywords": [
            "agreement", "contract", "promised", "failed to deliver",
            "breach", "terms", "conditions", "obligation"
        ],
        "required_elements": [
            "valid contract existed",
            "plaintiff performed or was excused",
            "defendant breached",
            "plaintiff harmed"
        ],
        "evidence_needs": [
            "copy of contract",
            "evidence of performance",
            "evidence of breach",
            "damages documentation"
        ]
    },
    "wrongful_termination": {
        "caci_instruction": "2400-2414",
        "keywords": [
            "terminated", "fired", "dismissed", "laid off",
            "retaliation", "discrimination", "FEHA", "public policy",
            "whistleblower", "safety complaint"
        ],
        "required_elements": [
            "employment relationship",
            "discharge",
            "adverse action based on protected reason",
            "damages"
        ],
        "evidence_needs": [
            "employment records",
            "complaints filed",
            "emails/communications",
            "witness statements",
            "performance reviews"
        ]
    },
    "discrimination": {
        "caci_instruction": "2500-2507",
        "keywords": [
            "discrimination", "FEHA", "protected class", "race", "gender",
            "religion", "age", "disability", "harassment", "hostile",
            "based on", "bias", "stereotype"
        ],
        "required_elements": [
            "protected characteristic",
            "adverse employment action",
            "discriminatory motivation",
            "damages"
        ],
        "evidence_needs": [
            "comparative treatment evidence",
            "witness statements",
            "communications showing bias",
            "personnel records"
        ]
    },
    "fraud": {
        "caci_instruction": "1900-1916",
        "keywords": [
            "misrepresented", "false statement", "concealed", "fraudulent",
            "intentional", "deceived", "relied upon", "defrauded",
            "knowingly", "omitted", "material fact"
        ],
        "required_elements": [
            "defendant made false representation",
            "defendant knew it was false",
            "plaintiff reasonably relied",
            "plaintiff harmed"
        ],
        "evidence_needs": [
            "false statements",
            "evidence of knowledge",
            "reliance evidence",
            "damages documentation"
        ]
    },
    "medical_malpractice": {
        "caci_instruction": "500-505",
        "keywords": [
            "medical", "doctor", "physician", "nurse", "hospital",
            "negligent", "treatment", "diagnosis", "standard of care",
            "deviation", "healthcare"
        ],
        "required_elements": [
            "professional relationship",
            "breach of standard of care",
            "causation",
            "damages"
        ],
        "evidence_needs": [
            "medical records",
            "expert declaration",
            "standard of care evidence",
            "damages documentation"
        ]
    },
    "product_liability": {
        "caci_instruction": "1200-1204",
        "keywords": [
            "defective", "product", "unreasonably dangerous",
            "design defect", "manufacturing defect", "failure to warn",
            "injured", "product caused"
        ],
        "required_elements": [
            "product defect",
            "defect caused injury",
            "plaintiff harmed",
            "damages"
        ],
        "evidence_needs": [
            "product examination",
            "warnings/instructions",
            "similar incidents",
            "expert analysis"
        ]
    },
}


# ---------------------------------------------------------------------------
# Real-Time COA Matcher Service
# ---------------------------------------------------------------------------

class RealtimeCOAMatcher:
    """
    Real-time COA matching engine that watches transcript accumulation.

    Configuration via environment variables:
      ANTHROPIC_API_KEY — Required for Claude AI reasoning
      CASECORE_LLM_MODEL — Model to use (default: "claude-sonnet-4-20250514")
      COA_UPDATE_INTERVAL_SECONDS — How often to re-evaluate (default: 10)

    Example usage:
      matcher = RealtimeCOAMatcher(case_id="case-123", on_update=my_callback)
      await matcher.on_transcript_update("Client was terminated after filing OSHA complaint")
      matches = matcher.get_current_matches()
      questions = await matcher.get_suggested_questions()
    """

    def __init__(
        self,
        case_id: str,
        on_update: Optional[Callable[[RealtimeCOAUpdate], None]] = None,
    ):
        self.case_id = case_id
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("CASECORE_LLM_MODEL", "claude-sonnet-4-20250514")
        self.update_interval = int(
            os.getenv("COA_UPDATE_INTERVAL_SECONDS", "10")
        )
        self._client = None
        self._on_update = on_update
        self._current_matches: dict[str, COAMatch] = {}
        self._previous_matches: dict[str, COAMatch] = {}
        self._last_update = datetime.now(timezone.utc)
        self._transcript = ""
        self._session_id = new_id()

    @property
    def client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "anthropic package not installed. "
                    "Run: pip install anthropic"
                )
        return self._client

    async def on_transcript_update(self, text: str) -> Optional[RealtimeCOAUpdate]:
        """
        Called when transcript is updated.

        Re-evaluates COAs if enough time has passed or sentence boundary detected.

        Args:
            text: The current accumulated transcript text

        Returns:
            RealtimeCOAUpdate if COAs were re-evaluated, None otherwise.
        """
        self._transcript = text

        # Check if enough time has passed OR if a sentence was completed
        now = datetime.now(timezone.utc)
        time_elapsed = (now - self._last_update).total_seconds()
        sentence_completed = self._sentence_boundary_detected(text)

        if time_elapsed >= self.update_interval or sentence_completed:
            return await self._evaluate_coas()

        return None

    def _sentence_boundary_detected(self, text: str) -> bool:
        """Simple heuristic: check if text ends with sentence punctuation."""
        if not text or not text.strip():
            return False
        return text.rstrip()[-1] in ".!?"

    async def _evaluate_coas(self) -> RealtimeCOAUpdate:
        """
        Re-evaluate COAs against current transcript using Claude.

        Uses a structured prompt to identify matching COA patterns.
        """
        self._previous_matches = self._current_matches.copy()

        # Build prompt for Claude
        coa_descriptions = "\n".join([
            f"- {name}: {info['keywords']}"
            for name, info in COA_PATTERNS.items()
        ])

        prompt = f"""You are a legal intake assistant analyzing a client's narrative for potential Causes of Action (COAs).

TRANSCRIPT:
{self._transcript}

POTENTIAL COAs TO EVALUATE:
{coa_descriptions}

For each COA that appears relevant based on the transcript, assess:
1. Confidence score (0.0-1.0) that this COA applies
2. Status: candidate, viable, strong, or weak
3. Key evidence gaps that would strengthen/weaken this COA
4. Snippets from the transcript that support this COA

Return a JSON array of COAs found, with empty array if none are apparent:
[
  {{
    "name": "COA name",
    "confidence_score": 0.85,
    "status": "viable",
    "evidence_gaps": ["list of missing evidence"],
    "supporting_text_snippets": ["relevant quotes from transcript"]
  }}
]

Only include JSON in your response, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = response.content[0].text.strip()

            # Extract JSON from response (may have markdown wrapping)
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                coas_data = json.loads(json_match.group())
            else:
                coas_data = json.loads(response_text)

            # Update matches
            self._current_matches.clear()
            for coa_data in coas_data:
                coa_name = coa_data.get("name", "").lower().replace(" ", "_")
                coa_id = new_id()
                match = COAMatch(
                    coa_id=coa_id,
                    name=coa_data.get("name", coa_name),
                    confidence_score=float(coa_data.get("confidence_score", 0.5)),
                    status=coa_data.get("status", "candidate"),
                    evidence_gaps=coa_data.get("evidence_gaps", []),
                    supporting_text_snippets=coa_data.get("supporting_text_snippets", []),
                )
                self._current_matches[coa_id] = match

            # Build update event
            new_ids = set(self._current_matches.keys()) - set(self._previous_matches.keys())
            updated_ids = set(self._current_matches.keys()) & set(self._previous_matches.keys())
            removed_ids = set(self._previous_matches.keys()) - set(self._current_matches.keys())

            update = RealtimeCOAUpdate(
                update_id=new_id(),
                new_matches=[self._current_matches[cid] for cid in new_ids],
                updated_matches=[self._current_matches[cid] for cid in updated_ids],
                removed_matches=list(removed_ids),
            )

            self._last_update = datetime.now(timezone.utc)

            # Invoke callback if provided
            if self._on_update:
                try:
                    result = self._on_update(update)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"[WARNING] on_update callback failed: {e}")

            return update

        except Exception as e:
            print(f"[ERROR] COA evaluation failed: {e}")
            return RealtimeCOAUpdate(update_id=new_id())

    def get_current_matches(self) -> list[COAMatch]:
        """Return current COA matches sorted by confidence."""
        return sorted(
            self._current_matches.values(),
            key=lambda m: m.confidence_score,
            reverse=True,
        )

    async def get_suggested_questions(self) -> list[SuggestedQuestion]:
        """
        Generate follow-up questions based on current COA gaps using Claude.

        Returns top 3-5 questions ranked by priority.
        """
        if not self._current_matches:
            return []

        # Build evidence gaps summary
        all_gaps = []
        for match in self._current_matches.values():
            all_gaps.extend(match.evidence_gaps)

        if not all_gaps:
            return []

        gaps_text = "\n".join([f"- {gap}" for gap in all_gaps[:10]])

        prompt = f"""You are a legal intake interviewer. Based on these identified evidence gaps,
generate 3-5 targeted follow-up questions to ask the client.

IDENTIFIED GAPS:
{gaps_text}

For each question, provide:
1. The question itself (client-friendly, not legal jargon)
2. Type: evidence, timeline, parties, damages, or causation
3. Priority: high, medium, or low

Return JSON array:
[
  {{
    "question": "When did you first notice...?",
    "question_type": "evidence",
    "priority": "high"
  }}
]

Only include JSON in your response, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Extract JSON from response
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                questions_data = json.loads(json_match.group())
            else:
                questions_data = json.loads(response_text)

            questions = [
                SuggestedQuestion(
                    question_id=new_id(),
                    question=q.get("question", ""),
                    question_type=q.get("question_type", "evidence"),
                    priority=q.get("priority", "medium"),
                )
                for q in questions_data
                if q.get("question")
            ]

            return questions

        except Exception as e:
            print(f"[ERROR] Question generation failed: {e}")
            return []

    def get_transcript(self) -> str:
        """Get current accumulated transcript."""
        return self._transcript

    def get_session_id(self) -> str:
        """Get the session ID for this matcher."""
        return self._session_id

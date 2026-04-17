"""
INTERVIEW_AGENT — AI-Powered Intake Interview Service

Uses LLM to:
  1. Parse raw narratives into structured parties, events, relationships
  2. Classify case type, jurisdiction, applicable codes
  3. Detect gaps, ambiguities, contradictions
  4. Generate targeted follow-up questions
  5. Refine structured model as new information arrives

Governance controls:
  - Original narrative is NEVER modified
  - No facts are asserted as true (all are "reported" or "alleged")
  - No legal conclusions are made
  - All transformations are auditable
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from src.utils.ids import new_id

# ---------------------------------------------------------------------------
# LLM Provider abstraction
# ---------------------------------------------------------------------------

class LLMProvider:
    """Abstract LLM interface. Swap implementation for different providers."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("CASECORE_LLM_MODEL", "claude-sonnet-4-20250514")
        self._client = None

    @property
    def client(self):
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

    def complete(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        """Send a message to the LLM and return the text response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

NARRATIVE_PARSER_SYSTEM = """You are the INTERVIEW_AGENT for CaseCore, a legal case management platform.

Your task is to analyze a client's intake narrative and extract structured information.

RULES:
- All extracted information must be characterized as "reported" or "alleged" — never assert facts as true
- Do not make legal conclusions
- Preserve the original narrative exactly — your output is a STRUCTURED OVERLAY, not a replacement
- Flag anything ambiguous, contradictory, or missing
- Be thorough but conservative: only extract what is clearly present in the narrative

OUTPUT FORMAT: Return valid JSON with this structure:
{
  "parties": [
    {"name": "...", "role": "plaintiff|defendant|witness|expert|third_party|unknown", "description": "..."}
  ],
  "events": [
    {"event_type": "incident|communication|agreement|breach|discovery|legal_action|other", "description": "...", "date_approximate": "...", "date_precision": "exact|month|quarter|year|unknown", "location": "...", "parties_involved": ["name1", "name2"]}
  ],
  "relationships": [
    {"party_a": "...", "party_b": "...", "relationship_type": "...", "description": "..."}
  ],
  "timeline_sequence": ["event descriptions in chronological order"],
  "case_context": {
    "case_type": "...",
    "case_subtype": "...",
    "jurisdiction": "...",
    "claim_categories": ["..."],
    "applicable_codes": ["EVID", "CIV", "CCP", etc.],
    "statute_of_limitations_notes": "..."
  },
  "gaps": [
    {"gap_type": "missing_info|ambiguity|contradiction|timeline_gap|unidentified_party", "severity": "critical|high|medium|low", "description": "...", "suggested_question": "..."}
  ]
}"""

FOLLOW_UP_SYSTEM = """You are the INTERVIEW_AGENT for CaseCore. You are conducting a structured legal intake interview.

Given the current state of the intake (narrative, structured model, identified gaps), generate targeted follow-up questions.

RULES:
- Ask questions that resolve identified gaps, starting with the most critical
- Be empathetic but precise — this is a legal intake, not therapy
- Ask one question at a time when possible, or group closely related questions
- Frame questions to elicit specific, useful information (dates, names, sequences)
- Never suggest legal strategy or make promises about case outcomes
- If the client's response introduces new information, note what gaps it resolves and any new gaps it creates

OUTPUT FORMAT: Return valid JSON:
{
  "questions": ["question 1", "question 2", ...],
  "reasoning": "brief explanation of why these questions matter",
  "gaps_targeted": ["gap descriptions being addressed"],
  "priority": "critical|high|medium|low"
}"""

REFINEMENT_SYSTEM = """You are the INTERVIEW_AGENT for CaseCore. You are refining a structured intake model based on new information from the client or attorney.

Given:
1. The current structured model (parties, events, timeline, gaps)
2. New information from the latest response

Update the structured model. Return the FULL updated model (not just deltas).

RULES:
- Merge new information into existing structure
- Mark resolved gaps as resolved
- Identify any NEW gaps introduced by the new information
- Update timeline if new dates or sequences are mentioned
- Update party information if new details emerge
- Never modify the original narrative
- All assertions remain "reported" / "alleged"

OUTPUT FORMAT: Same JSON structure as the initial parse, but updated."""


# ---------------------------------------------------------------------------
# InterviewAgent class
# ---------------------------------------------------------------------------

class InterviewAgent:
    """
    AI-powered intake interview agent.

    Lifecycle:
      1. parse_narrative()     — initial extraction from raw narrative
      2. generate_questions()  — follow-up questions based on gaps
      3. refine_model()        — update model with new client responses
      4. assess_completeness() — determine if intake is sufficient
    """

    def __init__(self, llm: Optional[LLMProvider] = None):
        self.llm = llm or LLMProvider()

    def parse_narrative(self, narrative: str, hints: Optional[dict] = None) -> dict:
        """
        Parse a raw client narrative into structured intake components.

        Returns dict with: parties, events, relationships, timeline_sequence,
                          case_context, gaps
        """
        user_msg = f"CLIENT NARRATIVE:\n\n{narrative}"
        if hints:
            user_msg += f"\n\nADDITIONAL HINTS:\n{json.dumps(hints)}"

        raw_response = self.llm.complete(
            system_prompt=NARRATIVE_PARSER_SYSTEM,
            user_message=user_msg,
        )
        return self._parse_json_response(raw_response)

    def generate_questions(
        self,
        narrative: str,
        structured_model: dict,
        gaps: list[dict],
        conversation_history: list[dict],
    ) -> dict:
        """
        Generate targeted follow-up questions based on current gaps.

        Returns dict with: questions, reasoning, gaps_targeted, priority
        """
        user_msg = (
            f"ORIGINAL NARRATIVE:\n{narrative}\n\n"
            f"CURRENT STRUCTURED MODEL:\n{json.dumps(structured_model, indent=2, default=str)}\n\n"
            f"IDENTIFIED GAPS:\n{json.dumps(gaps, indent=2, default=str)}\n\n"
            f"CONVERSATION SO FAR:\n{json.dumps(conversation_history[-10:], indent=2, default=str)}"
        )

        raw_response = self.llm.complete(
            system_prompt=FOLLOW_UP_SYSTEM,
            user_message=user_msg,
        )
        return self._parse_json_response(raw_response)

    def refine_model(
        self,
        narrative: str,
        current_model: dict,
        new_response: str,
        responder_role: str = "client",
    ) -> dict:
        """
        Refine the structured model based on a new client/attorney response.

        Returns updated model dict.
        """
        user_msg = (
            f"ORIGINAL NARRATIVE:\n{narrative}\n\n"
            f"CURRENT STRUCTURED MODEL:\n{json.dumps(current_model, indent=2, default=str)}\n\n"
            f"NEW RESPONSE FROM {responder_role.upper()}:\n{new_response}"
        )

        raw_response = self.llm.complete(
            system_prompt=REFINEMENT_SYSTEM,
            user_message=user_msg,
        )
        return self._parse_json_response(raw_response)

    def assess_completeness(self, gaps: list[dict]) -> dict:
        """
        Assess whether the intake is sufficiently complete.

        Returns: {"complete": bool, "reason": str, "blocking_gaps": [...]}
        """
        critical = [g for g in gaps if g.get("severity") == "critical" and not g.get("resolved")]
        high = [g for g in gaps if g.get("severity") == "high" and not g.get("resolved")]
        unresolved = [g for g in gaps if not g.get("resolved")]

        if critical:
            return {
                "complete": False,
                "reason": f"{len(critical)} critical gaps remain unresolved",
                "blocking_gaps": critical,
            }
        if len(high) > 2:
            return {
                "complete": False,
                "reason": f"{len(high)} high-severity gaps remain — recommend further intake",
                "blocking_gaps": high,
            }
        return {
            "complete": True,
            "reason": f"Intake sufficient. {len(unresolved)} non-critical gaps remain for future follow-up.",
            "blocking_gaps": [],
        }

    def _parse_json_response(self, raw: str) -> dict:
        """Extract JSON from LLM response, handling markdown code fences."""
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (code fences)
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
            # Try to find JSON object in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse LLM response", "raw": raw[:500]}

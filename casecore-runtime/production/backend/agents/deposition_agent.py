"""
Deposition Agent for CaseCore
==============================

Real-time deposition assistant with contradiction detection.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, case_id: str, config: dict = None):
        self.case_id = case_id
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()

    @abstractmethod
    async def analyze(self, context: dict) -> dict:
        pass

    def _validate_context(self, context: dict, required_keys: List[str]) -> bool:
        missing = [k for k in required_keys if k not in context]
        if missing:
            raise ValueError(f"Context missing required keys: {missing}")
        return True

    def _format_response(self, data: dict, confidence: float = 1.0) -> dict:
        return {
            "case_id": self.case_id,
            "agent_type": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": confidence,
            "data": data
        }


# Evidence index with 7 key documents
EVIDENCE_INDEX = {
    "Michigan.pdf": {
        "id": "370",
        "keywords": ["michigan", "cultivation", "agreement", "terminate"],
        "key_facts": ["DocuSigned contract", "Requires written termination notice", "15 day cure period"],
    },
    "Oklahoma.pdf": {
        "id": "371",
        "keywords": ["oklahoma", "cultivator", "profit sharing"],
        "key_facts": ["David as designated cultivator", "Jeremy's capital contribution"],
    },
    "PSH_Operating_Agreement.pdf": {
        "id": "372",
        "keywords": ["operating agreement", "termination", "member"],
        "key_facts": ["Section 8: Termination requires written notice", "Two-member LLC"],
    },
    "Termination_Notice_June_2022.pdf": {
        "id": "373",
        "keywords": ["termination", "notice", "effective"],
        "key_facts": ["Dated June 15, 2022", "Effective immediately", "Dissolution demand"],
    },
    "Bank_Statements_2022.pdf": {
        "id": "374",
        "keywords": ["withdraw", "transfer", "deposit"],
        "key_facts": ["Large July 2022 withdrawals", "$120k unexplained", "Personal account transfers"],
    },
    "Email_April_2022.pdf": {
        "id": "375",
        "keywords": ["email", "concerns", "operational"],
        "key_facts": ["Jeremy raises concerns", "David responds defensively"],
    },
    "Cultivation_Records_2022.pdf": {
        "id": "376",
        "keywords": ["plants", "harvest", "capacity"],
        "key_facts": ["50k to 120k plant expansion", "Post-notice growth"],
    },
}


class DepositionAgent(BaseAgent):
    """Real-time deposition analysis with contradiction detection."""

    def __init__(self, case_id: str, config: dict = None):
        super().__init__(case_id, config)
        self.evidence_index = EVIDENCE_INDEX

    async def analyze(self, context: dict) -> dict:
        """Analyze deposition transcript segment."""
        self._validate_context(context, ["transcript_segment"])

        segment = context.get("transcript_segment", "").strip()
        weapon_id = context.get("weapon_id")

        contradictions = await self._find_contradictions(segment)
        follow_ups = self._generate_follow_ups(segment, contradictions)
        perjury_risk, confidence = self._assess_perjury_risk(segment, contradictions)

        result = {
            "transcript_segment": segment[:200],
            "contradictions": contradictions[:3],
            "suggested_questions": follow_ups,
            "perjury_risk": perjury_risk,
            "confidence": confidence,
        }

        return self._format_response(result, confidence)

    async def _find_contradictions(self, segment: str) -> List[Dict[str, Any]]:
        """Find contradictions between testimony and evidence."""
        contradictions = []
        segment_lower = segment.lower()

        for doc_name, doc_data in self.evidence_index.items():
            matching_keywords = [
                kw for kw in doc_data.get("keywords", [])
                if kw in segment_lower
            ]

            if not matching_keywords:
                continue

            # Check for negations contradicting facts
            if "don't recall" in segment_lower or "didn't" in segment_lower:
                for fact in doc_data.get("key_facts", []):
                    if any(word in segment_lower for word in fact.lower().split()):
                        contradictions.append({
                            "document": doc_name,
                            "doc_id": doc_data.get("id"),
                            "excerpt": fact,
                            "contradiction": "Witness denies or can't recall documented fact",
                            "follow_up_question": f"Doesn't {doc_name} show: {fact}?",
                            "severity": "high",
                        })

        return contradictions

    def _generate_follow_ups(self, segment: str, contradictions: List[Dict]) -> List[str]:
        """Generate follow-up questions."""
        follow_ups = []

        if contradictions:
            for c in contradictions[:2]:
                follow_ups.append(c.get("follow_up_question", ""))

        if "don't recall" in segment.lower():
            follow_ups.append("Would reviewing these documents refresh your recollection?")

        return [q for q in follow_ups if q][:3]

    def _assess_perjury_risk(
        self, segment: str, contradictions: List[Dict]
    ) -> Tuple[float, float]:
        """Assess perjury risk."""
        risk = 0.0
        confidence = 0.7

        if contradictions:
            risk += min(0.3, len(contradictions) * 0.1)
            confidence += 0.1

        if "didn't" in segment.lower() or "never" in segment.lower():
            risk += 0.2

        if "don't recall" in segment.lower():
            risk += 0.2

        return min(1.0, risk), min(0.95, confidence)


async def suggest_follow_up_questions(
    transcript_segment: str, case_id: str = "unknown"
) -> List[str]:
    """Module-level shim for deposition routes."""
    agent = DepositionAgent(case_id=case_id)
    result = await agent.analyze({"transcript": transcript_segment})
    data = result.get("data") or {}
    return data.get("follow_ups", []) or []


async def analyze_testimony(
    transcript_segment: str, case_id: str = "unknown"
) -> Dict[str, Any]:
    """Module-level shim for deposition routes."""
    agent = DepositionAgent(case_id=case_id)
    return await agent.analyze({"transcript": transcript_segment})


async def flag_perjury_opportunity(
    transcript_segment: str, case_id: str = "unknown"
) -> Dict[str, Any]:
    """Module-level shim for deposition routes."""
    agent = DepositionAgent(case_id=case_id)
    result = await agent.analyze({"transcript": transcript_segment})
    data = result.get("data") or {}
    return {
        "perjury_risk": data.get("perjury_risk", 0.0),
        "confidence": data.get("confidence", 0.0),
        "contradictions": data.get("contradictions", []),
    }


__all__ = [
    "DepositionAgent",
    "EVIDENCE_INDEX",
    "suggest_follow_up_questions",
    "analyze_testimony",
    "flag_perjury_opportunity",
]

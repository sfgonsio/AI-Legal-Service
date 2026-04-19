"""
Document Agent for CaseCore
===========================

Analyzes new evidence and maps to COAs/burden elements.
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


# COAs and their keywords
COAS = {
    "BC-1": {"name": "Breach - Performance", "keywords": ["contract", "agreement", "breach", "perform"]},
    "BC-2": {"name": "Breach - Repudiation", "keywords": ["repudiation", "material breach", "refuse"]},
    "Fraud-1": {"name": "Fraud - Inducement", "keywords": ["misrepresent", "false", "deceive", "fraud"]},
    "Fraud-2": {"name": "Fraud - Damages", "keywords": ["damages", "loss", "injury", "relied"]},
    "Fiduciary-1": {"name": "Fiduciary - Loyalty", "keywords": ["fiduciary", "self-dealing", "conflict"]},
    "Fiduciary-2": {"name": "Fiduciary - Care", "keywords": ["negligence", "failure", "care", "reckless"]},
}

# Weapons and what they establish
WEAPONS = {
    1: {"title": "Contracts", "establishes": ["BC-1", "BC-2"]},
    4: {"title": "Termination comms", "establishes": ["BC-2"]},
    9: {"title": "Financial transactions", "establishes": ["Fiduciary-1"]},
    12: {"title": "Post-notice actions", "establishes": ["BC-2"]},
    14: {"title": "Knowledge docs", "establishes": ["Fraud-1"]},
    16: {"title": "Operational docs", "establishes": ["BC-1"]},
    23: {"title": "Damages knowledge", "establishes": ["Fraud-2"]},
}


class DocumentAgent(BaseAgent):
    """Analyzes new evidence documents."""

    def __init__(self, case_id: str, config: dict = None):
        super().__init__(case_id, config)
        self.coas = COAS
        self.weapons = WEAPONS

    async def analyze(self, context: dict) -> dict:
        """Analyze newly uploaded document."""
        self._validate_context(context, ["document_text"])

        doc_text = context.get("document_text", "").strip()
        doc_name = context.get("document_name", "Unknown")

        entities = self._extract_entities(doc_text)
        dates = self._extract_dates(doc_text)
        amounts = self._extract_amounts(doc_text)
        coa_scores = self._score_coas(doc_text)
        relevant_weapons = self._identify_weapons(coa_scores)
        significance, confidence = self._assess_significance(coa_scores)

        result = {
            "document_name": doc_name,
            "significance": significance,
            "extracted_entities": entities,
            "dates": dates,
            "amounts": amounts,
            "coa_relevance": coa_scores,
            "relevant_weapons": relevant_weapons,
        }

        return self._format_response(result, confidence)

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities."""
        entities = {"people": [], "businesses": [], "locations": []}
        text_lower = text.lower()

        people = {"jeremy mills": "Jeremy Mills", "david polley": "David Polley"}
        businesses = {"packwood": "Packwood LLC", "psh": "PSH"}
        locations = {"sacramento": "Sacramento", "michigan": "Michigan", "oklahoma": "Oklahoma"}

        for key, display in people.items():
            if key in text_lower and display not in entities["people"]:
                entities["people"].append(display)

        for key, display in businesses.items():
            if key in text_lower and display not in entities["businesses"]:
                entities["businesses"].append(display)

        for key, display in locations.items():
            if key in text_lower and display not in entities["locations"]:
                entities["locations"].append(display)

        return entities

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from document."""
        pattern = r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+20\d{2}"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))[:5]

    def _extract_amounts(self, text: str) -> List[str]:
        """Extract financial amounts."""
        pattern = r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?"
        matches = re.findall(pattern, text)
        return list(set(matches))[:5]

    def _score_coas(self, text: str) -> Dict[str, float]:
        """Score relevance to each COA."""
        scores = {}
        text_lower = text.lower()

        for coa_id, coa_data in self.coas.items():
            matches = sum(
                1 for keyword in coa_data.get("keywords", [])
                if keyword in text_lower
            )
            score = min(100, matches * 20)
            scores[coa_id] = score

        return {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}

    def _identify_weapons(self, coa_scores: Dict[str, float]) -> List[int]:
        """Identify relevant weapons."""
        recommended = []
        top_coas = [coa for coa, score in list(coa_scores.items())[:2] if score > 20]

        for weapon_id, weapon_data in self.weapons.items():
            establishes = weapon_data.get("establishes", [])
            if any(coa in top_coas for coa in establishes):
                recommended.append(weapon_id)

        return recommended

    def _assess_significance(self, coa_scores: Dict[str, float]) -> Tuple[str, float]:
        """Assess document significance."""
        max_score = max(coa_scores.values()) if coa_scores else 0

        if max_score > 70:
            return "critical", 0.90
        elif max_score > 50:
            return "high", 0.85
        elif max_score > 30:
            return "medium", 0.80
        else:
            return "low", 0.70


__all__ = ["DocumentAgent", "COAS", "WEAPONS"]

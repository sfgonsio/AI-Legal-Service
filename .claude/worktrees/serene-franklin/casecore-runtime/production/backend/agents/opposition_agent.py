"""
Opposition Agent for CaseCore
==============================

Predicts how David Polley's defense attorney will respond to interrogatory weapons.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


class DefenseTactic(str, Enum):
    """Common defense attorney tactics David's counsel may employ."""
    SELECTIVE_MEMORY = "selective_memory"
    ENTITY_SHIELD = "entity_shield"
    TIMELINE_BLUR = "timeline_blur"
    MINIMIZATION = "minimization"
    FIFTH_AMENDMENT = "fifth_amendment"
    OVERBREADTH_OBJECTION = "overbreadth_objection"
    PRIVILEGE_CLAIM = "privilege_claim"
    LACK_OF_KNOWLEDGE = "lack_of_knowledge"
    TECHNICAL_OBJECTION = "technical_objection"


class WeaponCategory(str, Enum):
    """Categories that determine likely defense strategy."""
    WEAPONIZE = "weaponize"
    DISCOVER = "discover"
    UNCOVER = "uncover"
    ESTABLISH = "establish"


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, case_id: str, config: dict = None):
        self.case_id = case_id
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()

    @abstractmethod
    async def analyze(self, context: dict) -> dict:
        """Run agent analysis."""
        pass

    def _validate_context(self, context: dict, required_keys: List[str]) -> bool:
        """Validate context contains required keys."""
        missing = [k for k in required_keys if k not in context]
        if missing:
            raise ValueError(f"Context missing required keys: {missing}")
        return True

    def _format_response(self, data: dict, confidence: float = 1.0) -> dict:
        """Format standard response envelope."""
        return {
            "case_id": self.case_id,
            "agent_type": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": confidence,
            "data": data
        }


class OppositionAgent(BaseAgent):
    """
    Predicts defense responses to interrogatory weapons in Mills v. Polley.

    Generates 2-4 probable responses ranked by likelihood, with detailed
    counter-strategy analysis and case impact assessment.
    """

    def __init__(self, case_id: str, config: dict = None):
        super().__init__(case_id, config)

        self.david_patterns = {
            "entity_preference": True,
            "document_evasion": True,
            "timeline_gaps": True,
            "financial_opacity": True,
            "memory_lapses": True,
            "attorney_reliance": True,
        }

        self.weapon_response_map = self._build_weapon_response_map()

    def _build_weapon_response_map(self) -> Dict[int, List[Dict[str, Any]]]:
        """Build map of weapons to likely defense responses."""
        return {
            1: [
                {
                    "response": "David lists contracts but claims PSH/PSV entity business, not personal",
                    "probability": 0.75,
                    "defense_tactic": "entity_shield",
                    "our_counter": "Pierce entity veil - show David's personal control",
                    "case_strength_delta": 12,
                    "depo_follow_up": "Who authorized your signature? Who made the business decision?",
                    "risk_level": "low"
                },
                {
                    "response": "Counsel objects as overbroad, seeks business records spanning 5+ years",
                    "probability": 0.65,
                    "defense_tactic": "overbreadth_objection",
                    "our_counter": "Narrow to contracts involving Jeremy Mills specifically, 2018-2023",
                    "case_strength_delta": 0,
                    "depo_follow_up": "How many contracts total? Which ones involved Jeremy?",
                    "risk_level": "medium"
                },
            ],

            4: [
                {
                    "response": "David claims never received termination notice, only informal conversations",
                    "probability": 0.70,
                    "defense_tactic": "selective_memory",
                    "our_counter": "Produce email with termination language, show intentional evasion",
                    "case_strength_delta": 15,
                    "depo_follow_up": "Didn't you receive Jeremy's June 2022 email about partnership termination?",
                    "risk_level": "low"
                },
                {
                    "response": "Counsel invokes privilege over legal advice re: termination response",
                    "probability": 0.80,
                    "defense_tactic": "privilege_claim",
                    "our_counter": "If David took action based on advice, waived privilege",
                    "case_strength_delta": 8,
                    "depo_follow_up": "Did your attorney advise you to ignore the termination notice?",
                    "risk_level": "medium"
                },
            ],

            9: [
                {
                    "response": "All transactions were legitimate entity distributions, not personal benefit",
                    "probability": 0.80,
                    "defense_tactic": "entity_shield",
                    "our_counter": "Show excessive unauthorized distributions, self-dealing",
                    "case_strength_delta": 18,
                    "depo_follow_up": "Were these approved by Jeremy? Did he vote on them?",
                    "risk_level": "low"
                },
                {
                    "response": "Invokes Fifth Amendment on hidden accounts/off-books payments",
                    "probability": 0.60,
                    "defense_tactic": "fifth_amendment",
                    "our_counter": "Negative inference - consciousness of guilt",
                    "case_strength_delta": 22,
                    "depo_follow_up": "Are you invoking Fifth because fraud or criminal conduct?",
                    "risk_level": "low"
                },
            ],

            12: [
                {
                    "response": "Continued operations were routine, no change in behavior",
                    "probability": 0.65,
                    "defense_tactic": "minimization",
                    "our_counter": "Show expansion - increased harvests, new contracts",
                    "case_strength_delta": 14,
                    "depo_follow_up": "Plant volume went from 50k to 120k in 3 months. How do you explain that?",
                    "risk_level": "low"
                },
            ],

            14: [
                {
                    "response": "Admits knowledge but claims Jeremy voluntarily relinquished rights",
                    "probability": 0.60,
                    "defense_tactic": "minimization",
                    "our_counter": "No voluntary relinquishment - forced out by bad faith",
                    "case_strength_delta": 12,
                    "depo_follow_up": "What actions did you take to force Jeremy out?",
                    "risk_level": "low"
                },
            ],

            16: [
                {
                    "response": "Overbreadth objection - seeks entire business files",
                    "probability": 0.85,
                    "defense_tactic": "overbreadth_objection",
                    "our_counter": "Narrow to David's communications and decisions",
                    "case_strength_delta": 0,
                    "depo_follow_up": "We'll limit to David's decisions only",
                    "risk_level": "high"
                },
            ],

            23: [
                {
                    "response": "Admits knowledge but denies responsibility for damages",
                    "probability": 0.65,
                    "defense_tactic": "minimization",
                    "our_counter": "Knowledge of breach and harm establishes damages liability",
                    "case_strength_delta": 10,
                    "depo_follow_up": "You knew Jeremy invested 250k. You knew excluding him would cost him that?",
                    "risk_level": "low"
                },
            ],
        }

    async def analyze(self, context: dict) -> dict:
        """
        Predict likely defense responses to a specific weapon.

        Args:
            context: Dictionary containing weapon_id and weapon_category

        Returns:
            Dictionary with predicted responses and analysis
        """
        self._validate_context(context, ["weapon_id"])

        weapon_id = context.get("weapon_id")
        weapon_category = context.get("weapon_category", "establish")

        predicted_responses = []
        if weapon_id in self.weapon_response_map:
            predicted_responses = self.weapon_response_map[weapon_id]
        else:
            predicted_responses = await self._generate_generic_responses(
                weapon_id, weapon_category
            )

        confidence = self._calculate_confidence(weapon_id, len(predicted_responses))
        recommended_strategy = self._get_strategy_recommendation(weapon_id)
        warnings = self._generate_warnings(weapon_id, weapon_category)

        result = {
            "weapon_id": weapon_id,
            "weapon_category": str(weapon_category),
            "predicted_responses": predicted_responses,
            "recommended_strategy": recommended_strategy,
            "warnings": warnings,
            "confidence": confidence,
        }

        return self._format_response(result, confidence)

    async def _generate_generic_responses(
        self, weapon_id: int, category: str
    ) -> List[Dict[str, Any]]:
        """Generate generic responses for unmapped weapons."""
        responses = []

        if category == "discover":
            responses.append({
                "response": "Counsel objects as overly broad and burdensome",
                "probability": 0.85,
                "defense_tactic": "overbreadth_objection",
                "our_counter": "Negotiate scope, offer phased production",
                "case_strength_delta": 0,
                "depo_follow_up": "Let's narrow the scope",
                "risk_level": "high"
            })

        elif category == "uncover":
            responses.append({
                "response": "Counsel asserts privilege on legal advice",
                "probability": 0.80,
                "defense_tactic": "privilege_claim",
                "our_counter": "Challenge privilege scope",
                "case_strength_delta": 5,
                "depo_follow_up": "Privilege log shows what?",
                "risk_level": "medium"
            })

        else:
            responses.append({
                "response": "Provides straightforward answer",
                "probability": 0.70,
                "defense_tactic": "minimization",
                "our_counter": "Use as foundation for harder questions",
                "case_strength_delta": 3,
                "depo_follow_up": "Thanks. Now let me build on that",
                "risk_level": "low"
            })

        return responses

    def _calculate_confidence(self, weapon_id: int, response_count: int) -> float:
        """Calculate confidence score."""
        base = 0.75
        if weapon_id in self.weapon_response_map:
            base = 0.85
        if response_count >= 3:
            base += 0.05
        return min(0.95, max(0.6, base))

    def _get_strategy_recommendation(self, weapon_id: int) -> str:
        """Get deployment strategy recommendation."""
        strategies = {
            1: "Deploy early to lock in entity shield claim",
            4: "Critical for establishing breach awareness",
            9: "High impact for fiduciary breach",
            12: "Shows consciousness of guilt post-notice",
            14: "Establishes knowledge of value",
            16: "Broad discovery, expect objections",
            23: "Capstone weapon for damages",
        }
        return strategies.get(weapon_id, "Deploy in sequence with related weapons")

    def _generate_warnings(self, weapon_id: int, category: str) -> List[str]:
        """Generate attorney warnings for this weapon."""
        warnings = []

        if category == "discover":
            warnings.append("Expect overbreadth objection")

        if category == "uncover":
            warnings.append("High probability of privilege claim")

        if weapon_id in [9, 14, 23]:
            warnings.append("David may invoke Fifth Amendment")

        return warnings


__all__ = ["OppositionAgent", "DefenseTactic", "WeaponCategory"]

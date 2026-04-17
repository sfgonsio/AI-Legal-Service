"""
Strategy Agent for CaseCore
============================

Recommends the next best weapon to deploy based on current case state.
"""

import asyncio
from typing import Dict, List, Any, Optional
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


class StrategyAgent(BaseAgent):
    """
    Recommends optimal weapon deployment sequence in Mills v. Polley.
    """

    def __init__(self, case_id: str, config: dict = None):
        super().__init__(case_id, config)

        # 5 named strategies
        self.strategies = {
            "entity_shell_game": {
                "description": "Expose David's use of entities as alter ego shells",
                "weapons": [1, 6, 8, 9, 14],
                "priority": "high",
            },
            "timeline_trap": {
                "description": "Lock David into false timeline",
                "weapons": [4, 12, 13, 15, 21],
                "priority": "high",
            },
            "financial_forensics": {
                "description": "Follow money trails showing personal benefit",
                "weapons": [9, 19, 24, 25],
                "priority": "high",
            },
            "document_pincer": {
                "description": "Use documents to eliminate David's objections",
                "weapons": [2, 3, 5, 7, 16, 20],
                "priority": "medium",
            },
            "knowledge_closure": {
                "description": "Establish David's knowledge of partnership terms",
                "weapons": [10, 11, 17, 18, 23],
                "priority": "high",
            },
        }

        # Perjury paths
        self.perjury_paths = {
            "PATH_A": {
                "description": "Entity shield collapse sequence",
                "weapons": [1, 6, 9, 14],
                "completion_bonus": 25,
            },
            "PATH_B": {
                "description": "Timeline/sequence trap",
                "weapons": [4, 12, 13, 15],
                "completion_bonus": 20,
            },
            "PATH_C": {
                "description": "Knowledge/intent sequence",
                "weapons": [10, 11, 17, 23],
                "completion_bonus": 18,
            },
        }

        # Weapon impact scores
        self.weapon_data = {
            1: {"impact": 15, "dependencies": [], "strategy": "entity_shell_game"},
            4: {"impact": 14, "dependencies": [1], "strategy": "timeline_trap"},
            6: {"impact": 12, "dependencies": [1], "strategy": "entity_shell_game"},
            9: {"impact": 18, "dependencies": [1, 6], "strategy": "financial_forensics"},
            10: {"impact": 13, "dependencies": [4, 12], "strategy": "knowledge_closure"},
            12: {"impact": 14, "dependencies": [4], "strategy": "timeline_trap"},
            14: {"impact": 16, "dependencies": [9], "strategy": "entity_shell_game"},
            16: {"impact": 13, "dependencies": [1, 9], "strategy": "document_pincer"},
            23: {"impact": 17, "dependencies": [10, 11], "strategy": "knowledge_closure"},
        }

    async def analyze(self, context: dict) -> dict:
        """
        Recommend the next weapon to deploy.

        Args:
            context: Dictionary with deployed_weapons, case_strength, etc.

        Returns:
            Dictionary with recommended weapon and analysis
        """
        self._validate_context(context, ["deployed_weapons"])

        deployed = set(context.get("deployed_weapons", []))
        case_strength = context.get("case_strength", 50)
        current_strategy = context.get("current_strategy")

        # Get undeployed weapons
        undeployed = [w for w in range(1, 27) if w not in deployed]

        # Filter to deployable weapons (dependencies met)
        deployable = [
            w for w in undeployed
            if self._check_dependencies(w, deployed)
        ]

        # Score each deployable
        scores = {}
        for weapon in deployable:
            scores[weapon] = self._score_weapon(
                weapon, deployed, case_strength, current_strategy
            )

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        priority_queue = [w for w, _ in ranked[:5]]

        recommended_weapon = priority_queue[0] if priority_queue else None

        # Get perjury path status
        perjury_status = self._get_perjury_path_status(deployed)

        # Project case strength
        after_recommended = case_strength
        if recommended_weapon:
            impact = self.weapon_data.get(recommended_weapon, {}).get("impact", 0)
            after_recommended = min(98, case_strength + impact)

        if recommended_weapon:
            strategy = self.weapon_data[recommended_weapon]["strategy"]
            reason = f"Weapon {recommended_weapon} has high impact and fits {strategy}"
        else:
            strategy = current_strategy or "knowledge_closure"
            reason = "All primary weapons deployed."

        result = {
            "recommended_weapon": recommended_weapon,
            "reason": reason,
            "priority_queue": priority_queue,
            "strategy_focus": strategy,
            "perjury_path_status": perjury_status,
            "case_strength_projection": {
                "current": case_strength,
                "after_recommended": after_recommended,
            },
        }

        confidence = 0.8
        return self._format_response(result, confidence)

    def _check_dependencies(self, weapon: int, deployed: set) -> bool:
        """Check if all dependencies for a weapon are met."""
        deps = self.weapon_data.get(weapon, {}).get("dependencies", [])
        return all(d in deployed for d in deps)

    def _score_weapon(
        self,
        weapon: int,
        deployed: set,
        case_strength: float,
        current_strategy: Optional[str] = None,
    ) -> float:
        """Score a weapon based on impact and strategy fit."""
        data = self.weapon_data.get(weapon, {})
        score = float(data.get("impact", 0))

        if current_strategy:
            if data.get("strategy") == current_strategy:
                score += 5

        return score

    def _get_perjury_path_status(self, deployed: set) -> Dict[str, Dict[str, Any]]:
        """Get status of all perjury path chains."""
        status = {}
        for path_name, path_data in self.perjury_paths.items():
            weapons = path_data["weapons"]
            armed = sum(1 for w in weapons if w in deployed)

            status[path_name] = {
                "armed": armed,
                "total": len(weapons),
                "progress": f"{armed}/{len(weapons)}",
            }

        return status


__all__ = ["StrategyAgent"]

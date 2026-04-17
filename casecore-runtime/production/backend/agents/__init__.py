"""
CaseCore AI Agent System
========================

Agent registry and base class for the Mills v. Polley litigation platform.
Provides abstract base class for all specialized agents and agent registry.

Agents:
- opposition_agent: Predicts defense responses to interrogatory weapons
- strategy_agent: Recommends next weapon to deploy based on case state
- deposition_agent: Real-time deposition assistant with contradiction detection
- document_agent: Analyzes new evidence and maps to COAs/burden elements
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class BaseAgent(ABC):
    """
    Abstract base class for all CaseCore AI agents.

    All agents inherit from this and implement the analyze() method
    to provide specialized legal analysis for different case phases.

    Attributes:
        case_id: Unique identifier for the Mills v. Polley case (typically "mills-v-polley")
        config: Configuration dictionary for agent-specific settings
        created_at: Timestamp when agent was instantiated
    """

    def __init__(self, case_id: str, config: dict = None):
        """
        Initialize base agent.

        Args:
            case_id: Unique case identifier
            config: Optional configuration dictionary
        """
        self.case_id = case_id
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()

    @abstractmethod
    async def analyze(self, context: dict) -> dict:
        """
        Run agent analysis. Must be implemented by all subclasses.

        Args:
            context: Dictionary containing case-specific context and parameters
                    for the analysis

        Returns:
            Dictionary with structured analysis results. Format depends on
            agent type but always includes confidence scores and reasoning.

        Raises:
            NotImplementedError: If called directly on BaseAgent
        """
        pass

    def _validate_context(self, context: dict, required_keys: List[str]) -> bool:
        """
        Validate that context contains all required keys.

        Args:
            context: Context dictionary to validate
            required_keys: List of required top-level keys

        Returns:
            True if all required keys present

        Raises:
            ValueError: If required keys are missing
        """
        missing = [k for k in required_keys if k not in context]
        if missing:
            raise ValueError(f"Context missing required keys: {missing}")
        return True

    def _format_response(self, data: dict, confidence: float = 1.0) -> dict:
        """
        Format standard response envelope for all agents.

        Args:
            data: Analysis data to wrap
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Formatted response dictionary
        """
        return {
            "case_id": self.case_id,
            "agent_type": self.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": confidence,
            "data": data
        }


class AgentRegistry:
    """
    Central registry for all CaseCore agents.

    Manages agent instantiation, lifecycle, and coordination.
    Provides factory methods for creating agents with proper configuration.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents = {}
        self._cache = {}

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent instance.

        Args:
            name: Unique name for the agent
            agent: Instantiated agent object
        """
        self._agents[name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Retrieve a registered agent by name.

        Args:
            name: Name of the agent to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """
        List all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def clear_cache(self) -> None:
        """Clear analysis cache (useful between case phases)."""
        self._cache.clear()


# Global registry instance
_global_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry.

    Returns:
        Global AgentRegistry instance
    """
    return _global_registry


# Import all agent classes after BaseAgent is defined
from .opposition_agent import OppositionAgent, DefenseTactic, WeaponCategory
from .strategy_agent import StrategyAgent
from .deposition_agent import DepositionAgent, EVIDENCE_INDEX
from .document_agent import DocumentAgent, COAS, WEAPONS


__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "get_registry",
    "OppositionAgent",
    "StrategyAgent",
    "DepositionAgent",
    "DocumentAgent",
    "DefenseTactic",
    "WeaponCategory",
    "EVIDENCE_INDEX",
    "COAS",
    "WEAPONS",
]

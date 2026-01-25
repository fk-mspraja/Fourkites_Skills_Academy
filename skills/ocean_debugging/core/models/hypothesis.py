"""Hypothesis models for adaptive RCA investigation"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
import uuid


class Hypothesis(BaseModel):
    """A single hypothesis about root cause"""

    id: str = Field(default_factory=lambda: f"h_{uuid.uuid4().hex[:8]}")
    description: str
    root_cause_type: str  # e.g., "network_relationship_missing", "jt_scraping_error"
    confidence: float = 0.5
    status: Literal["active", "confirmed", "eliminated"] = "active"
    evidence_for: List[str] = Field(default_factory=list)  # Evidence IDs supporting
    evidence_against: List[str] = Field(default_factory=list)  # Evidence IDs contradicting
    suggested_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def update_confidence(self, new_confidence: float, evidence_id: str, supports: bool) -> None:
        """Update confidence and track evidence"""
        self.confidence = max(0.0, min(1.0, new_confidence))

        if supports:
            self.evidence_for.append(evidence_id)
        else:
            self.evidence_against.append(evidence_id)

        # Auto-update status based on confidence
        if self.confidence >= 0.85:
            self.status = "confirmed"
        elif self.confidence <= 0.15:
            self.status = "eliminated"


class AgentAction(BaseModel):
    """Action decided by sub-agent via LLM reasoning"""

    type: Literal["query_data_source", "spawn_child", "revisit", "conclude"]
    source: Optional[str] = None  # Client name: tracking_api, company_api, etc.
    method: Optional[str] = None  # Method name: get_tracking_by_id, etc.
    params: Dict[str, Any] = Field(default_factory=dict)
    child_hypothesis: Optional[str] = None  # For spawn_child action
    reason: str = ""  # LLM's reasoning for this action

    @classmethod
    def query(cls, source: str, method: str, params: Dict[str, Any], reason: str) -> "AgentAction":
        """Create a query_data_source action"""
        return cls(
            type="query_data_source",
            source=source,
            method=method,
            params=params,
            reason=reason
        )

    @classmethod
    def revisit(cls, source: str, method: str, params: Dict[str, Any], reason: str) -> "AgentAction":
        """Create a revisit action (same API, different params)"""
        return cls(
            type="revisit",
            source=source,
            method=method,
            params=params,
            reason=reason
        )

    @classmethod
    def spawn(cls, child_hypothesis: str, reason: str) -> "AgentAction":
        """Create a spawn_child action"""
        return cls(
            type="spawn_child",
            child_hypothesis=child_hypothesis,
            reason=reason
        )

    @classmethod
    def conclude(cls, reason: str) -> "AgentAction":
        """Create a conclude action"""
        return cls(
            type="conclude",
            reason=reason
        )


class SubAgentResult(BaseModel):
    """Result from a sub-investigation agent"""

    agent_id: str
    hypothesis: Hypothesis
    evidence: List[Any] = Field(default_factory=list)  # Evidence objects
    children: List[str] = Field(default_factory=list)  # Child agent IDs or hypothesis descriptions
    iterations: int = 0
    conclusion: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class RootCauseSynthesis(BaseModel):
    """Final synthesis of root cause from all hypotheses"""

    root_cause: Optional[str] = None
    root_cause_type: Optional[str] = None
    confidence: float = 0.0
    explanation: str = ""
    recommended_actions: List[str] = Field(default_factory=list)
    remaining_uncertainties: List[str] = Field(default_factory=list)
    hypotheses_tested: int = 0
    hypotheses_confirmed: int = 0
    hypotheses_eliminated: int = 0
    total_evidence: int = 0

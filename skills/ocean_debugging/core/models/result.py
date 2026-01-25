"""Investigation result models"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .evidence import Evidence


class RootCauseCategory(str, Enum):
    """Category of root cause"""
    CARRIER_ISSUE = "carrier_issue"
    JT_ISSUE = "jt_issue"
    CONFIGURATION_ISSUE = "configuration_issue"
    SYSTEM_BUG = "system_bug"
    UNKNOWN = "unknown"


class ActionPriority(str, Enum):
    """Priority level for recommended actions"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendedAction(BaseModel):
    """A recommended action based on root cause analysis"""

    action: str  # What to do
    priority: ActionPriority = ActionPriority.MEDIUM
    assignee: Optional[str] = None  # Who should do it
    human_approval_required: bool = False

    # Details
    description: Optional[str] = None
    steps: List[str] = Field(default_factory=list)

    # Impact
    estimated_affected_loads: Optional[int] = None
    pattern_detected: bool = False

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        lines = [
            f"**Action:** {self.action}",
            f"**Priority:** {self.priority.value}",
        ]
        if self.assignee:
            lines.append(f"**Assignee:** {self.assignee}")
        if self.human_approval_required:
            lines.append("**Human Approval Required:** Yes")
        if self.description:
            lines.append(f"\n{self.description}")
        if self.steps:
            lines.append("\n**Steps:**")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step}")
        return "\n".join(lines)


class InvestigationResult(BaseModel):
    """
    Final result of an ocean debugging investigation.

    Contains the root cause determination, supporting evidence,
    and recommended actions.
    """

    # Case context
    ticket_id: Optional[str] = None
    case_number: Optional[str] = None
    load_id: Optional[str] = None

    # Root cause
    root_cause: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    confidence: float = 0.0

    # Supporting information
    explanation: str = ""
    evidence: List[Evidence] = Field(default_factory=list)

    # Recommendations
    recommended_action: Optional[RecommendedAction] = None

    # Human handoff
    needs_human: bool = False
    human_question: Optional[str] = None

    # Metrics
    investigation_time: float = 0.0  # seconds
    steps_executed: int = 0
    queries_executed: int = 0

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Similar impact
    similar_loads_affected: int = 0
    pattern_detected: bool = False

    @property
    def is_resolved(self) -> bool:
        """Check if root cause was determined"""
        return self.root_cause is not None and not self.needs_human

    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level"""
        if self.confidence >= 0.9:
            return "Very High"
        if self.confidence >= 0.7:
            return "High"
        if self.confidence >= 0.5:
            return "Medium"
        if self.confidence >= 0.3:
            return "Low"
        return "Very Low"

    def to_markdown(self) -> str:
        """Convert to markdown report format"""
        lines = [
            f"# Investigation Report",
            f"",
            f"**Case:** {self.case_number}",
            f"**Load:** {self.load_id or 'N/A'}",
            f"**Investigation Time:** {self.investigation_time:.1f}s",
            f"",
        ]

        if self.is_resolved:
            lines.extend([
                f"## Root Cause",
                f"",
                f"**Root Cause:** {self.root_cause}",
                f"**Category:** {self.root_cause_category.value if self.root_cause_category else 'N/A'}",
                f"**Confidence:** {self.confidence:.0%} ({self.confidence_level})",
                f"",
                f"## Explanation",
                f"",
                self.explanation,
                f"",
            ])
        else:
            lines.extend([
                f"## Status: Human Review Required",
                f"",
                f"**Question:** {self.human_question}",
                f"",
            ])

        if self.evidence:
            lines.extend([
                f"## Evidence",
                f"",
            ])
            for ev in self.evidence:
                lines.append(f"- **[{ev.source.value}]** {ev.finding}")
            lines.append("")

        if self.recommended_action:
            lines.extend([
                f"## Recommended Action",
                f"",
                self.recommended_action.to_markdown(),
                f"",
            ])

        if self.similar_loads_affected > 0:
            lines.extend([
                f"## Similar Impact",
                f"",
                f"- **Affected Loads:** {self.similar_loads_affected}",
                f"- **Pattern Detected:** {'Yes' if self.pattern_detected else 'No'}",
                f"",
            ])

        return "\n".join(lines)

    def to_salesforce_update(self) -> Dict[str, Any]:
        """Convert to Salesforce field update"""
        return {
            "RCA_Root_Cause__c": self.root_cause,
            "RCA_Category__c": self.root_cause_category.value if self.root_cause_category else None,
            "RCA_Confidence__c": self.confidence,
            "RCA_Explanation__c": self.explanation[:32000] if self.explanation else None,  # SF limit
            "RCA_Analysis_Time__c": self.investigation_time,
            "RCA_Analyzed_Date__c": self.completed_at.isoformat(),
            "RCA_Needs_Human_Review__c": self.needs_human,
            "RCA_Similar_Loads__c": self.similar_loads_affected,
        }

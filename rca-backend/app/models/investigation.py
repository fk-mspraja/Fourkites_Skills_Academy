"""
Investigation State Models for LangGraph Multi-Agent RCA System
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import operator


class TransportMode(str, Enum):
    """Transport mode types"""
    OCEAN = "OCEAN"
    OTR = "OTR"
    AIR = "AIR"
    LTL = "LTL"
    INTERMODAL = "INTERMODAL"
    UNKNOWN = "UNKNOWN"


class RootCauseCategory(str, Enum):
    """Root cause categories"""
    LOAD_CREATION_FAILURE = "load_creation_failure"
    CONFIGURATION_ISSUE = "configuration_issue"
    JT_ISSUE = "jt_issue"
    CARRIER_ISSUE = "carrier_issue"
    NETWORK_RELATIONSHIP = "network_relationship"
    CALLBACK_FAILURE = "callback_failure"
    DATA_QUALITY = "data_quality"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Evidence:
    """Evidence supporting or contradicting a hypothesis"""
    source: str  # "Tracking API", "JT", "SigNoz", etc.
    finding: str  # Human-readable description
    supports_hypothesis: bool  # True if evidence supports, False if contradicts
    weight: float  # 0.0 - 1.0, how strong is this evidence
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Hypothesis:
    """A hypothesis about the root cause"""
    id: str
    description: str
    category: RootCauseCategory
    confidence: float  # 0.0 - 1.0
    evidence_for: List[Evidence] = field(default_factory=list)
    evidence_against: List[Evidence] = field(default_factory=list)
    needs_validation: bool = False
    validation_queries: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_confidence(self):
        """Recalculate confidence based on evidence"""
        if not self.evidence_for:
            self.confidence = 0.0
            return

        # Weight evidence for vs against
        for_score = sum(e.weight for e in self.evidence_for)
        against_score = sum(e.weight for e in self.evidence_against)

        # Calculate confidence with dampening
        total_evidence = len(self.evidence_for) + len(self.evidence_against)
        if total_evidence == 0:
            self.confidence = 0.0
        else:
            self.confidence = max(0.0, min(1.0, (for_score - against_score) / total_evidence))

        self.updated_at = datetime.now()


@dataclass
class Action:
    """Recommended action to fix the issue"""
    description: str
    priority: Literal["high", "medium", "low"]
    category: str  # "fix", "investigate", "escalate"
    details: Optional[str] = None


@dataclass
class RootCause:
    """Final determined root cause"""
    category: RootCauseCategory
    description: str
    confidence: float
    evidence: List[Evidence]
    recommended_actions: List[Action]
    determined_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentMessage:
    """Message from an agent for conversation UI"""
    agent: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: Optional[AgentStatus] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    """Event in the investigation timeline"""
    timestamp: datetime
    agent: str
    action: str
    duration_ms: Optional[int] = None
    result_summary: Optional[str] = None
    status: AgentStatus = AgentStatus.COMPLETED


@dataclass
class Query:
    """Executed query for data source panels"""
    source: str  # "Tracking API", "JT", "Redshift", etc.
    query: str  # The actual query (SQL, HTTP request, etc.)
    result_count: Optional[int] = None
    raw_result: Optional[Any] = None
    executed_at: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    error: Optional[str] = None


@dataclass
class InvestigationPlan:
    """Investigation plan created by planner agent"""
    steps: List[str]
    data_sources: List[str]
    priorities: Dict[str, int]  # step -> priority
    estimated_duration: Optional[int] = None  # seconds


@dataclass
class ProposedAction:
    """An action proposed by an agent for the group to consider"""
    agent: str  # Who is proposing
    action: str  # What to do (e.g., "query_redshift", "check_jt")
    target: str  # What to investigate (e.g., "validation_errors", "subscription")
    reasoning: str  # Why this action is needed
    priority: int  # 1-10, higher = more urgent
    depends_on: List[str] = field(default_factory=list)  # Other actions this depends on
    estimated_value: float = 0.5  # Expected information gain 0-1
    proposed_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentDiscussion:
    """A discussion message between agents"""
    agent: str  # Who is speaking
    message: str  # What they're saying
    message_type: Literal["observation", "proposal", "agreement", "disagreement", "question", "decision"]
    references: List[str] = field(default_factory=list)  # IDs of related findings/proposals
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CollaborativeDecision:
    """A decision made by the agent team"""
    selected_action: ProposedAction
    votes: Dict[str, bool]  # agent -> agrees
    rationale: str
    alternative_actions: List[ProposedAction] = field(default_factory=list)
    decided_at: datetime = field(default_factory=datetime.now)


class InvestigationState(TypedDict, total=False):
    """
    State managed by LangGraph StateGraph
    Uses Annotated with operator.add for list accumulation
    """
    # Input
    issue_text: str
    manual_identifiers: Dict[str, str]  # User-provided hints

    # Extracted metadata
    identifiers: Dict[str, Any]  # tracking_id, load_number, container, etc.
    issue_category: str
    transport_mode: TransportMode

    # Investigation plan
    plan: Optional[InvestigationPlan]
    current_step: int
    completed_steps: List[str]

    # Collected data (dicts merge automatically, lists accumulate with operator.add)
    tracking_data: Dict[str, Any]
    jt_data: Dict[str, Any]
    super_api_data: Dict[str, Any]
    redshift_data: Dict[str, Any]
    signoz_logs: Annotated[List[Dict], operator.add]
    athena_logs: Annotated[List[Dict], operator.add]
    network_data: Dict[str, Any]
    confluence_docs: Annotated[List[Dict], operator.add]
    slack_threads: Annotated[List[Dict], operator.add]
    logs_data: Dict[str, Any]  # Service logs (integrations-worker, carrier-files-worker, tracking-service)

    # Analysis results
    error_patterns: List[Dict[str, Any]]
    hypotheses: List[Hypothesis]
    validated_hypotheses: List[Hypothesis]

    # Root cause determination
    root_cause: Optional[RootCause]
    confidence: float
    recommended_actions: List[Action]

    # HITL (Human-in-the-Loop)
    needs_human: bool
    human_question: str
    human_response: Optional[str]

    # Metadata
    iteration_count: int
    max_iterations: int  # Prevent infinite loops
    agent_messages: Annotated[List[AgentMessage], operator.add]  # For UI conversation
    timeline_events: Annotated[List[TimelineEvent], operator.add]
    executed_queries: Annotated[List[Query], operator.add]  # For data source panels

    # Collaborative workflow
    proposed_actions: Annotated[List[ProposedAction], operator.add]  # Actions agents want to take
    agent_discussions: Annotated[List[AgentDiscussion], operator.add]  # Agent conversation
    decisions: Annotated[List[CollaborativeDecision], operator.add]  # Decisions made
    current_focus: str  # What the team is currently investigating
    investigation_phase: Literal["gathering", "analyzing", "concluding", "stuck"]  # Current phase
    available_agents: List[str]  # Which agents can contribute
    confidence_threshold: float  # Threshold to auto-conclude (default 0.85)

    # Investigation metadata
    investigation_id: str
    started_at: datetime
    completed_at: Optional[datetime]


# Helper functions for state manipulation

def create_initial_state(
    issue_text: str,
    manual_identifiers: Optional[Dict[str, str]] = None,
    investigation_id: Optional[str] = None
) -> InvestigationState:
    """Create initial investigation state"""
    import uuid
    return InvestigationState(
        issue_text=issue_text,
        manual_identifiers=manual_identifiers or {},
        identifiers={},
        issue_category="",
        transport_mode=TransportMode.UNKNOWN,
        plan=None,
        current_step=0,
        completed_steps=[],
        tracking_data={},
        jt_data={},
        super_api_data={},
        redshift_data={},
        signoz_logs=[],
        athena_logs=[],
        network_data={},
        confluence_docs=[],
        slack_threads=[],
        logs_data={},
        error_patterns=[],
        hypotheses=[],
        validated_hypotheses=[],
        root_cause=None,
        confidence=0.0,
        recommended_actions=[],
        needs_human=False,
        human_question="",
        human_response=None,
        iteration_count=0,
        max_iterations=10,
        agent_messages=[],
        timeline_events=[],
        executed_queries=[],
        # Collaborative workflow
        proposed_actions=[],
        agent_discussions=[],
        decisions=[],
        current_focus="initial_assessment",
        investigation_phase="gathering",
        available_agents=["tracking", "redshift", "callbacks", "super_api", "jt", "ocean_events", "ocean_trace", "confluence", "slack", "jira"],
        confidence_threshold=0.85,
        investigation_id=investigation_id or str(uuid.uuid4()),
        started_at=datetime.now(),
        completed_at=None
    )


def add_agent_message(state: InvestigationState, agent: str, message: str, status: Optional[AgentStatus] = None) -> Dict:
    """Helper to add agent message to state"""
    msg = AgentMessage(agent=agent, message=message, status=status)
    return {"agent_messages": [msg]}


def add_timeline_event(
    state: InvestigationState,
    agent: str,
    action: str,
    duration_ms: Optional[int] = None,
    result_summary: Optional[str] = None,
    status: AgentStatus = AgentStatus.COMPLETED
) -> Dict:
    """Helper to add timeline event to state"""
    event = TimelineEvent(
        timestamp=datetime.now(),
        agent=agent,
        action=action,
        duration_ms=duration_ms,
        result_summary=result_summary,
        status=status
    )
    return {"timeline_events": [event]}


def add_query(
    state: InvestigationState,
    source: str,
    query: str,
    result_count: Optional[int] = None,
    raw_result: Optional[Any] = None,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
) -> Dict:
    """Helper to add executed query to state"""
    q = Query(
        source=source,
        query=query,
        result_count=result_count,
        raw_result=raw_result,
        duration_ms=duration_ms,
        error=error
    )
    return {"executed_queries": [q]}

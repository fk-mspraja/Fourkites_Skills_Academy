"""Investigation state management models"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatusEnum(str, Enum):
    """Status of a parallel task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(BaseModel):
    """Status tracking for a parallel task"""
    task_id: str
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class StepResult(BaseModel):
    """Result of executing an investigation step"""
    step_id: str
    step_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_empty(self) -> bool:
        """Check if step returned no meaningful data"""
        if not self.success:
            return True
        if not self.data:
            return True
        # Check for empty result patterns
        if self.data.get("count", -1) == 0:
            return True
        if self.data.get("rows") == []:
            return True
        return False


class InvestigationState(BaseModel):
    """
    Central state machine for ocean debugging investigation.

    Tracks the entire investigation process including:
    - Ticket context and identifiers
    - Current progress through decision tree
    - All evidence collected
    - Parallel task execution status
    - Final determination
    """

    # Ticket context
    ticket_id: str
    case_number: str
    identifiers: Dict[str, Any] = Field(default_factory=dict)

    # Investigation progress
    current_step: str = "init"
    completed_steps: List[StepResult] = Field(default_factory=list)
    parallel_tasks: Dict[str, TaskStatus] = Field(default_factory=dict)

    # Evidence accumulation
    evidence: List[Any] = Field(default_factory=list)  # List[Evidence]

    # Root cause determination
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    confidence: float = 0.0
    explanation: Optional[str] = None

    # Human handoff
    needs_human: bool = False
    human_question: Optional[str] = None
    human_response: Optional[str] = None

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    iteration_count: int = 0
    max_iterations: int = 10

    def add_step_result(self, result: StepResult) -> None:
        """Add a completed step result"""
        self.completed_steps.append(result)
        self.updated_at = datetime.utcnow()

    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Get result for a specific step"""
        for step in self.completed_steps:
            if step.step_id == step_id:
                return step
        return None

    def has_completed_step(self, step_id: str) -> bool:
        """Check if a step has been completed"""
        return any(s.step_id == step_id for s in self.completed_steps)

    def is_complete(self) -> bool:
        """Check if investigation is complete"""
        if self.root_cause is not None:
            return True
        if self.needs_human:
            return True
        if self.iteration_count >= self.max_iterations:
            return True
        return False

    def increment_iteration(self) -> None:
        """Increment iteration counter"""
        self.iteration_count += 1
        self.updated_at = datetime.utcnow()

    def set_human_handoff(self, question: str) -> None:
        """Set human handoff state"""
        self.needs_human = True
        self.human_question = question
        self.updated_at = datetime.utcnow()

    def set_root_cause(
        self,
        root_cause: str,
        category: str,
        confidence: float,
        explanation: str
    ) -> None:
        """Set the determined root cause"""
        self.root_cause = root_cause
        self.root_cause_category = category
        self.confidence = confidence
        self.explanation = explanation
        self.updated_at = datetime.utcnow()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since investigation started"""
        return (datetime.utcnow() - self.started_at).total_seconds()

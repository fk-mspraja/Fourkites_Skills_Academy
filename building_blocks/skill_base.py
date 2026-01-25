"""
Base class for all RCA Skills in the Skills-Empowered Platform.

This module provides the abstract base class that all specialized RCA skills
inherit from, defining the core interfaces for pattern-based root cause analysis.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class RootCauseCategory(Enum):
    """Categories of root causes for logistics tracking issues."""

    ELD_NOT_ENABLED = "eld_not_enabled"
    NETWORK_MISSING = "network_missing"
    LOAD_NOT_FOUND = "load_not_found"
    CARRIER_API_DOWN = "carrier_api_down"
    GPS_ISSUES = "gps_issues"
    DEVICE_CONFIG = "device_config"
    CALLBACK_FAILURE = "callback_failure"
    UNKNOWN = "unknown"


@dataclass
class Evidence:
    """Evidence for or against a hypothesis.

    Attributes:
        source: Data source that provided this evidence (e.g., "database", "API")
        finding: Description of what was found
        weight: Importance weight from 1-10 (10 being most important)
        confidence: Confidence in this evidence from 0-100%
        timestamp: When this evidence was collected
        metadata: Additional contextual information
    """
    source: str
    finding: str
    weight: int  # 1-10
    confidence: int  # 0-100
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate evidence parameters."""
        if not 1 <= self.weight <= 10:
            raise ValueError(f"Weight must be between 1-10, got {self.weight}")
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be between 0-100, got {self.confidence}")


@dataclass
class Hypothesis:
    """A potential root cause hypothesis.

    Attributes:
        pattern_id: Identifier for the pattern being tested
        category: Root cause category
        description: Human-readable description of this hypothesis
        evidence_for: List of evidence supporting this hypothesis
        evidence_against: List of evidence contradicting this hypothesis
        confidence_score: Overall confidence from 0.0-1.0
    """
    pattern_id: str
    category: RootCauseCategory
    description: str
    evidence_for: List[Evidence]
    evidence_against: List[Evidence]
    confidence_score: float  # 0.0-1.0

    def __post_init__(self):
        """Validate hypothesis parameters."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                f"Confidence score must be between 0.0-1.0, got {self.confidence_score}"
            )


@dataclass
class Resolution:
    """Resolution steps for a root cause.

    Attributes:
        root_cause: Identified root cause description
        explanation: Detailed explanation of the issue
        steps: List of actionable resolution steps
        email_template: Optional email template for customer communication
        estimated_time: Estimated time to resolve (e.g., "2-4 hours")
        human_approval_required: Whether human approval is needed before execution
        priority: Priority level (1=highest, 5=lowest)
        automation_available: Whether automated resolution is possible
    """
    root_cause: str
    explanation: str
    steps: List[Dict[str, Any]]
    email_template: Optional[str] = None
    estimated_time: str = "Unknown"
    human_approval_required: bool = True
    priority: int = 3
    automation_available: bool = False

    def __post_init__(self):
        """Validate resolution parameters."""
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Priority must be between 1-5, got {self.priority}")


class Skill(ABC):
    """Abstract base class for all RCA Skills.

    All specialized skills (ELDSkill, NetworkSkill, etc.) must inherit from this
    base class and implement the required abstract methods.

    Attributes:
        skill_name: Name of the skill (e.g., "ELD Investigation")
        version: Semantic version of the skill
        patterns: Pattern definitions loaded from configuration
    """

    def __init__(self, skill_name: str, version: str = "1.0.0"):
        """Initialize the skill.

        Args:
            skill_name: Name of the skill
            version: Semantic version string
        """
        self.skill_name = skill_name
        self.version = version
        self.patterns = self.load_patterns()
        self._validate_patterns()

    @abstractmethod
    def load_patterns(self) -> Dict[str, Dict]:
        """Load pattern definitions from YAML/JSON configuration.

        Returns:
            Dictionary mapping pattern IDs to pattern definitions.
            Each pattern should include:
            - category: RootCauseCategory
            - description: str
            - evidence_checks: List[Dict]
            - resolution: Dict (steps, email_template, etc.)
        """
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill investigation.

        This is the main entry point for skill execution. It should:
        1. Gather required data
        2. Generate and evaluate hypotheses
        3. Select the best hypothesis
        4. Return resolution steps

        Args:
            context: Investigation context containing:
                - load_number: str
                - description: str (optional)
                - additional contextual data

        Returns:
            Investigation result dictionary with:
            - root_cause: str
            - confidence: float (0.0-1.0)
            - resolution: Resolution object
            - hypotheses: List[Hypothesis]
            - evidence: List[Evidence]
        """
        pass

    def _validate_patterns(self) -> None:
        """Validate that loaded patterns have required structure."""
        required_fields = ["category", "description", "evidence_checks", "resolution"]

        for pattern_id, pattern in self.patterns.items():
            for field in required_fields:
                if field not in pattern:
                    raise ValueError(
                        f"Pattern '{pattern_id}' missing required field '{field}'"
                    )

            # Validate category is a valid RootCauseCategory
            category_str = pattern["category"]
            try:
                if isinstance(category_str, str):
                    RootCauseCategory(category_str)
            except ValueError:
                raise ValueError(
                    f"Pattern '{pattern_id}' has invalid category '{category_str}'"
                )

    def _evaluate_hypotheses(self,
                            data_results: Dict[str, Any]) -> List[Hypothesis]:
        """Generate and evaluate hypotheses based on collected data.

        This method:
        1. Iterates through all loaded patterns
        2. Evaluates evidence checks against the data
        3. Generates Evidence objects for matching/non-matching checks
        4. Calculates confidence scores
        5. Returns ranked hypotheses

        Args:
            data_results: Dictionary of data gathered from various sources

        Returns:
            List of Hypothesis objects, sorted by confidence (highest first)
        """
        hypotheses = []

        for pattern_id, pattern in self.patterns.items():
            evidence_for = []
            evidence_against = []

            # Evaluate each evidence check in the pattern
            for check in pattern.get("evidence_checks", []):
                result = self._evaluate_check(check, data_results)

                if result["matched"]:
                    evidence_for.append(Evidence(
                        source=check.get("source", "unknown"),
                        finding=result.get("finding", check.get("description", "")),
                        weight=check.get("weight", 5),
                        confidence=result.get("confidence", 100),
                        metadata=result.get("metadata", {})
                    ))
                elif result.get("contradicts", False):
                    evidence_against.append(Evidence(
                        source=check.get("source", "unknown"),
                        finding=result.get("finding", "Evidence contradicts pattern"),
                        weight=check.get("weight", 5),
                        confidence=result.get("confidence", 100),
                        metadata=result.get("metadata", {})
                    ))

            # Calculate overall confidence for this hypothesis
            confidence = self._calculate_confidence(evidence_for, evidence_against)

            # Convert category string to enum
            category = pattern["category"]
            if isinstance(category, str):
                category = RootCauseCategory(category)

            hypotheses.append(Hypothesis(
                pattern_id=pattern_id,
                category=category,
                description=pattern["description"],
                evidence_for=evidence_for,
                evidence_against=evidence_against,
                confidence_score=confidence
            ))

        # Sort by confidence score (highest first)
        hypotheses.sort(key=lambda h: h.confidence_score, reverse=True)

        return hypotheses

    def _evaluate_check(self,
                       check: Dict[str, Any],
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single evidence check against data.

        Args:
            check: Evidence check definition from pattern
            data: Data results to check against

        Returns:
            Dictionary with:
            - matched: bool
            - finding: str (description of what was found)
            - confidence: int (0-100)
            - contradicts: bool (whether this contradicts the hypothesis)
            - metadata: Dict (additional context)
        """
        # Default implementation - subclasses can override
        check_type = check.get("type", "field_check")

        if check_type == "field_check":
            return self._evaluate_field_check(check, data)
        elif check_type == "condition":
            return self._evaluate_condition(check, data)
        else:
            return {
                "matched": False,
                "finding": f"Unknown check type: {check_type}",
                "confidence": 0,
                "contradicts": False
            }

    def _evaluate_field_check(self,
                             check: Dict[str, Any],
                             data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a field existence/value check.

        Args:
            check: Check definition with 'field', 'expected_value', etc.
            data: Data to check

        Returns:
            Evaluation result
        """
        field_path = check.get("field", "")
        expected = check.get("expected_value")

        # Navigate nested fields using dot notation
        value = data
        for part in field_path.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        matched = False
        contradicts = False

        if expected is not None:
            matched = (value == expected)
            contradicts = (value is not None and value != expected)
        else:
            # Just checking field exists
            matched = (value is not None)

        return {
            "matched": matched,
            "finding": f"Field '{field_path}' = {value}",
            "confidence": 100 if matched else 50,
            "contradicts": contradicts,
            "metadata": {"field": field_path, "value": value}
        }

    def _evaluate_condition(self,
                           check: Dict[str, Any],
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a conditional check (>, <, contains, etc.).

        Args:
            check: Check definition with 'condition', 'field', etc.
            data: Data to check

        Returns:
            Evaluation result
        """
        # Placeholder for condition evaluation
        # Subclasses should implement specific logic
        return {
            "matched": False,
            "finding": "Condition evaluation not implemented",
            "confidence": 0,
            "contradicts": False
        }

    def _calculate_confidence(self,
                             evidence_for: List[Evidence],
                             evidence_against: List[Evidence]) -> float:
        """Calculate overall confidence score based on evidence.

        Uses weighted scoring where each evidence item contributes based on
        its weight (importance) and confidence level.

        Args:
            evidence_for: Evidence supporting the hypothesis
            evidence_against: Evidence contradicting the hypothesis

        Returns:
            Confidence score from 0.0 (no confidence) to 1.0 (certain)
        """
        if not evidence_for:
            return 0.0

        # Calculate weighted scores
        total_for = sum(e.weight * (e.confidence / 100) for e in evidence_for)
        total_against = sum(e.weight * (e.confidence / 100) for e in evidence_against)

        if total_for + total_against == 0:
            return 0.0

        # Confidence is the proportion of supporting evidence
        confidence = total_for / (total_for + total_against)

        # Ensure it's within [0.0, 1.0]
        return min(1.0, max(0.0, confidence))

    def _select_best_hypothesis(self,
                               hypotheses: List[Hypothesis],
                               confidence_threshold: float = 0.6) -> Optional[Hypothesis]:
        """Select the best hypothesis from the list.

        Args:
            hypotheses: List of evaluated hypotheses
            confidence_threshold: Minimum confidence to accept a hypothesis

        Returns:
            Best hypothesis if one exceeds threshold, None otherwise
        """
        if not hypotheses:
            return None

        # Hypotheses are already sorted by confidence (highest first)
        best = hypotheses[0]

        if best.confidence_score >= confidence_threshold:
            return best

        return None

    def _create_resolution(self,
                          hypothesis: Hypothesis) -> Resolution:
        """Create resolution steps from a hypothesis.

        Args:
            hypothesis: The selected hypothesis

        Returns:
            Resolution object with actionable steps
        """
        pattern = self.patterns.get(hypothesis.pattern_id, {})
        resolution_config = pattern.get("resolution", {})

        return Resolution(
            root_cause=hypothesis.description,
            explanation=resolution_config.get("explanation", ""),
            steps=resolution_config.get("steps", []),
            email_template=resolution_config.get("email_template"),
            estimated_time=resolution_config.get("estimated_time", "Unknown"),
            human_approval_required=resolution_config.get(
                "human_approval_required", True
            ),
            priority=resolution_config.get("priority", 3),
            automation_available=resolution_config.get("automation_available", False)
        )

    def get_metadata(self) -> Dict[str, Any]:
        """Get skill metadata.

        Returns:
            Dictionary with skill name, version, and pattern count
        """
        return {
            "skill_name": self.skill_name,
            "version": self.version,
            "pattern_count": len(self.patterns),
            "patterns": list(self.patterns.keys())
        }

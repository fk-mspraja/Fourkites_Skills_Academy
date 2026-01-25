"""Decision engine for evaluating investigation results"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models.state import InvestigationState, StepResult
from .models.evidence import Evidence
from .models.result import RootCauseCategory, ActionPriority, RecommendedAction
from .utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Decision:
    """A decision from the decision engine"""
    name: str = ""
    root_cause: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    confidence: float = 0.0
    next_step: Optional[str] = None
    needs_human: bool = False
    question: Optional[str] = None
    explanation: Optional[str] = None
    recommended_action: Optional[RecommendedAction] = None


class DecisionEngine:
    """
    Evaluates decision tree rules against investigation state.

    Loads the decision tree from YAML and evaluates conditions
    against accumulated evidence to determine root cause.
    """

    def __init__(self, decision_tree_path: Optional[str] = None):
        if decision_tree_path is None:
            # Default to skill's decision tree
            skill_dir = Path(__file__).parent.parent
            decision_tree_path = str(skill_dir / "decision_tree.yaml")

        self.tree_path = decision_tree_path
        self.tree = self._load_tree()

    def _load_tree(self) -> Dict[str, Any]:
        """Load decision tree from YAML"""
        try:
            with open(self.tree_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Decision tree not found: {self.tree_path}")
            return {"steps": {}}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse decision tree: {e}")
            return {"steps": {}}

    def evaluate(self, state: InvestigationState) -> Decision:
        """
        Evaluate decision tree against current state.

        Args:
            state: Current investigation state with completed steps

        Returns:
            Decision with root cause or next step
        """
        # Get current step configuration
        step_config = self.tree.get("steps", {}).get(state.current_step, {})

        if not step_config:
            logger.warning(f"No config for step: {state.current_step}")
            return Decision(
                needs_human=True,
                question=f"Unknown step: {state.current_step}. What should I do next?"
            )

        # Get the result for current step
        step_result = state.get_step_result(state.current_step)

        if not step_result:
            # Step not yet completed
            return Decision(next_step=state.current_step)

        # Evaluate each decision condition
        decisions = step_config.get("decisions", {})
        for decision_name, config in decisions.items():
            condition = config.get("condition", "")

            if self._evaluate_condition(condition, step_result, state):
                logger.info(f"Decision matched: {decision_name}")
                return self._build_decision(decision_name, config, state)

        # No decision matched - use default next step
        default_next = step_config.get("next_step")
        if default_next:
            return Decision(next_step=default_next)

        # No default - need human help
        return Decision(
            needs_human=True,
            question="No decision conditions matched. What should I check next?"
        )

    def _evaluate_condition(
        self,
        condition: str,
        step_result: StepResult,
        state: InvestigationState
    ) -> bool:
        """
        Evaluate a condition string against step result.

        Conditions are strings like:
        - "result.load_exists == false"
        - "result.count == 0"
        - "result.status == 'AWAITING_TRACKING_INFO'"
        """
        if not condition:
            return False

        try:
            # Parse the condition
            # Format: field.path operator value
            match = re.match(
                r"result\.(\w+(?:\.\w+)*)\s*(==|!=|>|<|>=|<=)\s*(.+)",
                condition.strip()
            )

            if not match:
                logger.warning(f"Could not parse condition: {condition}")
                return False

            field_path = match.group(1)
            operator = match.group(2)
            expected = match.group(3).strip()

            # Get actual value from result
            actual = self._get_nested_value(step_result.data, field_path)

            # Parse expected value
            expected_val = self._parse_value(expected)

            # Compare
            return self._compare(actual, operator, expected_val)

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation"""
        parts = path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value to appropriate type"""
        value_str = value_str.strip()

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Null
        if value_str.lower() in ("null", "none"):
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # String (with or without quotes)
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]

        return value_str

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare two values with given operator"""
        if operator == "==":
            return actual == expected
        if operator == "!=":
            return actual != expected
        if operator == ">":
            return actual is not None and actual > expected
        if operator == "<":
            return actual is not None and actual < expected
        if operator == ">=":
            return actual is not None and actual >= expected
        if operator == "<=":
            return actual is not None and actual <= expected
        return False

    def _build_decision(
        self,
        decision_name: str,
        config: Dict[str, Any],
        state: InvestigationState
    ) -> Decision:
        """Build a Decision object from config"""
        conclusion = config.get("conclusion", {})

        # Map category string to enum
        category_str = conclusion.get("category")
        category = None
        if category_str:
            category_map = {
                "carrier_issue": RootCauseCategory.CARRIER_ISSUE,
                "jt_issue": RootCauseCategory.JT_ISSUE,
                "configuration_issue": RootCauseCategory.CONFIGURATION_ISSUE,
                "system_bug": RootCauseCategory.SYSTEM_BUG,
            }
            category = category_map.get(category_str, RootCauseCategory.UNKNOWN)

        # Build recommended action if present
        action_config = config.get("recommended_action", {})
        recommended_action = None
        if action_config:
            priority_str = action_config.get("priority", "medium")
            priority_map = {
                "immediate": ActionPriority.IMMEDIATE,
                "high": ActionPriority.HIGH,
                "medium": ActionPriority.MEDIUM,
                "low": ActionPriority.LOW,
            }
            recommended_action = RecommendedAction(
                action=action_config.get("action", "Review and resolve"),
                priority=priority_map.get(priority_str, ActionPriority.MEDIUM),
                assignee=action_config.get("assignee"),
                human_approval_required=action_config.get("human_approval_required", False)
            )

        return Decision(
            name=decision_name,
            root_cause=conclusion.get("root_cause"),
            root_cause_category=category,
            confidence=config.get("confidence", 0.5),
            next_step=config.get("next_step"),
            needs_human=config.get("human_approval_required", False),
            explanation=conclusion.get("explanation"),
            recommended_action=recommended_action
        )

    def evaluate_all_evidence(
        self,
        state: InvestigationState
    ) -> Decision:
        """
        Evaluate all collected evidence to determine root cause.

        This is called after all steps are complete to make final determination.
        """
        evidence_list = state.evidence

        # Check for network relationship missing (highest priority)
        network_evidence = self._find_evidence_by_step(evidence_list, "step_5_network_check")
        if network_evidence:
            data = network_evidence.raw_data
            if not data.get("exists", True):
                # Get similar loads count
                similar = self._find_evidence_by_step(evidence_list, "step_6_similar_loads")
                affected_loads = similar.raw_data.get("affected_loads", 0) if similar else 0

                return Decision(
                    name="network_relationship_missing",
                    root_cause="network_relationship_missing",
                    root_cause_category=RootCauseCategory.CONFIGURATION_ISSUE,
                    confidence=0.95,
                    explanation=(
                        "No carrier-shipper relationship exists in the system. "
                        "This is the #1 cause of 'Awaiting Tracking Info' (7.7% of loads). "
                        f"Found {affected_loads} other loads from same carrier also stuck."
                    ),
                    recommended_action=RecommendedAction(
                        action="Create carrier-shipper network relationship",
                        priority=ActionPriority.IMMEDIATE,
                        assignee="Network Team",
                        human_approval_required=True,
                        estimated_affected_loads=affected_loads,
                        pattern_detected=affected_loads > 10
                    )
                )

        # Check for JT discrepancies
        jt_evidence = self._find_evidence_by_step(evidence_list, "step_3_jt_history")
        if jt_evidence:
            data = jt_evidence.raw_data
            if data.get("has_discrepancies"):
                return Decision(
                    name="jt_formatting_error",
                    root_cause="jt_scraping_error",
                    root_cause_category=RootCauseCategory.JT_ISSUE,
                    confidence=0.85,
                    explanation=(
                        "JT scraping shows discrepancies between crawled output "
                        "and formatted response. Data is being incorrectly transformed."
                    ),
                    recommended_action=RecommendedAction(
                        action="Create JT bug ticket with evidence",
                        priority=ActionPriority.HIGH,
                        assignee="JT Team"
                    )
                )
            if data.get("events_count", 0) == 0:
                return Decision(
                    name="no_jt_data",
                    root_cause="carrier_portal_issue",
                    root_cause_category=RootCauseCategory.CARRIER_ISSUE,
                    confidence=0.7,
                    explanation=(
                        "No scraping history found in JT. Carrier portal may not "
                        "have data or portal structure may have changed."
                    ),
                    recommended_action=RecommendedAction(
                        action="Check carrier portal manually and verify JT subscription",
                        priority=ActionPriority.HIGH
                    )
                )

        # Check SigNoz logs
        signoz_evidence = self._find_evidence_by_step(evidence_list, "step_4_signoz_logs")
        if signoz_evidence:
            data = signoz_evidence.raw_data
            if data.get("count", 0) == 0:
                return Decision(
                    name="no_processing_logs",
                    root_cause="configuration_issue",
                    root_cause_category=RootCauseCategory.CONFIGURATION_ISSUE,
                    confidence=0.6,
                    explanation=(
                        "No PROCESS_OCEAN_UPDATE logs found. Load may not be "
                        "configured for tracking or subscription is inactive."
                    ),
                    needs_human=True,
                    question="No processing logs found. Should I check tracking configuration?"
                )

        # No clear root cause - need human
        return Decision(
            needs_human=True,
            confidence=0.3,
            question=(
                "Could not determine root cause from available evidence. "
                "Please review the collected data and provide guidance."
            )
        )

    def _find_evidence_by_step(
        self,
        evidence_list: List[Evidence],
        step_id: str
    ) -> Optional[Evidence]:
        """Find evidence for a specific step"""
        for ev in evidence_list:
            if ev.step_id == step_id:
                return ev
        return None

    def calculate_confidence(self, state: InvestigationState) -> float:
        """
        Calculate overall confidence based on evidence quality.

        Factors:
        - Number of evidence sources
        - Agreement between sources
        - Data freshness
        - Evidence type weights
        """
        if not state.evidence:
            return 0.0

        # Base confidence from evidence count
        evidence_count = len(state.evidence)
        base_confidence = min(0.5, evidence_count * 0.1)

        # Source diversity bonus
        sources = set(ev.source for ev in state.evidence)
        diversity_bonus = min(0.2, len(sources) * 0.05)

        # Success rate bonus
        completed_steps = len(state.completed_steps)
        successful_steps = sum(1 for s in state.completed_steps if s.success)
        success_rate = successful_steps / max(1, completed_steps)
        success_bonus = success_rate * 0.3

        total = base_confidence + diversity_bonus + success_bonus
        return min(1.0, total)

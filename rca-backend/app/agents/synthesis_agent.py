"""
Synthesis Agent
Determines final root cause from validated hypotheses
"""
from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.models import (
    InvestigationState,
    RootCause,
    Action,
    RootCauseCategory
)


class SynthesisAgent(BaseAgent):
    """Determines final root cause from hypotheses"""

    def __init__(self):
        super().__init__("Synthesis Agent")
        self.confidence_threshold = 0.80

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Determine final root cause from hypotheses

        Returns:
            State updates with:
            - root_cause: RootCause object or None
            - confidence: float
            - recommended_actions: List[Action]
            - needs_human: bool (if confidence too low)
            - human_question: str (if HITL needed)
        """
        hypotheses = state.get("hypotheses", [])

        if not hypotheses:
            return {
                "root_cause": None,
                "confidence": 0.0,
                "needs_human": True,
                "human_question": "No hypotheses were formed. Please review the collected data.",
                "_message": "No hypotheses found - requesting human review"
            }

        # Sort by confidence
        sorted_hypotheses = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)
        top_hypothesis = sorted_hypotheses[0]

        # Check if we can auto-determine
        if top_hypothesis.confidence >= self.confidence_threshold:
            # High confidence - determine root cause
            root_cause = RootCause(
                category=top_hypothesis.category,
                description=top_hypothesis.description,
                confidence=top_hypothesis.confidence,
                evidence=top_hypothesis.evidence_for,
                recommended_actions=self._get_actions_for_category(top_hypothesis.category)
            )

            return {
                "root_cause": root_cause,
                "confidence": top_hypothesis.confidence,
                "recommended_actions": root_cause.recommended_actions,
                "needs_human": False,
                "_message": f"Root cause determined: {root_cause.description} ({root_cause.confidence:.0%} confidence)"
            }

        # Check for multiple competing hypotheses
        high_confidence_count = len([h for h in sorted_hypotheses if h.confidence > 0.60])

        if high_confidence_count > 1:
            # Multiple plausible hypotheses - need human input
            hypothesis_list = "\n".join([
                f"- {h.description} ({h.confidence:.0%} confidence)"
                for h in sorted_hypotheses[:3]
            ])

            return {
                "root_cause": None,
                "confidence": top_hypothesis.confidence,
                "needs_human": True,
                "human_question": f"Multiple possible root causes found:\n\n{hypothesis_list}\n\nWhich seems most likely based on your domain knowledge?",
                "_message": f"Multiple competing hypotheses - requesting human review"
            }

        # Low confidence on all hypotheses
        return {
            "root_cause": None,
            "confidence": top_hypothesis.confidence,
            "needs_human": True,
            "human_question": f"Could not determine root cause with high confidence. Top hypothesis:\n\n{top_hypothesis.description} ({top_hypothesis.confidence:.0%})\n\nEvidence:\n" + "\n".join([f"- {e.finding}" for e in top_hypothesis.evidence_for[:3]]) + "\n\nDoes this seem correct?",
            "_message": f"Low confidence ({top_hypothesis.confidence:.0%}) - requesting human review"
        }

    def _get_actions_for_category(self, category: RootCauseCategory) -> List[Action]:
        """Get recommended actions for a root cause category"""
        action_map = {
            RootCauseCategory.LOAD_CREATION_FAILURE: [
                Action(
                    description="Check load validation errors in Redshift",
                    priority="high",
                    category="investigate",
                    details="Query load_validation_data_mart for error details"
                ),
                Action(
                    description="Verify input file format or API payload",
                    priority="high",
                    category="investigate"
                )
            ],
            RootCauseCategory.NETWORK_RELATIONSHIP: [
                Action(
                    description="Create carrier-shipper network relationship",
                    priority="high",
                    category="fix",
                    details="Use Company API or admin portal to establish relationship"
                ),
                Action(
                    description="Verify carrier SCAC code is correct",
                    priority="medium",
                    category="investigate"
                )
            ],
            RootCauseCategory.JT_ISSUE: [
                Action(
                    description="Check JT scraping errors and portal access",
                    priority="high",
                    category="investigate",
                    details="Review subscription history and credential status"
                ),
                Action(
                    description="Verify carrier portal is accessible",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Escalate to JT team if portal changed",
                    priority="medium",
                    category="escalate"
                )
            ],
            RootCauseCategory.CONFIGURATION_ISSUE: [
                Action(
                    description="Review and fix tracking configuration",
                    priority="high",
                    category="fix",
                    details="Update subscription settings or tracking source"
                ),
                Action(
                    description="Enable disabled subscriptions if needed",
                    priority="high",
                    category="fix"
                )
            ],
            RootCauseCategory.CARRIER_ISSUE: [
                Action(
                    description="Contact carrier to verify status",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Check if carrier API/ELD is operational",
                    priority="medium",
                    category="investigate"
                )
            ],
            RootCauseCategory.CALLBACK_FAILURE: [
                Action(
                    description="Check callback logs in SigNoz/Athena",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Verify customer webhook endpoint is accessible",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Retry failed callbacks if endpoint is fixed",
                    priority="medium",
                    category="fix"
                )
            ],
            RootCauseCategory.DATA_QUALITY: [
                Action(
                    description="Identify data quality issues in source",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Contact data provider to fix issues",
                    priority="medium",
                    category="escalate"
                )
            ],
            RootCauseCategory.SYSTEM_ERROR: [
                Action(
                    description="Review system logs for errors",
                    priority="high",
                    category="investigate"
                ),
                Action(
                    description="Escalate to engineering if system bug",
                    priority="high",
                    category="escalate"
                )
            ],
        }

        return action_map.get(category, [
            Action(
                description="Manual investigation required",
                priority="high",
                category="investigate",
                details="Root cause category not recognized by automated system"
            )
        ])

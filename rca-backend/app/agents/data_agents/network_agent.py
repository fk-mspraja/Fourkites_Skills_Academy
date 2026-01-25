"""
Network API Data Collection Agent
Checks carrier-shipper relationship configuration
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.company_api_client import CompanyAPIClient


class NetworkAgent(BaseAgent):
    """
    Checks carrier-shipper network relationships with verbose output.

    Role: Network Configuration Analyst
    I verify that carriers and shippers are properly connected in the FourKites network.
    """

    def __init__(self):
        super().__init__("Network Agent")
        self.client = CompanyAPIClient()

    def _merge_updates(self, updates: Dict, new_update: Dict) -> Dict:
        """Helper to merge updates, handling list accumulation"""
        for key, value in new_update.items():
            if key in updates and isinstance(updates[key], list) and isinstance(value, list):
                updates[key] = updates[key] + value
            else:
                updates[key] = value
        return updates

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Check if carrier-shipper relationship exists with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        # Get carrier and shipper from tracking data or identifiers
        tracking_data = state.get("tracking_data", {})
        identifiers = state.get("identifiers", {})

        carrier_name = tracking_data.get("carrier") or identifiers.get("carrier_name")
        shipper_id = tracking_data.get("shipperCompanyId") or identifiers.get("shipper_id")
        shipper_name = tracking_data.get("shipper") or identifiers.get("shipper_name")

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking network relationship configuration.\n" +
                    f"  • Carrier: {carrier_name or 'not available'}\n" +
                    f"  • Shipper ID: {shipper_id or 'not available'}\n" +
                    f"  • Shipper Name: {shipper_name or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not carrier_name or (not shipper_id and not shipper_name):
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] Missing carrier or shipper information. Need both to check network relationship.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "network_data": {"skipped": True, "reason": "Missing carrier or shipper info"},
                "_message": "Cannot check network: missing carrier or shipper"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will check Network API to verify:\n" +
                    "  • Carrier-shipper relationship exists\n" +
                    "  • Network connection is active\n" +
                    "  • Configuration is correct for tracking",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Note: Current implementation limitation
        think = AgentDiscussion(
            agent=self.name,
            message="[Thinking] Network API requires company IDs (not names) for relationship lookup.\n" +
                    "  • We have carrier name but need carrier ID\n" +
                    "  • This lookup is not yet implemented\n" +
                    "  • For now, marking as skipped",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(think)

        # For now, skip network check as we need company IDs not names
        finding = AgentDiscussion(
            agent=self.name,
            message="[Finding] Network check skipped due to implementation limitation.\n" +
                    f"  • Carrier: {carrier_name}\n" +
                    f"  • Shipper: {shipper_name or shipper_id}\n" +
                    "  • Note: Manual verification needed in Company API",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(finding)

        return {
            **updates,
            "network_data": {
                "skipped": True,
                "reason": "Network API requires company IDs (not implemented yet)",
                "carrier_name": carrier_name,
                "shipper_name": shipper_name,
                "shipper_id": shipper_id
            },
            "_message": "Skipped Network API (requires company IDs)"
        }

    def _build_message(self, result: Dict[str, Any], carrier: str, shipper: str) -> str:
        """Build summary message"""
        if result.get("error"):
            return f"Error checking network: {result['error']}"

        if result.get("relationship_exists"):
            return f"Network relationship found: {carrier} <-> {shipper}"
        else:
            return f"No network relationship: {carrier} <-> {shipper}"

"""
Ocean Events Trace Agent
Queries DataHub for ocean tracking subscription details and update history
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, TransportMode, AgentDiscussion, AgentMessage, AgentStatus
from app.services.super_api_client import SuperAPIClient


class OceanTraceAgent(BaseAgent):
    """
    Collects ocean tracking subscription details from DataHub with verbose output.

    Role: Subscription Tracker
    I trace ocean subscriptions and verify carrier data flow.
    """

    def __init__(self):
        super().__init__("Ocean Trace Agent")
        self.client = SuperAPIClient()

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
        Query DataHub for ocean subscription details and update history
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        transport_mode = state.get("transport_mode", TransportMode.UNKNOWN)
        tracking_data = state.get("tracking_data", {})
        super_api_data = state.get("super_api_data", {})

        # Check if load is ocean
        actual_mode = (tracking_data.get("mode") or "").lower()
        is_ocean = any(keyword in actual_mode for keyword in ["ocean", "intermodal", "multimodal"])

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking if this load needs ocean trace analysis.\n" +
                    f"  • Transport mode: {transport_mode}\n" +
                    f"  • Actual mode: {actual_mode or 'unknown'}\n" +
                    f"  • Super API data available: {bool(super_api_data)}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not is_ocean and transport_mode not in [TransportMode.OCEAN]:
            think = AgentDiscussion(
                agent=self.name,
                message=f"[Thinking] This is not an ocean load (mode: {actual_mode}). Ocean Trace is only relevant for ocean/intermodal shipments.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "ocean_trace_data": {"skipped": True, "reason": f"Not an ocean load (mode: {actual_mode})"},
                "_message": f"Skipped Ocean Trace: mode is {actual_mode}"
            }

        # Get subscription_id from super_api_data
        subscription_id = super_api_data.get("subscription_id")

        if not subscription_id:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No subscription_id available from Super API. Cannot query subscription details without it.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "ocean_trace_data": {"skipped": True, "reason": "No subscription_id from Super API"},
                "_message": "Skipped Ocean Trace: no subscription_id"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message=f"[Plan] Will query DataHub for subscription details:\n" +
                    f"  • Subscription ID: {subscription_id}\n" +
                    f"  • Looking for: update history, success/rejection counts\n" +
                    f"  • Will check if subscription is active and receiving data",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] GET /v1/subscriptions/{subscription_id}",
            status=AgentStatus.RUNNING,
            metadata={"type": "api_call", "endpoint": "datahub"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Get subscription details from DataHub
            subscription_details = await self.client.get_subscription_details(subscription_id)

            duration_ms = int((time.time() - start_time) * 1000)

            # Check for errors
            if subscription_details.get("error"):
                error_disc = AgentDiscussion(
                    agent=self.name,
                    message=f"[Finding] Error fetching subscription details.\n" +
                            f"  • Error: {subscription_details['error']}\n" +
                            "  • The subscription may not exist or DataHub is unavailable",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(error_disc)

                return {
                    **updates,
                    "ocean_trace_data": subscription_details,
                    "_message": f"Ocean Trace error: {subscription_details['error']}"
                }

            # Extract update history
            updates_list = subscription_details.get("updates", [])
            update_count = len(updates_list)

            # Count successful vs rejected
            successful = sum(1 for u in updates_list if u.get("status") == "success")
            rejected = update_count - successful

            query_log = self.log_query(
                state,
                "DataHub (Ocean Trace)",
                f"GET /v1/subscriptions/{subscription_id}",
                result_count=update_count,
                raw_result={"updates": updates_list[:10]},  # First 10 for summary
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            if update_count > 0:
                if rejected > 0:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Subscription updates have issues!\n" +
                                f"  • Total updates: {update_count}\n" +
                                f"  • Successful: {successful}\n" +
                                f"  • Rejected: {rejected}\n\n" +
                                f"Rejected updates may indicate data quality issues.",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Subscription updates are healthy!\n" +
                                f"  • Total updates: {update_count}\n" +
                                f"  • All updates successful\n" +
                                "  • Data flow appears to be working correctly",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                updates["agent_discussions"].append(finding)
                message = f"Found {update_count} subscription updates: {successful} successful, {rejected} rejected"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No subscription updates found.\n" +
                            "  • This could mean no data has been received\n" +
                            "  • Or the subscription is new/inactive",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No subscription updates found"

            result = {
                "subscription_id": subscription_id,
                "total_updates": update_count,
                "successful": successful,
                "rejected": rejected,
                "updates": updates_list,
                "subscription_details": subscription_details
            }

            return {
                **updates,
                "ocean_trace_data": result,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Ocean trace query error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query ocean trace: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "ocean_trace_data": {"error": str(e)},
                "_message": f"Ocean Trace error: {str(e)}"
            }

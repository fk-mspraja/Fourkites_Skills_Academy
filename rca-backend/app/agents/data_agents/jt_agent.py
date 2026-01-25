"""
Just Transform (JT) Data Collection Agent
Fetches RPA scraping history from carrier portals for Ocean tracking
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, TransportMode, AgentDiscussion, AgentMessage, AgentStatus
from app.services.jt_client import JTClient


class JTAgent(BaseAgent):
    """
    Collects data from Just Transform RPA system with verbose output.

    Role: RPA Scraping Analyst
    I investigate the RPA scraping pipeline to find extraction issues.
    """

    def __init__(self):
        super().__init__("JT Agent")
        self.client = JTClient()

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
        Fetch JT scraping history with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        # Check transport mode
        mode = state.get("transport_mode", TransportMode.UNKNOWN)
        tracking_data = state.get("tracking_data", {})
        actual_mode = (tracking_data.get("mode") or "").lower()

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking if this load needs JT investigation.\n" +
                    f"  • Transport mode: {mode}\n" +
                    f"  • Actual mode from tracking: {actual_mode or 'unknown'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        # Only run for Ocean mode
        is_ocean = any(keyword in actual_mode for keyword in ["ocean", "intermodal", "multimodal"])
        if mode != TransportMode.OCEAN and not is_ocean:
            think = AgentDiscussion(
                agent=self.name,
                message=f"[Thinking] This is not an ocean/intermodal load (mode={actual_mode or mode}). JT is only used for ocean carrier portal scraping.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "jt_data": {"skipped": True, "reason": f"Not ocean mode (mode={actual_mode or mode})"},
                "_message": f"Skipped JT (mode={actual_mode or mode})"
            }

        # Need subscription_id from Super API or container number
        super_api_data = state.get("super_api_data", {})
        subscription_id = super_api_data.get("subscription_id")
        container = self.extract_identifier(state, "container")

        # Observation about identifiers
        id_obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Looking for JT identifiers.\n" +
                    f"  • subscription_id: {subscription_id or 'not available'}\n" +
                    f"  • container: {container or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(id_obs)

        if not subscription_id and not container:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No subscription_id or container number available. Cannot query JT without these identifiers.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "jt_data": {"skipped": True, "reason": "No subscription_id or container"},
                "_message": "No subscription_id or container for JT lookup"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query Just Transform to check:\n" +
                    "  • RPA scraping history from carrier portal\n" +
                    "  • Successful vs failed scraping attempts\n" +
                    "  • Data extraction errors or formatting issues\n" +
                    "  • Last successful scrape timestamp",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        try:
            if subscription_id:
                # Executing action
                action_msg = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /api/v1/ocean/subscriptions/{subscription_id}/history?days=7",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "just_transform"}
                )
                updates["agent_messages"].append(action_msg)

                result = await self.client.get_subscription_history(subscription_id, days=7)
                duration_ms = int((time.time() - start_time) * 1000)

                query_log = self.log_query(
                    state,
                    "Just Transform",
                    f"GET /api/v1/ocean/subscriptions/{subscription_id}/history?days=7",
                    result_count=result.get("events_count", 0),
                    raw_result=result,
                    duration_ms=duration_ms
                )
                self._merge_updates(updates, query_log)

                # Report findings
                events_count = result.get("events_count", 0)
                error_count = result.get("error_count", 0)
                last_scrape = result.get("last_successful_scrape", "unknown")

                if events_count > 0:
                    if error_count > 0:
                        finding = AgentDiscussion(
                            agent=self.name,
                            message=f"[Finding] JT scraping issues detected!\n" +
                                    f"  • Total events: {events_count}\n" +
                                    f"  • Errors: {error_count}\n" +
                                    f"  • Last successful scrape: {last_scrape}\n\n" +
                                    f"This suggests carrier portal scraping problems.",
                            message_type="observation",
                            timestamp=datetime.now()
                        )
                    else:
                        finding = AgentDiscussion(
                            agent=self.name,
                            message=f"[Finding] JT scraping working normally.\n" +
                                    f"  • Total events: {events_count}\n" +
                                    f"  • No errors found\n" +
                                    f"  • Last scrape: {last_scrape}",
                            message_type="observation",
                            timestamp=datetime.now()
                        )
                    updates["agent_discussions"].append(finding)
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message="[Finding] No JT scraping events found.\n" +
                                "  • Subscription may not be active\n" +
                                "  • Or carrier is not configured for portal scraping",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)

                message = self._build_message(result)

                return {
                    **updates,
                    "jt_data": result,
                    "_message": message
                }

            elif container:
                # Executing action for container lookup
                action_msg = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /api/v1/ocean/containers/{container}/events?days=14",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "just_transform"}
                )
                updates["agent_messages"].append(action_msg)

                result = await self.client.get_container_events(container, days=14)
                duration_ms = int((time.time() - start_time) * 1000)

                query_log = self.log_query(
                    state,
                    "Just Transform",
                    f"GET /api/v1/ocean/containers/{container}/events?days=14",
                    result_count=len(result.get("events", [])),
                    raw_result=result,
                    duration_ms=duration_ms
                )
                self._merge_updates(updates, query_log)

                if result.get("has_data"):
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Container events found in JT.\n" +
                                f"  • Container: {container}\n" +
                                f"  • Events: {len(result.get('events', []))}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Container NOT found in JT.\n" +
                                f"  • Container: {container}\n" +
                                f"  • This container may not be tracked via JT",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                updates["agent_discussions"].append(finding)

                message = f"Container {'found' if result.get('has_data') else 'not found'} in JT"

                return {
                    **updates,
                    "jt_data": result,
                    "_message": message
                }

        except Exception as e:
            self.logger.error(f"JT API error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query Just Transform: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "jt_data": {"error": str(e), "has_errors": True},
                "_message": f"JT error: {str(e)}"
            }

    def _build_message(self, result: Dict[str, Any]) -> str:
        """Build summary message from JT result"""
        if result.get("error"):
            return f"JT error: {result['error']}"

        if not result.get("events_count"):
            return "No JT scraping events found"

        error_count = result.get("error_count", 0)
        last_scrape = result.get("last_successful_scrape", "unknown")

        if error_count > 0:
            return f"Found {result['events_count']} events, {error_count} errors. Last success: {last_scrape}"
        else:
            return f"Found {result['events_count']} scraping events, no errors. Last: {last_scrape}"

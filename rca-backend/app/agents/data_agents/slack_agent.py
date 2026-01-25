"""
Slack History Agent
Searches for past similar issues and resolutions in support channels
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any, List
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.slack_client import SlackClient


class SlackAgent(BaseAgent):
    """
    Searches Slack for past similar issues with verbose output.

    Role: Communication Analyst
    I look through team communications for similar issues and resolutions.
    """

    def __init__(self):
        super().__init__("Slack Agent")
        self.client = SlackClient()

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
        Search Slack for past similar issues and resolutions
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message="[Observation] Preparing to search Slack for similar past issues.\n" +
                    "  • Will check support channels for similar discussions\n" +
                    "  • Looking for resolved issues with check mark reactions",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        # Build search query from investigation context
        search_query = self._build_search_query(state)

        if not search_query:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No meaningful search query could be built. Need error context or identifiers.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "slack_data": {"skipped": True, "reason": "No search query"},
                "_message": "Skipped Slack: no search context"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message=f"[Plan] Will search Slack for:\n" +
                    f"  • Query: '{search_query[:80]}...'\n" +
                    f"  • Channels: support-related channels\n" +
                    f"  • Looking for: resolved issues, workarounds, escalations",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] Slack Search: {search_query[:100]}",
            status=AgentStatus.RUNNING,
            metadata={"type": "search", "source": "slack"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Search for similar issues in support channels
            service_name = self._get_service_name(state)
            results = await self.client.search_similar_issues(
                issue_description=search_query,
                service_name=service_name
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Log the query
            query_log = self.log_query(
                state,
                "Slack",
                f"Search: {search_query[:100]}",
                result_count=len(results),
                raw_result=results[:5],  # Limit stored results
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            slack_data = {
                "found": len(results) > 0,
                "count": len(results),
                "threads": results[:10],  # Top 10 results
                "search_query": search_query
            }

            if results:
                # Check for potentially resolved issues (those with check mark reactions)
                resolved_count = sum(1 for r in results if any(
                    rx.get("name") in ["white_check_mark", "heavy_check_mark", "check"]
                    for rx in r.get("reactions", [])
                ))

                # Report findings
                finding = AgentDiscussion(
                    agent=self.name,
                    message=f"[Finding] Found {len(results)} similar discussions in Slack!\n" +
                            f"  • Potentially resolved: {resolved_count}\n" +
                            f"  • Recent threads may contain workarounds\n" +
                            f"  • Check for related escalations",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = f"Found {len(results)} similar discussions ({resolved_count} resolved)"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No similar issues found in Slack history.\n" +
                            "  • This may be a new/unique issue\n" +
                            "  • Consider checking broader channels or date ranges",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No similar issues found in Slack history"

            return {
                **updates,
                "slack_data": slack_data,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Slack search error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to search Slack: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "slack_data": {"error": str(e)},
                "_message": f"Slack error: {str(e)}"
            }

    def _build_search_query(self, state: InvestigationState) -> str:
        """Build search query from investigation context"""
        parts = []

        # Use error message if available
        redshift_data = state.get("redshift_data", {})
        latest_error = redshift_data.get("latest_error", "")
        if latest_error:
            # Take key part of error
            error_key = latest_error[:80].split("[")[0].strip()
            if error_key:
                parts.append(error_key)

        # Use transport mode
        transport_mode = state.get("transport_mode")
        if transport_mode and transport_mode != "unknown":
            parts.append(transport_mode)

        # Use tracking ID if nothing else
        if not parts:
            tracking_id = self.extract_identifier(state, "tracking_id")
            if tracking_id:
                parts.append(tracking_id)

        # Fall back to issue text keywords
        if not parts:
            issue_text = state.get("issue_text", "")
            words = [w for w in issue_text.split() if len(w) > 4][:5]
            parts.extend(words)

        return " ".join(parts)

    def _get_service_name(self, state: InvestigationState) -> str:
        """Get service name from transport mode"""
        transport_mode = state.get("transport_mode", "")
        mode_map = {
            "ocean": "ocean tracking",
            "otr": "truckload",
            "ltl": "ltl",
            "air": "air freight",
            "rail": "rail",
            "parcel": "parcel"
        }
        return mode_map.get(transport_mode.lower(), "")

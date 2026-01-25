"""
Callbacks Data Collection Agent
Queries webhook/callback history from Athena
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
import asyncio
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus


class CallbacksAgent(BaseAgent):
    """
    Collects callback/webhook history from Athena with verbose output.

    Role: Integration Specialist
    I analyze callback delivery and look for integration issues with external systems.
    """

    def __init__(self):
        super().__init__("Callbacks Agent")
        # Lazy import to handle missing credentials gracefully
        self.client = None

    def _get_client(self):
        if self.client is None:
            from app.services.athena_client import AthenaClient
            self.client = AthenaClient()
        return self.client

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
        Query callback history from Athena with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        load_number = self.extract_identifier(state, "load_number")

        # Try to get load_number from tracking_data if not available
        tracking_data = state.get("tracking_data", {})
        if not load_number and tracking_data.get("loadNumber"):
            load_number = tracking_data.get("loadNumber")

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking callback delivery history.\n" +
                    f"  • tracking_id: {tracking_id or 'not available'}\n" +
                    f"  • load_number: {load_number or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not tracking_id and not load_number:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No tracking_id available. Cannot query Athena callbacks without identifier.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "callbacks_data": {"skipped": True, "reason": "No tracking_id"},
                "_message": "Skipped callbacks: no tracking_id"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query Athena callbacks_v2 table to check:\n" +
                    "  • If callbacks were sent for this load\n" +
                    "  • HTTP response codes (2xx = success, 4xx/5xx = failures)\n" +
                    "  • Error messages on failed deliveries\n" +
                    "  • Destination URLs and delivery timestamps",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Build query - callbacks_v2 uses fk_tracking_id column
        query = f"""
        SELECT
            uuid,
            ts,
            fk_tracking_id,
            config_id,
            load_number,
            company_id,
            ext_url,
            ext_request_status,
            message_type,
            error_msg
        FROM raw_data_db.callbacks_v2
        WHERE fk_tracking_id = '{tracking_id}'
        ORDER BY ts DESC
        LIMIT 200
        """

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] SELECT * FROM raw_data_db.callbacks_v2 WHERE fk_tracking_id={tracking_id}",
            status=AgentStatus.RUNNING,
            metadata={"type": "sql_query", "database": "athena"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Execute query with timeout
            try:
                callbacks = await asyncio.wait_for(
                    asyncio.to_thread(self._get_client().execute, query),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Callbacks query timed out after 15 seconds")

                timeout_disc = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Query timed out after 15 seconds.\n" +
                            "  • Athena queries can be slow for large datasets\n" +
                            "  • Consider narrowing the date range\n" +
                            "  • Recommendation: Try again or check AWS status",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(timeout_disc)

                return {
                    **updates,
                    "callbacks_data": {"timeout": True, "reason": "Athena query timed out"},
                    "_message": "Callbacks query timed out (Athena slow)"
                }

            duration_ms = int((time.time() - start_time) * 1000)

            # Check for errors
            if not callbacks or (isinstance(callbacks, dict) and callbacks.get("error")):
                error_disc = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Query failed or returned no data.\n" +
                            "  • This could indicate a connection issue\n" +
                            "  • Or the tracking_id doesn't exist in callbacks",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(error_disc)

                return {
                    **updates,
                    "callbacks_data": {"error": "Query failed or no data"},
                    "_message": "Callbacks query failed"
                }

            total_count = len(callbacks)

            # Count successful vs failed
            success_count = sum(1 for cb in callbacks if cb.get("http_response_code") and str(cb["http_response_code"]).startswith("2"))
            failed_count = total_count - success_count

            # Get unique destinations
            destinations = list(set(cb.get("destination_url", "unknown") for cb in callbacks))

            # Get error messages
            error_messages = list(set(cb.get("error_message") for cb in callbacks if cb.get("error_message")))

            # Build query description
            query_desc = f"SELECT * FROM raw_data_db.callbacks_v2 WHERE tracking_id={tracking_id}"

            query_log = self.log_query(
                state,
                "Athena (Callbacks)",
                query_desc,
                result_count=total_count,
                raw_result={"callbacks": callbacks[:10]},  # Only first 10 for summary
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            if total_count > 0:
                if failed_count > 0:
                    # Found callback failures - this is important!
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Callback delivery issues detected!\n" +
                                f"  • Total callbacks: {total_count}\n" +
                                f"  • Successful (2xx): {success_count}\n" +
                                f"  • Failed: {failed_count}\n" +
                                f"  • Destinations: {len(destinations)}\n" +
                                (f"  • Errors: {', '.join(error_messages[:3])}\n" if error_messages else "") +
                                f"\nThis suggests webhook integration issues.",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Found {total_count} callbacks: {success_count} successful, {failed_count} failed"
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] All callbacks delivered successfully!\n" +
                                f"  • Total callbacks: {total_count}\n" +
                                f"  • All returned 2xx status\n" +
                                f"  • Destinations: {len(destinations)}\n\n" +
                                f"Webhook delivery is working correctly.",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Found {total_count} callbacks: all successful"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No callbacks found in Athena.\n" +
                            "  • This could mean no webhooks are configured\n" +
                            "  • Or callbacks haven't been triggered yet\n" +
                            "  • Or the data has been archived (90-day retention)",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No callbacks found in Athena"

            result = {
                "total_callbacks": total_count,
                "successful": success_count,
                "failed": failed_count,
                "callbacks": callbacks,
                "summary": {
                    "total": total_count,
                    "success": success_count,
                    "failed": failed_count,
                    "destinations": destinations[:5],
                    "errors": error_messages[:5]
                }
            }

            return {
                **updates,
                "callbacks_data": result,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Callbacks query error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query callbacks: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "callbacks_data": {"error": str(e)},
                "_message": f"Callbacks error: {str(e)}"
            }

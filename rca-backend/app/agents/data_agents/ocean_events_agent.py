"""
Ocean Events Data Collection Agent
Queries ClickHouse for MMCUW (Multimodal Carrier Updates Worker) logs
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
import asyncio
from datetime import datetime, timedelta

from app.agents.base import BaseAgent
from app.models import InvestigationState, TransportMode, AgentDiscussion, AgentMessage, AgentStatus
from app.services.clickhouse_client import ClickHouseClient


class OceanEventsAgent(BaseAgent):
    """
    Collects ocean tracking events from ClickHouse MMCUW logs with verbose output.

    Role: Ocean Logistics Specialist
    I analyze ocean-specific events and container milestones.
    """

    def __init__(self):
        super().__init__("Ocean Events Agent")
        self.client = ClickHouseClient()

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
        Query ClickHouse for ocean tracking events
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        transport_mode = state.get("transport_mode", TransportMode.UNKNOWN)
        tracking_data = state.get("tracking_data", {})

        # Check if load is ocean/multimodal/intermodal
        actual_mode = (tracking_data.get("mode") or "").lower()
        is_ocean = any(keyword in actual_mode for keyword in ["ocean", "intermodal", "multimodal"])

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking if this load requires ocean event analysis.\n" +
                    f"  • Transport mode: {transport_mode}\n" +
                    f"  • Actual mode: {actual_mode or 'unknown'}\n" +
                    f"  • tracking_id: {tracking_id or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not is_ocean and transport_mode not in [TransportMode.OCEAN]:
            think = AgentDiscussion(
                agent=self.name,
                message=f"[Thinking] This is not an ocean load (mode: {actual_mode}). MMCUW logs are only relevant for ocean/intermodal shipments.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "ocean_events_data": {"skipped": True, "reason": f"Not an ocean load (mode: {actual_mode})"},
                "_message": f"Skipped Ocean Events: mode is {actual_mode}"
            }

        if not tracking_id:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No tracking_id available. Cannot query MMCUW logs without identifier.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "ocean_events_data": {"skipped": True, "reason": "No tracking_id"},
                "_message": "Skipped Ocean Events: no tracking_id"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query ClickHouse (SigNoz) for MMCUW logs:\n" +
                    "  • Service: mmcuw (Multimodal Carrier Updates Worker)\n" +
                    "  • Looking for: container milestones, tracking updates\n" +
                    "  • Time range: last 3 days from last update",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        try:
            # Get date range from tracking data (3 days from updated_at)
            updated_at = tracking_data.get("raw", {}).get("updatedAt")
            if updated_at:
                try:
                    end_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except:
                    end_date = datetime.now()
            else:
                end_date = datetime.now()

            start_date = end_date - timedelta(days=3)

            # Format dates for ClickHouse
            start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

            # Query ClickHouse for ocean events
            query = f"""
            SELECT
                timestamp,
                correlation_id,
                body
            FROM signoz_logs.logs
            WHERE serviceName = 'mmcuw'
              AND body LIKE '%{tracking_id}%'
              AND timestamp >= toDateTime('{start_str}')
              AND timestamp <= toDateTime('{end_str}')
            ORDER BY timestamp DESC
            LIMIT 100
            """

            # Executing action
            action_msg = AgentMessage(
                agent=self.name,
                message=f"[Executing] SELECT * FROM signoz_logs.logs WHERE serviceName='mmcuw' AND tracking_id={tracking_id}",
                status=AgentStatus.RUNNING,
                metadata={"type": "sql_query", "database": "clickhouse"}
            )
            updates["agent_messages"].append(action_msg)

            # Execute query with timeout
            try:
                events = await asyncio.wait_for(
                    asyncio.to_thread(self.client.execute_query, query),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Ocean events query timed out after 10 seconds")

                timeout_disc = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Query timed out after 10 seconds.\n" +
                            "  • ClickHouse may be under heavy load\n" +
                            "  • Check VPN connectivity\n" +
                            "  • Try narrowing the date range",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(timeout_disc)

                return {
                    **updates,
                    "ocean_events_data": {"timeout": True, "reason": "ClickHouse query timed out"},
                    "_message": "Ocean Events query timed out"
                }

            duration_ms = int((time.time() - start_time) * 1000)

            # Check for errors
            if not events or (isinstance(events, dict) and events.get("error")):
                error_disc = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Query returned no data or failed.\n" +
                            "  • No MMCUW logs found for this tracking_id\n" +
                            "  • Data may be outside the 30-day retention window",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(error_disc)

                return {
                    **updates,
                    "ocean_events_data": {"error": "Query failed or no data"},
                    "_message": "Ocean Events query failed"
                }

            event_count = len(events) if isinstance(events, list) else 0

            query_log = self.log_query(
                state,
                "ClickHouse (Ocean Events)",
                f"SELECT * FROM signoz_logs.logs WHERE serviceName='mmcuw' AND tracking_id={tracking_id}",
                result_count=event_count,
                raw_result={"events": events[:10]},  # Only first 10 for summary
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            if event_count > 0:
                finding = AgentDiscussion(
                    agent=self.name,
                    message=f"[Finding] Found {event_count} ocean tracking events!\n" +
                            f"  • Date range: {start_str} to {end_str}\n" +
                            f"  • These logs show carrier update processing\n" +
                            f"  • Check for error patterns or missed updates",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = f"Found {event_count} ocean tracking events in last 3 days"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No ocean events found in ClickHouse.\n" +
                            f"  • Date range checked: {start_str} to {end_str}\n" +
                            "  • This could indicate no updates were processed\n" +
                            "  • Or data is outside 30-day retention",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No ocean events found in ClickHouse"

            result = {
                "total_events": event_count,
                "events": events,
                "date_range": {
                    "start": start_str,
                    "end": end_str
                }
            }

            return {
                **updates,
                "ocean_events_data": result,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Ocean events query error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query ocean events: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "ocean_events_data": {"error": str(e)},
                "_message": f"Ocean Events error: {str(e)}"
            }

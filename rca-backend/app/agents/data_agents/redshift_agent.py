"""
Redshift Data Collection Agent
Queries load validation errors and historical data from Data Warehouse
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
import asyncio
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.redshift_client import RedshiftClient


class RedshiftAgent(BaseAgent):
    """
    Collects data from Redshift Data Warehouse with verbose output.

    Role: Data Warehouse Analyst
    I dig into the data warehouse to find historical patterns and validation issues.
    """

    def __init__(self):
        super().__init__("Redshift Agent")
        self.client = RedshiftClient()

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
        Query Redshift for load validation errors and metadata with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        load_number = self.extract_identifier(state, "load_number")

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking Redshift DWH for validation history.\n" +
                    f"  • tracking_id: {tracking_id or 'not available'}\n" +
                    f"  • load_number: {load_number or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not tracking_id and not load_number:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No identifiers available. Cannot query Redshift without tracking_id or load_number.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "redshift_data": {"skipped": True, "reason": "No identifiers"},
                "_message": "Skipped Redshift: no identifiers"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query load_validation_data_mart to check:\n" +
                    "  • If load creation was attempted\n" +
                    "  • How many validation attempts occurred\n" +
                    "  • What errors (if any) caused failures\n" +
                    "  • Historical pattern of this load",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Build query description
        if tracking_id and load_number:
            query_desc = f"SELECT * FROM hadoop.load_validation_data_mart WHERE load_id={tracking_id} OR load_number='{load_number}'"
        elif tracking_id:
            query_desc = f"SELECT * FROM hadoop.load_validation_data_mart WHERE load_id={tracking_id}"
        else:
            query_desc = f"SELECT * FROM hadoop.load_validation_data_mart WHERE load_number='{load_number}'"

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] {query_desc}",
            status=AgentStatus.RUNNING,
            metadata={"type": "sql_query", "database": "redshift"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Query with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.get_load_validation_errors,
                        load_number=load_number,
                        tracking_id=tracking_id
                    ),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Redshift query timed out after 10 seconds")

                timeout_disc = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Query timed out after 10 seconds.\n" +
                            "  • This usually indicates VPN connectivity issues\n" +
                            "  • Or the database is under heavy load\n" +
                            "  • Recommendation: Try again or check VPN connection",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(timeout_disc)

                return {
                    **updates,
                    "redshift_data": {"timeout": True, "reason": "Query timed out"},
                    "_message": "Redshift query timed out (VPN required)"
                }

            duration_ms = int((time.time() - start_time) * 1000)

            # Check for errors
            if result.get("error"):
                error_disc = AgentDiscussion(
                    agent=self.name,
                    message=f"[Error] Database query failed: {result['error']}",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(error_disc)

                return {
                    **updates,
                    "redshift_data": result,
                    "_message": f"Redshift error: {result['error']}"
                }

            # Log the query
            query_log = self.log_query(
                state,
                "Redshift",
                query_desc,
                result_count=result.get("total_attempts", 0),
                raw_result=result,
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            # Analyze results
            total = result.get("total_attempts", 0)
            failed = result.get("failed_attempts", 0)
            latest_error = result.get("latest_error")
            attempts = result.get("validation_attempts", [])

            if total > 0:
                if failed > 0:
                    # Found validation errors - this is important!
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Validation errors detected!\n" +
                                f"  • Total attempts: {total}\n" +
                                f"  • Failed: {failed}\n" +
                                f"  • Success: {total - failed}\n" +
                                f"  • Latest error: {latest_error or 'N/A'}\n\n" +
                                f"This suggests load creation was attempted but failed validation.",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Found {total} validation attempts: {failed} failed, {total - failed} succeeded"
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] All validation attempts succeeded!\n" +
                                f"  • Total attempts: {total}\n" +
                                f"  • All passed validation\n\n" +
                                f"The load was created successfully. Issue is likely not load creation.",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Found {total} validation attempts: all succeeded"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No validation records found in Redshift.\n" +
                            "  • This could mean the load was never submitted for creation\n" +
                            "  • Or it's too old and data was purged\n" +
                            "  • Or the identifiers don't match any records",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No validation records found in Redshift"

            return {
                **updates,
                "redshift_data": result,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Redshift query error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query Redshift: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "redshift_data": {"error": str(e)},
                "_message": f"Redshift error: {str(e)}"
            }

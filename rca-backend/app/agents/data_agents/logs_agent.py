"""
Logs Data Collection Agent
Queries SigNoz ClickHouse for service logs (integrations-worker, carrier-files-worker, tracking-service)
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus


class LogsAgent(BaseAgent):
    """
    Collects service logs from SigNoz ClickHouse with verbose output.

    Role: System Logs Analyst
    I search service logs for errors, warnings, and processing issues.

    Key Services:
    - integrations-worker: Load file processing
    - carrier-files-worker: Carrier file processing (CFW → GWEX → LW)
    - tracking-service: API calls for load creation
    """

    # Key services to query for RCA
    KEY_SERVICES = [
        "integrations-worker",
        "carrier-files-worker",
        "tracking-service",
        "ocean-datahub",
        "mmcuw",  # Multimodal Carrier Updates Worker
    ]

    def __init__(self):
        super().__init__("Logs Agent")
        # Lazy import to handle missing credentials gracefully
        self.client = None

    def _get_client(self):
        if self.client is None:
            from app.services.clickhouse_client import ClickHouseClient
            self.client = ClickHouseClient()
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
        Query SigNoz ClickHouse for service logs
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        # Get identifiers to search for
        tracking_id = self.extract_identifier(state, "tracking_id")
        load_number = self.extract_identifier(state, "load_number")
        tracking_data = state.get("tracking_data", {})

        # Also get load_number from tracking_data if available
        if not load_number and tracking_data.get("loadNumber"):
            load_number = tracking_data.get("loadNumber")

        # Build search terms
        search_terms = []
        if tracking_id:
            search_terms.append(str(tracking_id))
        if load_number:
            search_terms.append(str(load_number))

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Searching service logs for errors and warnings.\n" +
                    f"  • Search terms: {', '.join(search_terms) if search_terms else 'none'}\n" +
                    f"  • Target services: {', '.join(self.KEY_SERVICES[:3])}...\n" +
                    f"  • Looking for: ERROR, WARN level logs",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not search_terms:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No tracking_id or load_number available. Cannot search logs without identifier.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "logs_data": {"skipped": True, "reason": "No identifiers to search"},
                "_message": "Skipped Logs Agent: no identifiers"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query SigNoz ClickHouse for:\n" +
                    "  • integrations-worker: Load file processing errors\n" +
                    "  • carrier-files-worker: Carrier file processing errors\n" +
                    "  • tracking-service: API call errors\n" +
                    "  • Time range: last 7 days",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()
        all_logs: List[Dict] = []
        errors_by_service: Dict[str, List[Dict]] = {}
        query_count = 0

        # Starting message
        start_msg = AgentMessage(
            agent=self.name,
            message="[Searching] Querying logs across services...",
            status=AgentStatus.RUNNING,
            metadata={"type": "start"}
        )
        updates["agent_messages"].append(start_msg)

        try:
            client = self._get_client()

            # Calculate time range (last 7 days)
            end_time = datetime.utcnow()
            start_time_query = end_time - timedelta(days=7)
            start_ts = int(start_time_query.timestamp() * 1e9)  # nanoseconds
            end_ts = int(end_time.timestamp() * 1e9)

            # Build search pattern for WHERE clause
            search_pattern = " OR ".join([f"body LIKE '%{term}%'" for term in search_terms])

            # Query each key service
            for service in self.KEY_SERVICES:
                query = f"""
                SELECT
                    timestamp,
                    severity_text,
                    body,
                    service_name,
                    trace_id
                FROM signoz_logs.distributed_logs
                WHERE service_name = '{service}'
                  AND timestamp >= {start_ts}
                  AND timestamp <= {end_ts}
                  AND severity_text IN ('ERROR', 'WARN', 'error', 'warn', 'Error', 'Warning')
                  AND ({search_pattern})
                ORDER BY timestamp DESC
                LIMIT 20
                """

                try:
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        asyncio.to_thread(client.execute, query),
                        timeout=10.0
                    )

                    query_count += 1

                    if result and len(result) > 0:
                        errors_by_service[service] = result
                        all_logs.extend(result)

                        # Log the query
                        query_desc = f"SELECT * FROM signoz_logs WHERE service_name='{service}' AND severity IN (ERROR,WARN)"
                        query_log = self.log_query(
                            state,
                            f"SigNoz ({service})",
                            query_desc,
                            result_count=len(result),
                            raw_result={"logs": result[:5]},  # First 5 for summary
                            duration_ms=int((time.time() - start_time) * 1000)
                        )
                        self._merge_updates(updates, query_log)

                except asyncio.TimeoutError:
                    self.logger.warning(f"Query for {service} timed out")
                    continue
                except Exception as e:
                    self.logger.warning(f"Query for {service} failed: {e}")
                    continue

            duration_ms = int((time.time() - start_time) * 1000)

            # Analyze findings
            total_errors = len(all_logs)
            services_with_errors = list(errors_by_service.keys())

            if total_errors > 0:
                # Build finding message
                finding_parts = [f"[Finding] Found {total_errors} error/warning logs across {len(services_with_errors)} services!"]

                for service, logs in errors_by_service.items():
                    error_count = len([l for l in logs if l.get("severity_text", "").upper() == "ERROR"])
                    warn_count = len(logs) - error_count
                    finding_parts.append(f"  • {service}: {error_count} errors, {warn_count} warnings")

                    # Sample error messages
                    for log in logs[:2]:
                        body = log.get("body", "")
                        if len(body) > 100:
                            body = body[:100] + "..."
                        finding_parts.append(f"    → {body}")

                finding = AgentDiscussion(
                    agent=self.name,
                    message="\n".join(finding_parts),
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = f"Found {total_errors} errors across {len(services_with_errors)} services"

            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No errors or warnings found in recent logs.\n" +
                            f"  • Queried {query_count} services\n" +
                            f"  • Time range: last 7 days\n" +
                            "  • This could indicate the issue is not recent or logs have rotated",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No errors found in service logs"

            # Completion message
            complete_msg = AgentMessage(
                agent=self.name,
                message=f"[Complete] Logs search finished ({duration_ms}ms)",
                status=AgentStatus.COMPLETED,
                metadata={"type": "complete", "duration_ms": duration_ms}
            )
            updates["agent_messages"].append(complete_msg)

            # Categorize errors by type for hypothesis formation
            error_patterns = self._categorize_errors(all_logs)

            result = {
                "total_logs": total_errors,
                "services_queried": query_count,
                "services_with_errors": services_with_errors,
                "errors_by_service": {k: len(v) for k, v in errors_by_service.items()},
                "error_patterns": error_patterns,
                "logs": all_logs[:50],  # Limit to 50 for response size
                "summary": {
                    "total": total_errors,
                    "services": len(services_with_errors),
                    "patterns": error_patterns
                }
            }

            return {
                **updates,
                "logs_data": result,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Logs query error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query logs: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "logs_data": {"error": str(e)},
                "_message": f"Logs error: {str(e)}"
            }

    def _categorize_errors(self, logs: List[Dict]) -> Dict[str, int]:
        """Categorize errors by common patterns"""
        patterns = {
            "validation_error": 0,
            "connection_error": 0,
            "timeout_error": 0,
            "parsing_error": 0,
            "authentication_error": 0,
            "not_found_error": 0,
            "other_error": 0
        }

        for log in logs:
            body = (log.get("body") or "").lower()

            if any(kw in body for kw in ["validation", "invalid", "required field", "missing"]):
                patterns["validation_error"] += 1
            elif any(kw in body for kw in ["connection", "connect", "refused", "unreachable"]):
                patterns["connection_error"] += 1
            elif any(kw in body for kw in ["timeout", "timed out", "deadline"]):
                patterns["timeout_error"] += 1
            elif any(kw in body for kw in ["parse", "json", "format", "decode"]):
                patterns["parsing_error"] += 1
            elif any(kw in body for kw in ["auth", "unauthorized", "forbidden", "401", "403"]):
                patterns["authentication_error"] += 1
            elif any(kw in body for kw in ["not found", "404", "does not exist"]):
                patterns["not_found_error"] += 1
            else:
                patterns["other_error"] += 1

        # Remove zero counts
        return {k: v for k, v in patterns.items() if v > 0}

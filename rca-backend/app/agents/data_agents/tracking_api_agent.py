"""
Tracking API Data Collection Agent
Fetches customer-facing load view from FourKites Tracking API
With Claude Code-style verbose output showing observations, thinking, and actions
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.tracking_api_client import TrackingAPIClient


class TrackingAPIAgent(BaseAgent):
    """
    Collects data from Tracking API with verbose output.

    Role: Customer Data Specialist
    I focus on what the customer sees - the load's current state, status, and tracking information.
    """

    def __init__(self):
        super().__init__("Tracking API Agent")
        self.client = TrackingAPIClient()

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
        Fetch load metadata from Tracking API with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        load_number = self.extract_identifier(state, "load_number")

        # Observation: What identifiers do we have?
        if tracking_id:
            obs = AgentDiscussion(
                agent=self.name,
                message=f"[Observation] Found tracking_id={tracking_id} in state. This is a FourKites internal ID.",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(obs)

        if load_number:
            obs = AgentDiscussion(
                agent=self.name,
                message=f"[Observation] Found load_number={load_number} in state. This is the customer's reference number.",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(obs)

        if not tracking_id and not load_number:
            # No identifiers - report and return
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No tracking_id or load_number provided. Cannot query Tracking API without identifiers.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "tracking_data": {"exists": False, "error": "No tracking_id or load_number provided"},
                "_message": "No identifiers to query Tracking API"
            }

        # Plan: What are we going to do?
        plan = AgentDiscussion(
            agent=self.name,
            message=f"[Plan] Will query Tracking API to get customer-visible load data. This shows what the customer sees in their dashboard.",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        try:
            # Try tracking_id first
            if tracking_id:
                # Executing action
                action_msg = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /api/v1/tracking?tracking_ids={tracking_id}",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "tracking_api"}
                )
                updates["agent_messages"].append(action_msg)

                result = await self._fetch_by_tracking_id(tracking_id)
                duration_ms = int((time.time() - start_time) * 1000)

                if result.get("exists"):
                    # Report findings
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Load found in Tracking API!\n" +
                                f"  • Load Number: {result.get('loadNumber', 'N/A')}\n" +
                                f"  • Status: {result.get('status', 'N/A')}\n" +
                                f"  • Mode: {result.get('mode', 'N/A')}\n" +
                                f"  • Carrier: {result.get('carrier', 'N/A')}\n" +
                                f"  • Shipper: {result.get('shipper', 'N/A')}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)

                    query_log = self.log_query(
                        state,
                        "Tracking API",
                        f"GET /api/v1/tracking?tracking_ids={tracking_id}",
                        result_count=1,
                        raw_result=result.get("raw"),
                        duration_ms=duration_ms
                    )
                    self._merge_updates(updates, query_log)

                    message = f"Load found: {result.get('loadNumber', 'N/A')}, status: {result.get('status', 'N/A')}, mode: {result.get('mode', 'N/A')}"

                    return {
                        **updates,
                        "tracking_data": result,
                        "_message": message
                    }
                else:
                    # Not found by tracking_id - check if it looks like a load_number
                    # FK load numbers are typically 9-10 digits starting with 13 or 14
                    if tracking_id and tracking_id.isdigit() and len(tracking_id) >= 9:
                        not_found = AgentDiscussion(
                            agent=self.name,
                            message=f"[Finding] Load not found by tracking_id={tracking_id}. Looks like a load_number, trying that...",
                            message_type="observation",
                            timestamp=datetime.now()
                        )
                        updates["agent_discussions"].append(not_found)
                        # Try as load_number
                        if not load_number:
                            load_number = tracking_id
                    else:
                        not_found = AgentDiscussion(
                            agent=self.name,
                            message=f"[Finding] Load not found by tracking_id={tracking_id}. Will try load_number if available.",
                            message_type="observation",
                            timestamp=datetime.now()
                        )
                        updates["agent_discussions"].append(not_found)

            # Fallback to load_number
            if load_number:
                action_msg = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /api/v1/tracking?loadNumbers={load_number}",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "tracking_api"}
                )
                updates["agent_messages"].append(action_msg)

                result = await self._fetch_by_load_number(load_number)
                duration_ms = int((time.time() - start_time) * 1000)

                query_log = self.log_query(
                    state,
                    "Tracking API",
                    f"GET /api/v1/tracking?loadNumbers={load_number}",
                    result_count=1 if result.get("exists") else 0,
                    raw_result=result.get("raw") if result.get("exists") else None,
                    duration_ms=duration_ms
                )
                self._merge_updates(updates, query_log)

                if result.get("exists"):
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Load found by load_number!\n" +
                                f"  • Tracking ID: {result.get('tracking_id', 'N/A')}\n" +
                                f"  • Status: {result.get('status', 'N/A')}\n" +
                                f"  • Mode: {result.get('mode', 'N/A')}\n" +
                                f"  • Carrier: {result.get('carrier', 'N/A')}\n" +
                                f"  • Shipper: {result.get('shipper', 'N/A')}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Load found by load_number: {load_number}"
                else:
                    finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Load NOT found in Tracking API. This could mean:\n" +
                                f"  • Load was never created\n" +
                                f"  • Load number is incorrect\n" +
                                f"  • Load was deleted or archived",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(finding)
                    message = f"Load not found in Tracking API"

                return {
                    **updates,
                    "tracking_data": result,
                    "_message": message
                }

            # No results from either
            return {
                **updates,
                "tracking_data": {"exists": False},
                "_message": "Load not found in Tracking API"
            }

        except Exception as e:
            self.logger.error(f"Tracking API error: {str(e)}")

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query Tracking API: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "tracking_data": {"exists": False, "error": str(e)},
                "_message": f"Tracking API error: {str(e)}"
            }

    async def _fetch_by_tracking_id(self, tracking_id: str) -> Dict[str, Any]:
        """Fetch load by tracking ID"""
        try:
            data = self.client.get_tracking_by_id(tracking_id)

            if data and isinstance(data, dict):
                # API returns {"statusCode": 200, "loads": [...], "pagination": {...}}
                # or {"load": {...}} - we need to extract the actual load
                load = None
                if "loads" in data and data["loads"]:
                    load = data["loads"][0]  # Take first load from array
                elif "load" in data:
                    load = data["load"]

                if load:
                    # Handle nested objects for shipper/carrier
                    shipper = load.get("shipper", {}) if isinstance(load.get("shipper"), dict) else {}
                    carrier = load.get("carrier", {}) if isinstance(load.get("carrier"), dict) else {}

                    return {
                        "exists": True,
                        "tracking_id": tracking_id,
                        "loadNumber": load.get("loadNumber"),
                        "status": load.get("status"),
                        "mode": load.get("loadMode") or load.get("actualLoadMode"),
                        "carrier": carrier.get("name") or load.get("carrierName"),
                        "shipper": shipper.get("name") or load.get("shipperName"),
                        "shipperCompanyId": shipper.get("id") or load.get("shipperId"),
                        "stops": load.get("stops", []),
                        "raw": data
                    }
                else:
                    return {"exists": False, "raw": data}
            else:
                return {"exists": False}
        except Exception as e:
            self.logger.warning(f"Load not found by tracking_id {tracking_id}: {str(e)}")
            return {"exists": False, "error": str(e)}

    async def _fetch_by_load_number(self, load_number: str) -> Dict[str, Any]:
        """Fetch load by load number"""
        try:
            data = self.client.get_tracking_by_load_number(load_number)

            if data and isinstance(data, dict):
                # API returns {"statusCode": 200, "loads": [...], "pagination": {...}}
                load = None
                if "loads" in data and data["loads"]:
                    load = data["loads"][0]  # Take first load from array
                elif "load" in data:
                    load = data["load"]

                if load:
                    # Handle nested objects for shipper/carrier
                    shipper = load.get("shipper", {}) if isinstance(load.get("shipper"), dict) else {}
                    carrier = load.get("carrier", {}) if isinstance(load.get("carrier"), dict) else {}

                    return {
                        "exists": True,
                        "load_number": load_number,
                        "tracking_id": load.get("id"),
                        "loadNumber": load.get("loadNumber"),
                        "status": load.get("status"),
                        "mode": load.get("loadMode") or load.get("actualLoadMode"),
                        "carrier": carrier.get("name") or load.get("carrierName"),
                        "shipper": shipper.get("name") or load.get("shipperName"),
                        "raw": data
                    }
                else:
                    return {"exists": False, "raw": data}
            else:
                return {"exists": False}
        except Exception as e:
            self.logger.warning(f"Load not found by load_number {load_number}: {str(e)}")
            return {"exists": False, "error": str(e)}

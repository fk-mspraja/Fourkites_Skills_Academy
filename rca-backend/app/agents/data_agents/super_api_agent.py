"""
Super API (DataHub) Data Collection Agent
Fetches internal tracking configuration and subscription details
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.super_api_client import SuperAPIClient


class SuperAPIAgent(BaseAgent):
    """
    Collects internal tracking configuration from Super API with verbose output.

    Role: Configuration Expert
    I examine the internal configuration to ensure tracking is properly set up.
    """

    def __init__(self):
        super().__init__("Super API Agent")
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
        Fetch tracking configuration from Super API with verbose output
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")
        load_number = self.extract_identifier(state, "load_number")

        identifier = tracking_id or load_number

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Checking DataHub for tracking configuration.\n" +
                    f"  • tracking_id: {tracking_id or 'not available'}\n" +
                    f"  • load_number: {load_number or 'not available'}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        if not identifier:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No identifiers available. Cannot query Super API without tracking_id or load_number.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "super_api_data": {"skipped": True, "reason": "No identifier"},
                "_message": "No identifier for Super API lookup"
            }

        # Check if this is an ocean load
        tracking_data = state.get("tracking_data", {})
        actual_mode = (tracking_data.get("mode") or "").lower()
        is_ocean = any(keyword in actual_mode for keyword in ["ocean", "intermodal", "multimodal"])

        # Plan
        plan_items = [
            "  • Tracking source configuration",
            "  • Primary identifier used for tracking",
            "  • Subscription ID (if ocean mode)",
            "  • Carrier code and tracking method"
        ]
        if is_ocean:
            plan_items.append("  • Ocean events from DataHub SuperAPI (all carrier events)")

        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will query DataHub Super API to get:\n" + "\n".join(plan_items),
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] GET /v1/tracking/config/{identifier}",
            status=AgentStatus.RUNNING,
            metadata={"type": "api_call", "endpoint": "datahub"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Get tracking config
            config = await self.client.get_tracking_config(identifier)
            duration_ms = int((time.time() - start_time) * 1000)

            query_log = self.log_query(
                state,
                "Super API (DataHub)",
                f"GET /v1/tracking/config/{identifier}",
                result_count=1 if config.get("exists") else 0,
                raw_result=config,
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            if not config.get("exists"):
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] Tracking configuration NOT found in DataHub.\n" +
                            "  • The load may not be configured for tracking\n" +
                            "  • Or the identifier doesn't match any records\n" +
                            "  • This could indicate a load creation issue",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)

                return {
                    **updates,
                    "super_api_data": config,
                    "_message": "Tracking config not found in Super API"
                }

            # Config found - report details
            tracking_source = config.get("tracking_source", "unknown")
            carrier_code = config.get("carrier_code", "N/A")
            subscription_id = config.get("subscription_id")

            finding = AgentDiscussion(
                agent=self.name,
                message=f"[Finding] Tracking configuration found!\n" +
                        f"  • Tracking source: {tracking_source}\n" +
                        f"  • Carrier code: {carrier_code}\n" +
                        f"  • Subscription ID: {subscription_id or 'N/A'}\n" +
                        f"  • Primary identifier: {config.get('primary_identifier', 'N/A')}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(finding)

            # If we have subscription_id, get subscription details
            if subscription_id:
                sub_action = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /v1/subscriptions/{subscription_id}",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "datahub"}
                )
                updates["agent_messages"].append(sub_action)

                sub_details = await self.client.get_subscription_details(subscription_id)
                config["subscription_details"] = sub_details

                # Additional query log for subscription
                sub_query_log = self.log_query(
                    state,
                    "Super API (DataHub)",
                    f"GET /v1/subscriptions/{subscription_id}",
                    result_count=1 if sub_details.get("exists") else 0,
                    raw_result=sub_details
                )
                self._merge_updates(updates, sub_query_log)

                # Report subscription details
                if sub_details.get("exists"):
                    scraping_status = "enabled" if sub_details.get("scraping_enabled") else "disabled"
                    sub_finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Subscription details retrieved.\n" +
                                f"  • Subscription ID: {subscription_id}\n" +
                                f"  • Scraping: {scraping_status}\n" +
                                f"  • Last update: {sub_details.get('last_update', 'N/A')}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(sub_finding)

            # For ocean loads, also fetch ocean events from DataHub SuperAPI
            if is_ocean:
                container = self.extract_identifier(state, "container_number")
                booking = self.extract_identifier(state, "booking_number")

                event_identifier = container or booking or identifier
                event_type = "container" if container else ("booking" if booking else "container")

                ocean_action = AgentMessage(
                    agent=self.name,
                    message=f"[Executing] GET /v1/ocean/events?{event_type}={event_identifier}",
                    status=AgentStatus.RUNNING,
                    metadata={"type": "api_call", "endpoint": "datahub_ocean"}
                )
                updates["agent_messages"].append(ocean_action)

                ocean_events = await self.client.get_ocean_events(event_identifier, event_type)
                config["ocean_events"] = ocean_events

                # Log ocean events query
                ocean_query_log = self.log_query(
                    state,
                    "DataHub Ocean SuperAPI",
                    f"GET /v1/ocean/events?{event_type}={event_identifier}",
                    result_count=ocean_events.get("event_count", 0),
                    raw_result=ocean_events
                )
                self._merge_updates(updates, ocean_query_log)

                # Report ocean events
                if ocean_events.get("exists"):
                    event_count = ocean_events.get("event_count", 0)
                    events = ocean_events.get("events", [])

                    # Build event timeline summary
                    event_summary = []
                    for evt in events[:5]:  # Show first 5 events
                        code = evt.get("event_code", "?")
                        time_str = evt.get("event_time", "")[:10] if evt.get("event_time") else "?"
                        loc = evt.get("location", "?")
                        event_summary.append(f"    - {code} at {loc} ({time_str})")

                    ocean_finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Ocean events from DataHub SuperAPI!\n" +
                                f"  • Total events: {event_count}\n" +
                                f"  • Carrier: {ocean_events.get('carrier_name', 'N/A')}\n" +
                                f"  • Vessel: {ocean_events.get('vessel', 'N/A')}\n" +
                                f"  • Recent events:\n" + "\n".join(event_summary),
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(ocean_finding)
                else:
                    ocean_finding = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] No ocean events found in DataHub for {event_identifier}.\n" +
                                f"  • This could indicate the container is not being tracked\n" +
                                f"  • Or no carrier data has been received yet",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(ocean_finding)

            message = self._build_message(config)

            return {
                **updates,
                "super_api_data": config,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Super API error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to query Super API: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "super_api_data": {"error": str(e), "exists": False},
                "_message": f"Super API error: {str(e)}"
            }

    def _build_message(self, config: Dict[str, Any]) -> str:
        """Build summary message from config"""
        if not config.get("exists"):
            return "Tracking config not found"

        parts = []

        if config.get("tracking_source"):
            parts.append(f"source={config['tracking_source']}")

        if config.get("subscription_id"):
            parts.append(f"subscription={config['subscription_id']}")

        if config.get("carrier_code"):
            parts.append(f"carrier={config['carrier_code']}")

        if config.get("subscription_details"):
            sub = config["subscription_details"]
            if sub.get("scraping_enabled"):
                parts.append("scraping=enabled")
            else:
                parts.append("scraping=disabled")

        return f"Config found: {', '.join(parts)}" if parts else "Config found"

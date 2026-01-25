"""
Sub-Investigation Agent for testing individual hypotheses.

Each sub-agent is responsible for testing a single hypothesis by:
1. Querying relevant data sources
2. Evaluating evidence against the hypothesis
3. Updating confidence based on findings
4. Optionally spawning child sub-agents for deeper investigation
"""

import asyncio
import inspect
import logging
import time
from typing import Any, Dict, List, Optional

from core.models.hypothesis import Hypothesis, AgentAction, SubAgentResult
from core.models.evidence import Evidence, EvidenceType, EvidenceSource
from core.engine.hypothesis_engine import HypothesisEngine
from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SubInvestigationAgent:
    """
    Independent agent that tests a single hypothesis.

    The agent uses LLM reasoning to decide what data to query,
    can revisit APIs with different parameters, and can spawn
    child sub-agents for more specific investigations.
    """

    # Map client names to evidence sources
    CLIENT_TO_SOURCE = {
        "tracking_api": EvidenceSource.TRACKING_API,
        "company_api": EvidenceSource.COMPANY_API,
        "redshift": EvidenceSource.REDSHIFT,
        "clickhouse": EvidenceSource.SIGNOZ,
        "justtransform": EvidenceSource.JUSTTRANSFORM,
        "super_api": EvidenceSource.SUPER_API,
    }

    def __init__(
        self,
        agent_id: str,
        hypothesis: Hypothesis,
        clients: Dict[str, Any],
        llm_client: LLMClient,
        hypothesis_engine: HypothesisEngine,
        identifiers: Dict[str, Any],
        max_iterations: int = 5,
        parent_id: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.hypothesis = hypothesis
        self.clients = clients
        self.llm = llm_client
        self.hypothesis_engine = hypothesis_engine
        self.identifiers = identifiers
        self.max_iterations = max_iterations
        self.parent_id = parent_id

        self.evidence: List[Evidence] = []
        self.children: List[str] = []
        self.iteration = 0

    async def investigate(self, event_callback: Optional[Any] = None) -> SubAgentResult:
        """
        Run investigation for this hypothesis.

        The agent loops until:
        - Hypothesis is confirmed/eliminated
        - Max iterations reached
        - LLM decides to conclude

        Args:
            event_callback: Optional async callback for streaming events

        Returns:
            SubAgentResult with hypothesis, evidence, and any child agents
        """
        start_time = time.time()

        async def emit_event(event_type: str, data: Dict[str, Any]):
            if event_callback:
                await event_callback(event_type, data)

        logger.info(f"[{self.agent_id}] Starting investigation of: {self.hypothesis.description[:60]}...")

        while self.iteration < self.max_iterations:
            self.iteration += 1

            # Check if should continue
            if not await self.hypothesis_engine.should_continue(self.hypothesis):
                logger.info(
                    f"[{self.agent_id}] Stopping: hypothesis status={self.hypothesis.status}, "
                    f"confidence={self.hypothesis.confidence:.2f}"
                )
                break

            # LLM decides next action
            action = await self.hypothesis_engine.decide_next_action(
                hypothesis=self.hypothesis,
                evidence_so_far=self.evidence,
                available_clients=list(self.clients.keys())
            )

            logger.info(f"[{self.agent_id}] Iteration {self.iteration}: {action.type} - {action.reason[:80]}...")

            # Emit action event
            await emit_event("agent_action", {
                "agent_id": self.agent_id,
                "iteration": self.iteration,
                "action_type": action.type,
                "source": action.source,
                "method": action.method,
                "reason": action.reason[:200]
            })

            # Execute action
            if action.type in ["query_data_source", "revisit"]:
                evidence = await self._execute_query(action)

                if evidence:
                    self.evidence.append(evidence)

                    # Emit evidence event
                    await emit_event("evidence", {
                        "agent_id": self.agent_id,
                        "finding": evidence.finding,
                        "source": evidence.source.value if hasattr(evidence.source, 'value') else str(evidence.source),
                        "type": evidence.type.value if hasattr(evidence.type, 'value') else str(evidence.type)
                    })

                    # Update hypothesis confidence
                    old_confidence = self.hypothesis.confidence
                    self.hypothesis = await self.hypothesis_engine.update_hypothesis(
                        self.hypothesis, evidence
                    )

                    # Emit hypothesis update if confidence changed
                    if abs(self.hypothesis.confidence - old_confidence) > 0.01:
                        await emit_event("hypothesis_update", {
                            "id": self.hypothesis.id,
                            "confidence": self.hypothesis.confidence,
                            "status": self.hypothesis.status,
                            "delta": self.hypothesis.confidence - old_confidence
                        })

            elif action.type == "spawn_child":
                # Record child hypothesis for orchestrator to handle
                self.children.append(action.child_hypothesis)
                logger.info(f"[{self.agent_id}] Spawning child: {action.child_hypothesis[:60]}...")

                await emit_event("child_spawned", {
                    "agent_id": self.agent_id,
                    "child_hypothesis": action.child_hypothesis[:200]
                })

            elif action.type == "conclude":
                logger.info(f"[{self.agent_id}] Concluding: {action.reason}")
                await emit_event("agent_concluded", {
                    "agent_id": self.agent_id,
                    "reason": action.reason
                })
                break

        execution_time = time.time() - start_time

        logger.info(
            f"[{self.agent_id}] Completed: "
            f"status={self.hypothesis.status}, "
            f"confidence={self.hypothesis.confidence:.2f}, "
            f"evidence={len(self.evidence)}, "
            f"time={execution_time:.2f}s"
        )

        return SubAgentResult(
            agent_id=self.agent_id,
            hypothesis=self.hypothesis,
            evidence=self.evidence,
            children=self.children,
            iterations=self.iteration,
            execution_time=execution_time
        )

    async def _execute_query(self, action: AgentAction) -> Optional[Evidence]:
        """
        Execute a data source query based on the action.

        Args:
            action: AgentAction with source, method, and params

        Returns:
            Evidence object if successful, None otherwise
        """
        source = action.source
        method_name = action.method
        params = action.params or {}

        # Get client
        client = self.clients.get(source)
        if not client:
            logger.warning(f"[{self.agent_id}] Client '{source}' not found")
            return None

        # Get method
        method = getattr(client, method_name, None)
        if not method:
            logger.warning(f"[{self.agent_id}] Method '{method_name}' not found on {source}")
            return None

        # Fill in params from identifiers if not provided
        params = self._fill_params(method_name, params)

        try:
            start_time = time.time()

            # Execute method (handle both sync and async)
            if inspect.iscoroutinefunction(method):
                result = await asyncio.wait_for(method(**params), timeout=30.0)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(method, **params),
                    timeout=30.0
                )

            execution_time = (time.time() - start_time) * 1000  # ms

            # Convert result to evidence
            evidence = self._result_to_evidence(
                source=source,
                method=method_name,
                result=result,
                execution_time=execution_time
            )

            logger.info(f"[{self.agent_id}] Query {source}.{method_name} succeeded: {evidence.finding[:60]}...")

            return evidence

        except asyncio.TimeoutError:
            logger.error(f"[{self.agent_id}] Query {source}.{method_name} timed out")
            return None

        except Exception as e:
            logger.error(f"[{self.agent_id}] Query {source}.{method_name} failed: {e}")
            return None

    def _fill_params(self, method_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in missing params from identifiers"""
        filled = params.copy()

        # Map method names to required identifier keys
        param_mapping = {
            "get_tracking_by_id": {"tracking_id": "load_id"},
            "search_loads": {"load_number": "load_number"},
            "get_company_relationship": {
                "company_permalink": "shipper_id",
                "related_company_id": "carrier_id"
            },
            "find_similar_stuck_loads": {"carrier_id": "carrier_id"},
            "query_network_relationships": {
                "shipper_id": "shipper_id",
                "carrier_id": "carrier_id"
            },
            "get_subscription_history": {"subscription_id": "subscription_id"},
            "get_ocean_processing_logs": {
                "container_number": "container_number",
                "booking_number": "booking_number"
            },
            "get_tracking_config": {"load_id": "load_id"},
        }

        mapping = param_mapping.get(method_name, {})

        for param_key, id_key in mapping.items():
            if param_key not in filled and id_key in self.identifiers:
                value = self.identifiers[id_key]
                # Convert load_id to int for tracking API
                if param_key == "tracking_id" and isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                filled[param_key] = value

        return filled

    def _result_to_evidence(
        self,
        source: str,
        method: str,
        result: Any,
        execution_time: float
    ) -> Evidence:
        """Convert API/DB result to Evidence object"""

        # Determine evidence source
        evidence_source = self.CLIENT_TO_SOURCE.get(source, EvidenceSource.PLATFORM)

        # Generate finding summary
        finding = self._summarize_result(source, method, result)

        # Convert result to dict if needed
        raw_data = result if isinstance(result, dict) else {"data": result}

        return Evidence(
            type=EvidenceType.API if "api" in source else EvidenceType.DATABASE,
            source=evidence_source,
            step_id=f"{self.agent_id}_{method}",
            finding=finding,
            raw_data=raw_data,
            query_time_ms=execution_time
        )

    def _summarize_result(self, source: str, method: str, result: Any) -> str:
        """Generate human-readable summary of result"""

        if result is None:
            return f"No data returned from {source}.{method}"

        if not isinstance(result, dict):
            return f"Result from {source}.{method}: {str(result)[:100]}"

        # Source-specific summaries
        if source == "tracking_api":
            if result.get("exists") or result.get("load_exists"):
                status = result.get("status") or result.get("current_state", "unknown")
                carrier = result.get("carrier", {}).get("name", "unknown")
                return f"Load exists, status={status}, carrier={carrier}"
            return "Load not found in tracking system"

        if source == "company_api":
            if result.get("exists"):
                relationships = result.get("relationships", [])
                if relationships:
                    status = relationships[0].get("status", "unknown")
                    return f"Network relationship exists, status={status}"
                return "Relationship data found but no details"
            return "No carrier-shipper relationship found"

        if source == "justtransform":
            count = result.get("events_count", 0)
            has_disc = result.get("has_discrepancies", False)
            if count == 0:
                return "No JT scraping history found"
            if has_disc:
                return f"Found {count} JT events with discrepancies"
            return f"Found {count} JT events, no discrepancies"

        if source == "super_api":
            if result.get("exists"):
                tracking_source = result.get("tracking_source", "unknown")
                return f"Tracking config exists, source={tracking_source}"
            return "No tracking configuration found"

        if source == "clickhouse":
            count = result.get("count", 0)
            if count == 0:
                return "No processing logs found"
            return f"Found {count} processing log entries"

        if source == "redshift":
            affected = result.get("affected_loads", 0)
            if affected > 0:
                return f"{affected} similar loads also affected"
            return "No similar affected loads found"

        # Default
        return f"Data from {source}.{method}: {len(result)} fields"

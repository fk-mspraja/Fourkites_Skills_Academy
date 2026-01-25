"""
Hypothesis Orchestrator for adaptive RCA investigation.

Coordinates multiple SubInvestigationAgents running in parallel,
each testing a different hypothesis about the root cause.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.models.hypothesis import Hypothesis, SubAgentResult, RootCauseSynthesis
from core.models.evidence import Evidence
from core.models.result import InvestigationResult, RootCauseCategory
from core.engine.hypothesis_engine import HypothesisEngine
from core.engine.sub_agent import SubInvestigationAgent
from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class HypothesisOrchestrator:
    """
    Main supervisor for hypothesis-driven investigation.

    Workflow:
    1. Form initial hypotheses using LLM
    2. Spawn sub-agents for each hypothesis
    3. Run sub-agents in parallel
    4. Collect and correlate evidence
    5. Synthesize final root cause using LLM
    """

    def __init__(
        self,
        clients: Dict[str, Any],
        llm_client: LLMClient,
        hypothesis_engine: HypothesisEngine,
        max_parallel_agents: int = 5,
        max_child_depth: int = 2
    ):
        self.clients = clients
        self.llm = llm_client
        self.hypothesis_engine = hypothesis_engine
        self.max_parallel = max_parallel_agents
        self.max_child_depth = max_child_depth

        self.sub_agents: Dict[str, SubInvestigationAgent] = {}
        self.results: List[SubAgentResult] = []

    async def investigate(
        self,
        identifiers: Dict[str, Any],
        initial_evidence: List[Evidence],
        event_callback: Optional[Any] = None
    ) -> InvestigationResult:
        """
        Run hypothesis-driven investigation.

        Args:
            identifiers: Known identifiers (load_id, carrier_id, etc.)
            initial_evidence: Evidence from initial platform check
            event_callback: Optional async callback for streaming events

        Returns:
            InvestigationResult with root cause, evidence, and recommendations
        """
        start_time = datetime.utcnow()

        async def emit_event(event_type: str, data: Dict[str, Any]):
            if event_callback:
                await event_callback(event_type, data)

        # Phase 1: Form hypotheses
        logger.info("Phase 1: Forming hypotheses...")
        await emit_event("log", {"message": "Phase 1: Forming hypotheses using LLM...", "phase": "forming_hypotheses"})

        hypotheses = await self.hypothesis_engine.form_initial_hypotheses(
            identifiers, initial_evidence
        )

        if not hypotheses:
            logger.error("Failed to form any hypotheses")
            await emit_event("error", {"message": "Failed to form any hypotheses"})
            return self._create_error_result(
                "Failed to form hypotheses",
                start_time
            )

        logger.info(f"Formed {len(hypotheses)} hypotheses")

        # Emit hypothesis events
        for h in hypotheses:
            await emit_event("hypothesis", {
                "id": h.id,
                "description": h.description,
                "root_cause_type": h.root_cause_type,
                "confidence": h.confidence,
                "status": h.status
            })

        # Phase 2: Spawn sub-agents
        logger.info("Phase 2: Spawning sub-agents...")
        await emit_event("log", {"message": f"Phase 2: Spawning {len(hypotheses)} sub-agents...", "phase": "spawning_agents"})
        agents = self._spawn_agents(hypotheses, identifiers)

        # Emit sub-agent spawn events
        for agent in agents:
            await emit_event("subagent", {
                "agent_id": agent.agent_id,
                "hypothesis_id": agent.hypothesis.id,
                "status": "spawned",
                "hypothesis": agent.hypothesis.description[:100]
            })

        # Phase 3: Run agents in parallel
        logger.info(f"Phase 3: Running {len(agents)} sub-agents in parallel...")
        await emit_event("log", {"message": f"Phase 3: Running {len(agents)} sub-agents in parallel...", "phase": "running_agents"})

        results = await self._run_agents_parallel(agents, event_callback)

        # Phase 4: Handle child agents (if any spawned)
        logger.info("Phase 4: Processing child agents...")
        await emit_event("log", {"message": "Phase 4: Processing child agents...", "phase": "child_agents"})
        results = await self._process_children(results, identifiers, depth=1, event_callback=event_callback)

        # Phase 5: Collect all evidence
        logger.info("Phase 5: Collecting evidence...")
        await emit_event("log", {"message": "Phase 5: Collecting and correlating evidence...", "phase": "collecting_evidence"})
        all_evidence = self._collect_all_evidence(results, initial_evidence)
        final_hypotheses = [r.hypothesis for r in results]

        # Emit final hypothesis status
        for h in final_hypotheses:
            await emit_event("hypothesis_update", {
                "id": h.id,
                "status": h.status,
                "confidence": h.confidence
            })

        # Phase 6: Synthesize root cause
        logger.info("Phase 6: Synthesizing root cause...")
        await emit_event("log", {"message": "Phase 6: Synthesizing root cause using LLM...", "phase": "synthesizing"})
        synthesis = await self._synthesize_root_cause(final_hypotheses, all_evidence)

        await emit_event("synthesis", {
            "root_cause": synthesis.root_cause,
            "root_cause_type": synthesis.root_cause_type,
            "confidence": synthesis.confidence,
            "hypotheses_tested": synthesis.hypotheses_tested,
            "hypotheses_confirmed": synthesis.hypotheses_confirmed,
            "total_evidence": synthesis.total_evidence
        })

        # Build final result
        return self._build_result(
            synthesis=synthesis,
            hypotheses=final_hypotheses,
            evidence=all_evidence,
            start_time=start_time
        )

    # Map root cause types to friendly agent names
    AGENT_NAMES = {
        "network_relationship_missing": "Network Checker",
        "network_relationship_inactive": "Network Checker",
        "jt_scraping_error": "JT Investigator",
        "jt_formatting_error": "JT Investigator",
        "carrier_portal_down": "Carrier Monitor",
        "carrier_data_incorrect": "Carrier Monitor",
        "subscription_inactive": "Subscription Checker",
        "identifier_mismatch": "ID Validator",
        "system_processing_error": "System Analyzer",
    }

    def _spawn_agents(
        self,
        hypotheses: List[Hypothesis],
        identifiers: Dict[str, Any],
        parent_id: Optional[str] = None
    ) -> List[SubInvestigationAgent]:
        """Spawn sub-agents for each hypothesis"""
        agents = []
        name_counts = {}  # Track duplicates for numbering

        for i, hypothesis in enumerate(hypotheses):
            # Generate friendly name based on hypothesis type
            base_name = self.AGENT_NAMES.get(hypothesis.root_cause_type, "Investigator")
            name_counts[base_name] = name_counts.get(base_name, 0) + 1

            if name_counts[base_name] > 1:
                agent_id = f"{base_name} #{name_counts[base_name]}"
            else:
                agent_id = base_name

            if parent_id:
                agent_id = f"{parent_id} > Child {i+1}"

            agent = SubInvestigationAgent(
                agent_id=agent_id,
                hypothesis=hypothesis,
                clients=self.clients,
                llm_client=self.llm,
                hypothesis_engine=self.hypothesis_engine,
                identifiers=identifiers,
                parent_id=parent_id
            )

            agents.append(agent)
            self.sub_agents[agent_id] = agent

            logger.info(f"Spawned {agent_id}: {hypothesis.description[:50]}...")

        return agents

    async def _run_agents_parallel(
        self,
        agents: List[SubInvestigationAgent],
        event_callback: Optional[Any] = None
    ) -> List[SubAgentResult]:
        """Run multiple agents in parallel with concurrency limit"""
        if not agents:
            return []

        semaphore = asyncio.Semaphore(self.max_parallel)

        async def emit_event(event_type: str, data: Dict[str, Any]):
            if event_callback:
                await event_callback(event_type, data)

        async def run_with_limit(agent: SubInvestigationAgent) -> SubAgentResult:
            async with semaphore:
                try:
                    await emit_event("subagent_update", {
                        "agent_id": agent.agent_id,
                        "status": "running",
                        "iteration": 0
                    })

                    result = await agent.investigate(event_callback=event_callback)

                    await emit_event("subagent_update", {
                        "agent_id": agent.agent_id,
                        "status": "completed",
                        "iterations": result.iterations,
                        "evidence_count": len(result.evidence),
                        "hypothesis_status": result.hypothesis.status,
                        "hypothesis_confidence": result.hypothesis.confidence
                    })

                    return result
                except Exception as e:
                    logger.error(f"Agent {agent.agent_id} failed: {e}")
                    await emit_event("subagent_update", {
                        "agent_id": agent.agent_id,
                        "status": "failed",
                        "error": str(e)
                    })
                    return SubAgentResult(
                        agent_id=agent.agent_id,
                        hypothesis=agent.hypothesis,
                        error=str(e)
                    )

        results = await asyncio.gather(
            *[run_with_limit(agent) for agent in agents],
            return_exceptions=True
        )

        # Convert exceptions to error results
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent = agents[i]
                result = SubAgentResult(
                    agent_id=agent.agent_id,
                    hypothesis=agent.hypothesis,
                    error=str(result)
                )
            processed.append(result)

        return processed

    async def _process_children(
        self,
        results: List[SubAgentResult],
        identifiers: Dict[str, Any],
        depth: int,
        event_callback: Optional[Any] = None
    ) -> List[SubAgentResult]:
        """Process child hypotheses spawned by agents"""
        if depth >= self.max_child_depth:
            logger.info(f"Max child depth ({self.max_child_depth}) reached")
            return results

        # Collect child hypotheses
        child_hypotheses = []
        parent_map = {}

        for result in results:
            for child_desc in result.children:
                child_hyp = Hypothesis(
                    description=child_desc,
                    root_cause_type=result.hypothesis.root_cause_type,
                    confidence=result.hypothesis.confidence * 0.8  # Inherit reduced confidence
                )
                child_hypotheses.append(child_hyp)
                parent_map[child_hyp.id] = result.agent_id

        if not child_hypotheses:
            return results

        logger.info(f"Processing {len(child_hypotheses)} child hypotheses at depth {depth}")

        # Spawn and run child agents
        child_agents = []
        for hyp in child_hypotheses:
            parent_id = parent_map.get(hyp.id)
            agents = self._spawn_agents([hyp], identifiers, parent_id=parent_id)
            child_agents.extend(agents)

        child_results = await self._run_agents_parallel(child_agents, event_callback)

        # Recursively process their children
        child_results = await self._process_children(
            child_results, identifiers, depth + 1, event_callback
        )

        # Combine with parent results
        return results + child_results

    def _collect_all_evidence(
        self,
        results: List[SubAgentResult],
        initial_evidence: List[Evidence]
    ) -> List[Evidence]:
        """Collect all evidence from all sub-agents"""
        all_evidence = list(initial_evidence)

        for result in results:
            all_evidence.extend(result.evidence)

        # Remove duplicates by ID
        seen = set()
        unique = []
        for ev in all_evidence:
            if ev.id not in seen:
                seen.add(ev.id)
                unique.append(ev)

        return unique

    async def _synthesize_root_cause(
        self,
        hypotheses: List[Hypothesis],
        all_evidence: List[Evidence]
    ) -> RootCauseSynthesis:
        """Use LLM to synthesize final root cause from all findings"""

        # Convert to dicts for LLM
        hyp_dicts = [
            {
                "description": h.description,
                "root_cause_type": h.root_cause_type,
                "confidence": h.confidence,
                "status": h.status
            }
            for h in hypotheses
        ]

        evidence_dicts = [
            {
                "finding": e.finding,
                "source": e.source.value if hasattr(e.source, 'value') else str(e.source)
            }
            for e in all_evidence
        ]

        # Call LLM
        response = self.llm.synthesize_root_cause(hyp_dicts, evidence_dicts)

        # Parse response
        return RootCauseSynthesis(
            root_cause=response.get("root_cause"),
            root_cause_type=response.get("root_cause_type"),
            confidence=float(response.get("confidence", 0.0)),
            explanation=response.get("explanation", ""),
            recommended_actions=response.get("recommended_actions", []),
            remaining_uncertainties=response.get("remaining_uncertainties", []),
            hypotheses_tested=len(hypotheses),
            hypotheses_confirmed=sum(1 for h in hypotheses if h.status == "confirmed"),
            hypotheses_eliminated=sum(1 for h in hypotheses if h.status == "eliminated"),
            total_evidence=len(all_evidence)
        )

    def _build_result(
        self,
        synthesis: RootCauseSynthesis,
        hypotheses: List[Hypothesis],
        evidence: List[Evidence],
        start_time: datetime
    ) -> InvestigationResult:
        """Build final InvestigationResult"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Map root cause type to category
        category_map = {
            # Network/Configuration
            "network_relationship_missing": RootCauseCategory.CONFIGURATION_ISSUE,
            "network_relationship_inactive": RootCauseCategory.CONFIGURATION_ISSUE,
            "carrier_config_missing": RootCauseCategory.CONFIGURATION_ISSUE,

            # JustTransform/ELD
            "jt_scraping_error": RootCauseCategory.JT_ISSUE,
            "jt_formatting_error": RootCauseCategory.JT_ISSUE,
            "eld_integration_error": RootCauseCategory.JT_ISSUE,

            # Carrier Issues
            "carrier_portal_down": RootCauseCategory.CARRIER_ISSUE,
            "carrier_data_incorrect": RootCauseCategory.CARRIER_ISSUE,
            "carrier_file_processing_error": RootCauseCategory.CARRIER_ISSUE,
            "carrier_file_malformed": RootCauseCategory.CARRIER_ISSUE,

            # TL/FTL Specific
            "asset_assignment_failure": RootCauseCategory.CARRIER_ISSUE,
            "truck_trailer_missing": RootCauseCategory.CARRIER_ISSUE,
            "location_processing_error": RootCauseCategory.SYSTEM_BUG,
            "location_validation_rejected": RootCauseCategory.SYSTEM_BUG,
            "file_ingestion_error": RootCauseCategory.CARRIER_ISSUE,
            "data_mapping_error": RootCauseCategory.CONFIGURATION_ISSUE,
            "geocoding_failure": RootCauseCategory.SYSTEM_BUG,

            # System/Platform
            "subscription_inactive": RootCauseCategory.CONFIGURATION_ISSUE,
            "identifier_mismatch": RootCauseCategory.CONFIGURATION_ISSUE,
            "system_processing_error": RootCauseCategory.SYSTEM_BUG,
        }

        category = category_map.get(
            synthesis.root_cause_type or "",
            RootCauseCategory.UNKNOWN
        )

        # Build explanation with synthesis info
        explanation = synthesis.explanation
        if synthesis.remaining_uncertainties:
            explanation += f"\n\nUncertainties: {', '.join(synthesis.remaining_uncertainties)}"

        logger.info(
            f"Investigation complete: root_cause={synthesis.root_cause_type}, "
            f"confidence={synthesis.confidence:.2f}, "
            f"hypotheses_tested={synthesis.hypotheses_tested}, "
            f"evidence_collected={synthesis.total_evidence}"
        )

        return InvestigationResult(
            ticket_id="",  # Will be set by caller
            case_number="",  # Will be set by caller
            root_cause=synthesis.root_cause,
            root_cause_category=category,
            confidence=synthesis.confidence,
            explanation=explanation,
            evidence=evidence,
            needs_human=synthesis.confidence < 0.6,
            human_question=(
                "Confidence is low. " + ", ".join(synthesis.remaining_uncertainties)
                if synthesis.confidence < 0.6 and synthesis.remaining_uncertainties
                else None
            ),
            investigation_time=duration,
            steps_executed=synthesis.hypotheses_tested,
            queries_executed=synthesis.total_evidence,
            started_at=start_time,
            completed_at=end_time
        )

    def _create_error_result(
        self,
        error: str,
        start_time: datetime
    ) -> InvestigationResult:
        """Create an error result"""
        end_time = datetime.utcnow()

        return InvestigationResult(
            ticket_id="",
            case_number="",
            needs_human=True,
            human_question=error,
            investigation_time=(end_time - start_time).total_seconds(),
            started_at=start_time,
            completed_at=end_time
        )

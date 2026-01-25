"""
LangGraph Multi-Agent Workflow
Orchestrates RCA investigation using StateGraph
"""
import asyncio
import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from app.models import InvestigationState, TransportMode

from app.agents.identifier_agent import IdentifierAgent
from app.agents.data_agents import (
    TrackingAPIAgent,
    JTAgent,
    SuperAPIAgent,
    NetworkAgent,
    RedshiftAgent,
    CallbacksAgent,
    OceanEventsAgent,
    OceanTraceAgent
)
from app.agents.hypothesis_agent import HypothesisAgent
from app.agents.synthesis_agent import SynthesisAgent

logger = logging.getLogger(__name__)


class RCAWorkflow:
    """Multi-agent RCA workflow using LangGraph"""

    def __init__(self):
        self.identifier_agent = IdentifierAgent()
        self.tracking_agent = TrackingAPIAgent()
        self.jt_agent = JTAgent()
        self.super_api_agent = SuperAPIAgent()
        self.network_agent = NetworkAgent()
        self.redshift_agent = RedshiftAgent()
        self.callbacks_agent = CallbacksAgent()
        self.ocean_events_agent = OceanEventsAgent()
        self.ocean_trace_agent = OceanTraceAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.synthesis_agent = SynthesisAgent()

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(InvestigationState)

        # Add nodes
        workflow.add_node("extract_identifiers", self._extract_identifiers_node)
        workflow.add_node("collect_data", self._parallel_data_collection_node)
        workflow.add_node("form_hypotheses", self._form_hypotheses_node)
        workflow.add_node("determine_root_cause", self._determine_root_cause_node)

        # Define edges
        workflow.set_entry_point("extract_identifiers")
        workflow.add_edge("extract_identifiers", "collect_data")
        workflow.add_edge("collect_data", "form_hypotheses")
        workflow.add_edge("form_hypotheses", "determine_root_cause")
        workflow.add_edge("determine_root_cause", END)

        return workflow.compile()

    async def _extract_identifiers_node(self, state: InvestigationState) -> Dict[str, Any]:
        """Node: Extract identifiers from issue text"""
        logger.info("=== STEP 1: Extracting Identifiers ===")
        return await self.identifier_agent.run(state)

    async def _parallel_data_collection_node(self, state: InvestigationState) -> Dict[str, Any]:
        """Node: Collect data from multiple sources in parallel"""
        logger.info("=== STEP 2: Parallel Data Collection ===")

        # Always run these agents in parallel
        tasks = [
            self.tracking_agent.run(state),
            self.network_agent.run(state),
            self.redshift_agent.run(state),
            self.callbacks_agent.run(state),
        ]

        # Conditionally run mode-specific agents
        mode = state.get("transport_mode", TransportMode.UNKNOWN)

        if mode == TransportMode.OCEAN:
            # For Ocean, we need Super API first to get subscription_id for JT and Ocean Trace
            super_api_result = await self.super_api_agent.run(state)
            # Merge Super API result into state for dependent agents
            state = {**state, **super_api_result}

            # Now run ocean-specific agents in parallel
            tasks.extend([
                self.jt_agent.run(state),
                self.ocean_events_agent.run(state),
                self.ocean_trace_agent.run(state)
            ])
        else:
            # For non-ocean, still try Super API (but won't run ocean agents)
            tasks.append(self.super_api_agent.run(state))

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all results
        merged_updates = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent error: {str(result)}")
                continue
            if isinstance(result, dict):
                merged_updates = {**merged_updates, **result}

        return merged_updates

    async def _form_hypotheses_node(self, state: InvestigationState) -> Dict[str, Any]:
        """Node: Form hypotheses from collected evidence"""
        logger.info("=== STEP 3: Forming Hypotheses ===")
        return await self.hypothesis_agent.run(state)

    async def _determine_root_cause_node(self, state: InvestigationState) -> Dict[str, Any]:
        """Node: Determine final root cause"""
        logger.info("=== STEP 4: Determining Root Cause ===")
        result = await self.synthesis_agent.run(state)

        # Mark investigation as complete
        from datetime import datetime
        result["completed_at"] = datetime.now()

        return result

    async def run(self, state: InvestigationState) -> InvestigationState:
        """
        Run the complete investigation workflow

        Args:
            state: Initial investigation state

        Returns:
            Final investigation state with root cause determination
        """
        logger.info(f"Starting RCA investigation: {state.get('investigation_id')}")
        logger.info(f"Issue: {state.get('issue_text', '')[:100]}...")

        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(state)

            logger.info("Investigation completed")
            if final_state.get("root_cause"):
                logger.info(f"Root cause: {final_state['root_cause'].description}")
            elif final_state.get("needs_human"):
                logger.info("Investigation requires human input")
            else:
                logger.warning("Investigation completed but no root cause determined")

            return final_state

        except Exception as e:
            logger.error(f"Workflow error: {str(e)}", exc_info=True)
            raise


# Factory function for easy workflow creation
def create_rca_workflow() -> RCAWorkflow:
    """Create a new RCA workflow instance"""
    return RCAWorkflow()

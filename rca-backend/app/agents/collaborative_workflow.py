"""
Collaborative Multi-Agent Workflow

This workflow implements an iterative, collaborative investigation pattern where:
1. Agents review current findings together
2. Agents propose next actions with reasoning
3. Coordinator facilitates decision-making
4. Selected action is executed
5. Loop continues until root cause found or human input needed

This mimics how support engineers actually investigate - iteratively,
with constant re-evaluation of what to check next based on findings.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.models import (
    InvestigationState,
    AgentMessage,
    AgentStatus,
    TimelineEvent,
    RootCause,
    Action,
    create_initial_state
)
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.identifier_agent import IdentifierAgent
from app.agents.hypothesis_agent import HypothesisAgent
from app.agents.synthesis_agent import SynthesisAgent

# Data agents
from app.agents.data_agents.tracking_api_agent import TrackingAPIAgent
from app.agents.data_agents.redshift_agent import RedshiftAgent
from app.agents.data_agents.callbacks_agent import CallbacksAgent
from app.agents.data_agents.super_api_agent import SuperAPIAgent
from app.agents.data_agents.jt_agent import JTAgent
from app.agents.data_agents.network_agent import NetworkAgent
from app.agents.data_agents.ocean_events_agent import OceanEventsAgent
from app.agents.data_agents.ocean_trace_agent import OceanTraceAgent
from app.agents.data_agents.confluence_agent import ConfluenceAgent
from app.agents.data_agents.slack_agent import SlackAgent
from app.agents.data_agents.jira_agent import JIRAAgent
from app.agents.data_agents.logs_agent import LogsAgent

logger = logging.getLogger(__name__)


class CollaborativeRCAWorkflow:
    """
    Collaborative multi-agent RCA workflow using iterative decision-making.

    Unlike the fixed pipeline approach, this workflow:
    - Lets agents decide what to investigate next
    - Shows agent reasoning and discussion
    - Adapts based on findings (skip irrelevant checks, dig deeper on promising leads)
    - Requests human input when stuck, not just at the end
    """

    def __init__(self):
        # Core agents
        self.coordinator = CoordinatorAgent()
        self.identifier_agent = IdentifierAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.synthesis_agent = SynthesisAgent()

        # Data agents (can be called based on coordinator decisions)
        self.data_agents = {
            "tracking": TrackingAPIAgent(),
            "redshift": RedshiftAgent(),  # Also known as DWH Agent
            "callbacks": CallbacksAgent(),
            "super_api": SuperAPIAgent(),
            "jt": JTAgent(),
            "network": NetworkAgent(),
            "ocean_events": OceanEventsAgent(),
            "ocean_trace": OceanTraceAgent(),
            "confluence": ConfluenceAgent(),
            "slack": SlackAgent(),
            "jira": JIRAAgent(),
            "logs": LogsAgent(),  # Service logs (integrations-worker, carrier-files-worker, tracking-service)
        }

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with collaborative decision-making"""
        workflow = StateGraph(InvestigationState)

        # Nodes
        workflow.add_node("extract_identifiers", self._extract_identifiers)
        workflow.add_node("initial_data_collection", self._initial_data_collection)
        workflow.add_node("coordinate", self._coordinate_iteration)
        workflow.add_node("execute_action", self._execute_selected_action)
        workflow.add_node("form_hypotheses", self._form_hypotheses)
        workflow.add_node("synthesize", self._synthesize_conclusion)
        workflow.add_node("request_human", self._request_human_input)

        # Entry point
        workflow.set_entry_point("extract_identifiers")

        # Flow
        workflow.add_edge("extract_identifiers", "initial_data_collection")
        workflow.add_edge("initial_data_collection", "coordinate")

        # Conditional routing from coordinator
        workflow.add_conditional_edges(
            "coordinate",
            self._route_after_coordination,
            {
                "execute": "execute_action",
                "conclude": "synthesize",  # Go directly to synthesis when concluding
                "human": "request_human",
                "done": END
            }
        )

        # After executing an action, form hypotheses
        workflow.add_edge("execute_action", "form_hypotheses")

        # After forming hypotheses, check if we should continue or conclude
        workflow.add_conditional_edges(
            "form_hypotheses",
            self._route_after_hypotheses,
            {
                "continue": "coordinate",
                "conclude": "synthesize"
            }
        )

        # Synthesis leads to end
        workflow.add_edge("synthesize", END)
        workflow.add_edge("request_human", END)

        return workflow.compile()

    async def _extract_identifiers(self, state: InvestigationState) -> Dict[str, Any]:
        """Extract identifiers from issue text"""
        logger.info("Extracting identifiers...")
        result = await self.identifier_agent.run(state)
        return result

    async def _initial_data_collection(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Do initial data collection to give agents something to work with.
        Always fetch basic info from Tracking API first.
        """
        messages = [AgentMessage(
            agent="Coordinator",
            message="Starting initial data collection. Let me get the basics first...",
            status=AgentStatus.RUNNING
        )]

        updates = {"agent_messages": messages}

        def merge_with_list_accumulation(base: Dict, new: Dict) -> Dict:
            """Merge dicts, extending lists instead of replacing them"""
            result = dict(base)
            for key, value in new.items():
                if key in result and isinstance(result[key], list) and isinstance(value, list):
                    result[key] = result[key] + value
                else:
                    result[key] = value
            return result

        # Always start with Tracking API
        try:
            tracking_result = await self.data_agents["tracking"].run(state)
            updates = merge_with_list_accumulation(updates, tracking_result)

            # Check if it's an ocean load - if so, get Super API config
            tracking_data = tracking_result.get("tracking_data", {})
            if tracking_data.get("exists"):
                raw = tracking_data.get("raw", {})
                loads = raw.get("loads", [])
                mode = (loads[0].get("loadMode") or loads[0].get("mode") or "").lower() if loads else ""
                if loads and mode == "ocean":
                    super_result = await self.data_agents["super_api"].run({**state, **updates})
                    updates = merge_with_list_accumulation(updates, super_result)

        except Exception as e:
            logger.error(f"Initial data collection error: {e}")
            updates["agent_messages"] = messages + [AgentMessage(
                agent="Tracking API Agent",
                message=f"Error during initial collection: {str(e)}",
                status=AgentStatus.FAILED
            )]

        return updates

    async def _coordinate_iteration(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Run one coordination iteration.
        The coordinator reviews state, collects proposals, and makes a decision.
        """
        logger.info(f"Coordination iteration {state.get('iteration_count', 0) + 1}")
        result = await self.coordinator.execute(state)
        return result

    def _route_after_hypotheses(self, state: InvestigationState) -> str:
        """Determine next step after forming hypotheses"""
        hypotheses = state.get("hypotheses", [])
        if hypotheses:
            top = hypotheses[0]
            threshold = state.get("confidence_threshold", 0.85)
            if top.confidence >= threshold:
                logger.info(f"High confidence hypothesis ({top.confidence:.0%}) - concluding")
                return "conclude"

        # Check iteration limit
        iteration = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 10)
        if iteration >= max_iterations:
            logger.info(f"Max iterations reached ({iteration}/{max_iterations})")
            return "conclude"  # Go to synthesis even if low confidence

        return "continue"

    def _route_after_coordination(self, state: InvestigationState) -> str:
        """Determine next step based on coordinator's decision"""
        decisions = state.get("decisions", [])
        if not decisions:
            return "execute"  # Default to executing if no decision

        latest_decision = decisions[-1]
        action = latest_decision.selected_action.action

        # PRIORITY 1: Check if we have high confidence hypothesis
        # This should take precedence over iteration limits
        hypotheses = state.get("hypotheses", [])
        if hypotheses:
            top = hypotheses[0]
            threshold = state.get("confidence_threshold", 0.85)
            if top.confidence >= threshold:
                logger.info(f"High confidence hypothesis found ({top.confidence:.0%}), concluding investigation")
                return "conclude"

        # PRIORITY 2: Check iteration limit
        iteration = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 10)
        if iteration >= max_iterations:
            logger.info(f"Max iterations ({max_iterations}) reached, requesting human input")
            return "human"

        # Route based on action
        if action == "conclude":
            return "conclude"
        elif action == "request_human":
            return "human"
        elif action in ["investigate", "query", "check", "verify", "continue"]:
            return "execute"
        else:
            return "execute"

    async def _execute_selected_action(self, state: InvestigationState) -> Dict[str, Any]:
        """Execute the action selected by the coordinator"""
        decisions = state.get("decisions", [])
        logger.info(f"Execute action - decisions count: {len(decisions)}")
        if not decisions:
            logger.warning("No decisions found in state")
            return {}

        decision = decisions[-1]
        logger.info(f"Latest decision type: {type(decision)}")
        action = decision.selected_action
        logger.info(f"Selected action: {action.action} on {action.target}")
        agent_name = action.agent.lower()
        target = action.target.lower()

        messages = [AgentMessage(
            agent="Coordinator",
            message=f"Executing: {agent_name} will {action.action} on {target}",
            status=AgentStatus.RUNNING
        )]

        updates = {"agent_messages": messages}

        # Map agent names to data agents
        agent_mapping = {
            "tracking": "tracking",
            "redshift": "redshift",
            "dwh": "redshift",  # Alias for Data Warehouse
            "callbacks": "callbacks",
            "super_api": "super_api",
            "superapi": "super_api",
            "datahub": "super_api",  # Alias for DataHub
            "jt": "jt",
            "network": "network",
            "company": "network",
            "ocean_events": "ocean_events",
            "ocean": "ocean_events",
            "ocean_trace": "ocean_trace",
            "confluence": "confluence",
            "slack": "slack",
            "jira": "jira",
            "logs": "logs",
            "service_logs": "logs",  # Alias for logs
        }

        # Handle "continue" action by executing all unchecked data sources
        logger.info(f"Action: {action.action}, Agent: {agent_name}, Target: {target}")
        if action.action == "continue" or (agent_name == "coordinator" and target == "investigation"):
            logger.info("Executing all unchecked data sources - matched continue condition")
            unchecked_agents = []
            if not state.get("redshift_data"):
                unchecked_agents.append("redshift")
            if not state.get("callbacks_data"):
                unchecked_agents.append("callbacks")
            if not state.get("super_api_data"):
                unchecked_agents.append("super_api")
            if not state.get("jt_data"):
                unchecked_agents.append("jt")
            if not state.get("network_data"):
                unchecked_agents.append("network")
            if not state.get("ocean_events_data"):
                unchecked_agents.append("ocean_events")
            if not state.get("ocean_trace_data"):
                unchecked_agents.append("ocean_trace")
            if not state.get("confluence_data"):
                unchecked_agents.append("confluence")
            if not state.get("slack_data"):
                unchecked_agents.append("slack")
            if not state.get("jira_data"):
                unchecked_agents.append("jira")
            if not state.get("logs_data"):
                unchecked_agents.append("logs")

            if unchecked_agents:
                # Execute all unchecked agents in parallel
                import asyncio
                tasks = []
                for agent_key in unchecked_agents:
                    if agent_key in self.data_agents:
                        tasks.append(self.data_agents[agent_key].run(state))

                start_time = datetime.now()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                # Merge all results
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Agent error: {result}")
                        continue
                    if isinstance(result, dict):
                        updates = {**updates, **result}

                updates["agent_messages"] = messages + [AgentMessage(
                    agent="Coordinator",
                    message=f"Executed {len(unchecked_agents)} data agents in parallel: {', '.join(unchecked_agents)}",
                    status=AgentStatus.COMPLETED
                )]
                updates["timeline_events"] = [TimelineEvent(
                    timestamp=datetime.now(),
                    agent="Coordinator",
                    action=f"Parallel execution of {len(unchecked_agents)} agents",
                    duration_ms=duration,
                    status=AgentStatus.COMPLETED
                )]
                return updates
            else:
                updates["agent_messages"] = messages + [AgentMessage(
                    agent="Coordinator",
                    message="All data sources have been checked",
                    status=AgentStatus.COMPLETED
                )]
                return updates

        # Find the right agent to execute
        agent_key = agent_mapping.get(agent_name)
        if not agent_key:
            # Try to infer from target
            if "validation" in target or "redshift" in target:
                agent_key = "redshift"
            elif "callback" in target:
                agent_key = "callbacks"
            elif "tracking" in target or "load" in target:
                agent_key = "tracking"
            elif "subscription" in target or "config" in target:
                agent_key = "super_api"
            elif "jt" in target or "scraping" in target:
                agent_key = "jt"
            elif "ocean" in target or "event" in target:
                agent_key = "ocean_events"

        if agent_key and agent_key in self.data_agents:
            try:
                start_time = datetime.now()
                result = await self.data_agents[agent_key].run(state)
                duration = int((datetime.now() - start_time).total_seconds() * 1000)

                updates = {**updates, **result}
                updates["timeline_events"] = [TimelineEvent(
                    timestamp=datetime.now(),
                    agent=f"{agent_key.title()} Agent",
                    action=f"Executed {action.action} on {target}",
                    duration_ms=duration,
                    status=AgentStatus.COMPLETED
                )]

            except Exception as e:
                logger.error(f"Error executing {agent_key}: {e}")
                updates["agent_messages"] = messages + [AgentMessage(
                    agent=f"{agent_key.title()} Agent",
                    message=f"Error: {str(e)}",
                    status=AgentStatus.FAILED
                )]
        else:
            logger.warning(f"Unknown agent: {agent_name}")
            updates["agent_messages"] = messages + [AgentMessage(
                agent="Coordinator",
                message=f"Could not find agent for: {agent_name}",
                status=AgentStatus.FAILED
            )]

        return updates

    async def _form_hypotheses(self, state: InvestigationState) -> Dict[str, Any]:
        """Form or update hypotheses based on current evidence"""
        result = await self.hypothesis_agent.run(state)
        return result

    async def _synthesize_conclusion(self, state: InvestigationState) -> Dict[str, Any]:
        """Synthesize final root cause from hypotheses"""
        result = await self.synthesis_agent.run(state)
        return result

    async def _request_human_input(self, state: InvestigationState) -> Dict[str, Any]:
        """Request human input when stuck"""
        hypotheses = state.get("hypotheses", [])

        if hypotheses:
            top_hypotheses = hypotheses[:3]
            hypothesis_text = "\n".join([
                f"- {h.description} ({h.confidence:.0%})"
                for h in top_hypotheses
            ])
            question = f"""The investigation has examined multiple data sources but cannot reach a confident conclusion.

Current hypotheses:
{hypothesis_text}

What additional context can you provide? Or which hypothesis seems most likely based on your experience?"""
        else:
            question = "The investigation could not form any hypotheses. Please provide additional context about the issue."

        return {
            "needs_human": True,
            "human_question": question,
            "investigation_phase": "stuck",
            "agent_messages": [AgentMessage(
                agent="Coordinator",
                message="Requesting human input to continue investigation.",
                status=AgentStatus.COMPLETED
            )]
        }


def create_collaborative_workflow() -> CollaborativeRCAWorkflow:
    """Factory function to create a collaborative workflow instance"""
    return CollaborativeRCAWorkflow()

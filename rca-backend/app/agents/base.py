"""
Base Agent Class
Common functionality for all RCA agents with Claude Code-style verbose output
"""
import logging
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

from app.models import (
    InvestigationState,
    AgentStatus,
    AgentMessage,
    AgentDiscussion,
    TimelineEvent,
    Query,
    add_agent_message,
    add_timeline_event,
    add_query
)

logger = logging.getLogger(__name__)


# Agent Personas - Each agent has a distinct personality and expertise
AGENT_PERSONAS = {
    "Tracking API Agent": {
        "role": "Customer Data Specialist",
        "expertise": "FourKites Tracking API, load visibility, customer-facing data",
        "thinking_style": "I focus on what the customer sees - the load's current state, status, and tracking information.",
    },
    "Redshift Agent": {
        "role": "Data Warehouse Analyst",
        "expertise": "Historical data, validation errors, load creation failures",
        "thinking_style": "I dig into the data warehouse to find historical patterns and validation issues.",
    },
    "Callbacks Agent": {
        "role": "Integration Specialist",
        "expertise": "Callback delivery, API integrations, error patterns",
        "thinking_style": "I analyze callback delivery and look for integration issues with external systems.",
    },
    "Super API Agent": {
        "role": "Configuration Expert",
        "expertise": "Internal tracking configuration, subscription management, DataHub",
        "thinking_style": "I examine the internal configuration to ensure tracking is properly set up.",
    },
    "JT Agent": {
        "role": "RPA Scraping Analyst",
        "expertise": "Just Transform, carrier portal scraping, data extraction",
        "thinking_style": "I investigate the RPA scraping pipeline to find extraction issues.",
    },
    "Ocean Events Agent": {
        "role": "Ocean Logistics Specialist",
        "expertise": "MMCUW logs, ocean container events, vessel tracking",
        "thinking_style": "I analyze ocean-specific events and container milestones.",
    },
    "Ocean Trace Agent": {
        "role": "Subscription Tracker",
        "expertise": "Ocean subscriptions, DataHub traces, carrier data",
        "thinking_style": "I trace ocean subscriptions and verify carrier data flow.",
    },
    "Confluence Agent": {
        "role": "Documentation Researcher",
        "expertise": "Internal documentation, troubleshooting guides, known issues",
        "thinking_style": "I search our knowledge base for relevant documentation and past solutions.",
    },
    "Slack Agent": {
        "role": "Communication Analyst",
        "expertise": "Team discussions, incident history, support threads",
        "thinking_style": "I look through team communications for similar issues and resolutions.",
    },
    "JIRA Agent": {
        "role": "Issue Tracker",
        "expertise": "Bug reports, feature requests, known issues",
        "thinking_style": "I search for related tickets and known issues in our tracking system.",
    },
    "Identifier Agent": {
        "role": "Data Extractor",
        "expertise": "Pattern recognition, identifier extraction, text parsing",
        "thinking_style": "I extract key identifiers like tracking IDs, load numbers, and containers from text.",
    },
    "Coordinator Agent": {
        "role": "Investigation Lead",
        "expertise": "Orchestration, decision making, prioritization",
        "thinking_style": "I coordinate the investigation and decide what to check next based on findings.",
    },
    "Hypothesis Agent": {
        "role": "Reasoning Specialist",
        "expertise": "Hypothesis formation, evidence evaluation, Bayesian reasoning",
        "thinking_style": "I form hypotheses based on evidence and update confidence as new data arrives.",
    },
    "Synthesis Agent": {
        "role": "Root Cause Determiner",
        "expertise": "Pattern synthesis, conclusion drawing, action recommendations",
        "thinking_style": "I synthesize all findings to determine the most likely root cause.",
    },
}


class BaseAgent(ABC):
    """Base class for all RCA agents with verbose output like Claude Code"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name.lower().replace(' ', '_')}")
        self.persona = AGENT_PERSONAS.get(name, {
            "role": "Investigation Agent",
            "expertise": "General investigation",
            "thinking_style": "I analyze available data to find relevant information.",
        })

    @abstractmethod
    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """Execute the agent's task"""
        pass

    def _create_discussion(
        self,
        message: str,
        message_type: str = "observation",
        references: Optional[List[str]] = None
    ) -> Dict:
        """Create an agent discussion entry for streaming"""
        disc = AgentDiscussion(
            agent=self.name,
            message=message,
            message_type=message_type,
            references=references or [],
            timestamp=datetime.now()
        )
        return {"agent_discussions": [disc]}

    def observe(self, observation: str) -> Dict:
        """Log an observation about the current state"""
        return self._create_discussion(f"[Observation] {observation}", "observation")

    def think(self, thought: str) -> Dict:
        """Log the agent's thinking/reasoning"""
        return self._create_discussion(f"[Thinking] {thought}", "proposal")

    def plan(self, plan: str) -> Dict:
        """Log what the agent plans to do"""
        return self._create_discussion(f"[Plan] {plan}", "proposal")

    def execute_action(self, action: str) -> Dict:
        """Log an action being executed"""
        msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] {action}",
            status=AgentStatus.RUNNING,
            metadata={"type": "action"}
        )
        return {"agent_messages": [msg]}

    def report_finding(self, finding: str) -> Dict:
        """Report a finding/result"""
        return self._create_discussion(f"[Finding] {finding}", "observation")

    async def run(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Run the agent with verbose Claude Code-style output
        """
        start_time = time.time()
        self.logger.info(f"{self.name} starting execution")

        updates = {}

        # Introduction with persona
        intro_msg = AgentMessage(
            agent=self.name,
            message=f"[{self.persona['role']}] Starting analysis...",
            status=AgentStatus.RUNNING,
            metadata={"type": "start", "expertise": self.persona["expertise"]}
        )
        updates["agent_messages"] = [intro_msg]

        # Add thinking about what we're going to do
        thinking_disc = AgentDiscussion(
            agent=self.name,
            message=f"[Thinking] {self.persona['thinking_style']}",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"] = [thinking_disc]

        updates.update(add_timeline_event(
            state,
            self.name,
            f"Started {self.name.lower()}",
            status=AgentStatus.RUNNING
        ))

        try:
            # Execute agent logic - this will add more messages/discussions
            result = await self.execute(state)

            # Merge results
            # Handle list accumulation properly
            for key, value in result.items():
                if key in updates and isinstance(updates[key], list) and isinstance(value, list):
                    updates[key] = updates[key] + value
                else:
                    updates[key] = value

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Add completion message
            success_msg = result.get("_message", "Completed successfully")
            completion_msg = AgentMessage(
                agent=self.name,
                message=f"[Complete] {success_msg} ({duration_ms}ms)",
                status=AgentStatus.COMPLETED,
                metadata={"type": "complete", "duration_ms": duration_ms}
            )
            if "agent_messages" in updates:
                updates["agent_messages"].append(completion_msg)
            else:
                updates["agent_messages"] = [completion_msg]

            updates.update(add_timeline_event(
                state,
                self.name,
                f"Completed {self.name.lower()}",
                duration_ms=duration_ms,
                result_summary=success_msg,
                status=AgentStatus.COMPLETED
            ))

            # Remove internal metadata
            updates.pop("_message", None)

            self.logger.info(f"{self.name} completed in {duration_ms}ms")
            return updates

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Error: {str(e)}"

            self.logger.error(f"{self.name} failed: {str(e)}", exc_info=True)

            error_message = AgentMessage(
                agent=self.name,
                message=f"[Error] {error_msg}",
                status=AgentStatus.FAILED,
                metadata={"type": "error", "duration_ms": duration_ms}
            )
            if "agent_messages" in updates:
                updates["agent_messages"].append(error_message)
            else:
                updates["agent_messages"] = [error_message]

            updates.update(add_timeline_event(
                state,
                self.name,
                f"Failed: {str(e)}",
                duration_ms=duration_ms,
                status=AgentStatus.FAILED
            ))

            return updates

    def log_query(
        self,
        state: InvestigationState,
        source: str,
        query: str,
        result_count: Optional[int] = None,
        raw_result: Optional[Any] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ) -> Dict:
        """Helper to log an executed query with verbose output"""
        # Create the query record
        query_update = add_query(state, source, query, result_count, raw_result, duration_ms, error)

        # Also add a discussion about the query
        if error:
            msg = f"[Query Failed] {source}: {query}\nError: {error}"
        else:
            result_info = f"{result_count} results" if result_count is not None else "completed"
            duration_info = f" in {duration_ms}ms" if duration_ms else ""
            msg = f"[Query Executed] {source}: {query}\nResult: {result_info}{duration_info}"

        disc = AgentDiscussion(
            agent=self.name,
            message=msg,
            message_type="observation",
            timestamp=datetime.now()
        )

        # Merge the updates
        if "agent_discussions" in query_update:
            query_update["agent_discussions"].append(disc)
        else:
            query_update["agent_discussions"] = [disc]

        return query_update

    def create_success_message(self, summary: str) -> Dict:
        """Helper to create success message for state update"""
        return {"_message": summary}

    def extract_identifier(self, state: InvestigationState, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Safely extract identifier from state"""
        return state.get("identifiers", {}).get(key, default)

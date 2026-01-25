"""
Coordinator Agent - Facilitates multi-agent collaboration and decision-making

This agent orchestrates the collaborative investigation process by:
1. Asking agents to review current findings
2. Collecting proposed next actions from each agent
3. Facilitating discussion about priorities
4. Making decisions on what to investigate next
5. Determining when to conclude or request human input
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.agents.base import BaseAgent
from app.models import (
    InvestigationState,
    AgentMessage,
    AgentStatus,
    AgentDiscussion,
    ProposedAction,
    CollaborativeDecision,
    RootCauseCategory
)
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Coordinates multi-agent investigation through collaborative decision-making.

    Acts as a facilitator that:
    - Summarizes current state for all agents
    - Collects proposals from agents
    - Facilitates voting/discussion
    - Makes final decisions on next steps
    - Determines when to conclude or ask for human help
    """

    def __init__(self):
        super().__init__("Coordinator")
        self.llm = LLMClient()

    async def summarize_state(self, state: InvestigationState) -> str:
        """Create a summary of current investigation state for agents to review"""
        summary_parts = []

        # Issue and identifiers
        summary_parts.append(f"**Issue**: {state.get('issue_text', 'Unknown')}")
        identifiers = state.get('identifiers', {})
        if identifiers:
            summary_parts.append(f"**Identifiers**: {identifiers}")

        # What we know so far
        tracking_data = state.get('tracking_data', {})
        if tracking_data.get('exists'):
            raw = tracking_data.get('raw', {})
            loads = raw.get('loads', [{}])
            if loads:
                load = loads[0]
                summary_parts.append(f"**Load Found**: {load.get('loadNumber')} | Mode: {load.get('loadMode')} | Status: {load.get('status')}")

        # Validation errors
        redshift_data = state.get('redshift_data', {})
        if redshift_data.get('validation_attempts'):
            failed = redshift_data.get('failed_attempts', 0)
            error = redshift_data.get('latest_error') or ''
            error_preview = error[:100] if error else 'No error message'
            summary_parts.append(f"**Validation Errors**: {failed} failures - {error_preview}...")

        # Callbacks data
        callbacks_data = state.get('callbacks_data', {})
        if callbacks_data.get('total_callbacks'):
            total = callbacks_data.get('total_callbacks', 0)
            failed = callbacks_data.get('failed', 0)
            summary_parts.append(f"**Callbacks**: {total} total, {failed} failed")

        # Current hypotheses
        hypotheses = state.get('hypotheses', [])
        if hypotheses:
            top = hypotheses[0] if hypotheses else None
            if top:
                summary_parts.append(f"**Top Hypothesis**: {top.description} ({top.confidence:.0%} confidence)")

        # What hasn't been checked yet
        unchecked = []
        if not state.get('tracking_data', {}).get('exists') and not state.get('tracking_data', {}).get('error'):
            unchecked.append("Tracking API")
        if not state.get('redshift_data'):
            unchecked.append("Redshift validation")
        if not state.get('callbacks_data'):
            unchecked.append("Callbacks history")
        if not state.get('super_api_data'):
            unchecked.append("Super API config")
        if not state.get('jt_data'):
            unchecked.append("JT scraping history")
        if not state.get('confluence_data'):
            unchecked.append("Confluence docs")
        if not state.get('slack_data'):
            unchecked.append("Slack history")
        if not state.get('jira_data'):
            unchecked.append("JIRA issues")
        if unchecked:
            summary_parts.append(f"**Not yet checked**: {', '.join(unchecked)}")

        return "\n".join(summary_parts)

    async def collect_proposals(
        self,
        state: InvestigationState,
        available_agents: List[str]
    ) -> List[ProposedAction]:
        """
        Use LLM to generate proposals from each agent's perspective.

        This simulates multiple agents proposing actions based on the current state.
        """
        state_summary = await self.summarize_state(state)

        prompt = f"""You are coordinating a multi-agent RCA (Root Cause Analysis) investigation.

Current State:
{state_summary}

Available agents that can investigate:
- tracking: Query FourKites Tracking API for load details
- redshift: Query Redshift for validation errors and load history
- callbacks: Query Athena for webhook callback history
- super_api: Query DataHub for internal tracking configuration
- jt: Query Just Transform for RPA scraping history
- ocean_events: Query ClickHouse for ocean tracking events

Based on the current findings, generate 2-4 proposed next actions. Each action should:
1. Come from a specific agent's perspective
2. Have clear reasoning based on current evidence
3. Have a priority (1-10, higher = more important)
4. Consider dependencies (what needs to happen first)

Respond in this exact JSON format:
{{
  "proposals": [
    {{
      "agent": "agent_name",
      "action": "action_type",
      "target": "what to investigate",
      "reasoning": "why this is important based on current findings",
      "priority": 8
    }}
  ],
  "discussion": [
    {{
      "agent": "agent_name",
      "message": "observation or comment about the investigation",
      "type": "observation|proposal|agreement|question"
    }}
  ]
}}

Focus on actions that will help determine the root cause. If we already have high-confidence findings, propose concluding."""

        try:
            response = await self.llm.generate(prompt)
            response_text = response.text.strip()

            # Clean up markdown if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            import json
            result = json.loads(response_text.strip())

            proposals = []
            for p in result.get("proposals", []):
                proposals.append(ProposedAction(
                    agent=p.get("agent", "unknown"),
                    action=p.get("action", "investigate"),
                    target=p.get("target", "unknown"),
                    reasoning=p.get("reasoning", ""),
                    priority=int(p.get("priority", 5)),
                    estimated_value=p.get("priority", 5) / 10.0
                ))

            return proposals

        except Exception as e:
            logger.error(f"Error collecting proposals: {e}")
            # Return a default proposal
            return [ProposedAction(
                agent="coordinator",
                action="continue",
                target="investigation",
                reasoning="Unable to generate specific proposals, continuing with standard checks",
                priority=5
            )]

    async def facilitate_decision(
        self,
        state: InvestigationState,
        proposals: List[ProposedAction]
    ) -> CollaborativeDecision:
        """
        Facilitate a decision based on proposals.

        Uses LLM to evaluate proposals and make a decision.
        """
        if not proposals:
            return CollaborativeDecision(
                selected_action=ProposedAction(
                    agent="coordinator",
                    action="conclude",
                    target="investigation",
                    reasoning="No proposals available",
                    priority=1
                ),
                votes={},
                rationale="No proposals to evaluate"
            )

        # Sort by priority
        sorted_proposals = sorted(proposals, key=lambda p: p.priority, reverse=True)

        # Check if we should conclude
        hypotheses = state.get('hypotheses', [])
        if hypotheses:
            top_hypothesis = hypotheses[0]
            confidence_threshold = state.get('confidence_threshold', 0.85)

            if top_hypothesis.confidence >= confidence_threshold:
                return CollaborativeDecision(
                    selected_action=ProposedAction(
                        agent="coordinator",
                        action="conclude",
                        target="root_cause",
                        reasoning=f"Top hypothesis has {top_hypothesis.confidence:.0%} confidence, exceeding threshold of {confidence_threshold:.0%}",
                        priority=10
                    ),
                    votes={"coordinator": True, "hypothesis_agent": True},
                    rationale=f"Confidence threshold met. Root cause: {top_hypothesis.description}",
                    alternative_actions=sorted_proposals[:3]
                )

        # Check iteration limit
        iteration = state.get('iteration_count', 0)
        max_iterations = state.get('max_iterations', 10)
        if iteration >= max_iterations:
            return CollaborativeDecision(
                selected_action=ProposedAction(
                    agent="coordinator",
                    action="request_human",
                    target="investigation",
                    reasoning=f"Reached maximum iterations ({max_iterations}) without confident conclusion",
                    priority=10
                ),
                votes={"coordinator": True},
                rationale="Maximum iterations reached, requesting human input"
            )

        # Select highest priority proposal
        selected = sorted_proposals[0]

        return CollaborativeDecision(
            selected_action=selected,
            votes={selected.agent: True, "coordinator": True},
            rationale=f"Selected based on priority ({selected.priority}/10) and reasoning: {selected.reasoning}",
            alternative_actions=sorted_proposals[1:4]
        )

    async def generate_discussion(
        self,
        state: InvestigationState,
        decision: CollaborativeDecision
    ) -> List[AgentDiscussion]:
        """Generate agent discussion about the decision"""
        discussions = []

        # Coordinator announces the decision
        discussions.append(AgentDiscussion(
            agent="Coordinator",
            message=f"Decision: {decision.selected_action.action} on {decision.selected_action.target}. Rationale: {decision.rationale}",
            message_type="decision"
        ))

        # Selected agent acknowledges
        discussions.append(AgentDiscussion(
            agent=decision.selected_action.agent.title() + " Agent",
            message=f"Acknowledged. {decision.selected_action.reasoning}",
            message_type="agreement"
        ))

        # If there are alternatives, mention them
        if decision.alternative_actions:
            alt = decision.alternative_actions[0]
            discussions.append(AgentDiscussion(
                agent=alt.agent.title() + " Agent",
                message=f"Alternative considered: {alt.action} on {alt.target} (priority: {alt.priority}/10)",
                message_type="observation"
            ))

        return discussions

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Main coordination loop for one iteration.

        Returns state updates including:
        - New agent discussions
        - Decision made
        - Next action to take
        - Updated investigation phase
        """
        iteration = state.get('iteration_count', 0) + 1

        # Create opening discussion
        discussions = [AgentDiscussion(
            agent="Coordinator",
            message=f"Starting iteration {iteration}. Let me review current findings...",
            message_type="observation"
        )]

        # Summarize state
        summary = await self.summarize_state(state)
        discussions.append(AgentDiscussion(
            agent="Coordinator",
            message=f"Current status:\n{summary}",
            message_type="observation"
        ))

        # Collect proposals from agents
        available_agents = state.get('available_agents', [])
        proposals = await self.collect_proposals(state, available_agents)

        # Add proposals to discussion
        for proposal in proposals:
            discussions.append(AgentDiscussion(
                agent=proposal.agent.title() + " Agent",
                message=f"I propose: {proposal.action} on {proposal.target}. Reason: {proposal.reasoning}",
                message_type="proposal"
            ))

        # Make decision
        decision = await self.facilitate_decision(state, proposals)

        # Generate discussion about decision
        decision_discussion = await self.generate_discussion(state, decision)
        discussions.extend(decision_discussion)

        # Determine next phase
        next_phase = state.get('investigation_phase', 'gathering')
        if decision.selected_action.action == "conclude":
            next_phase = "concluding"
        elif decision.selected_action.action == "request_human":
            next_phase = "stuck"
        elif iteration > 3:
            next_phase = "analyzing"

        # Convert discussions to agent messages for UI
        agent_messages = []
        for d in discussions:
            agent_messages.append(AgentMessage(
                agent=d.agent,
                message=d.message,
                status=AgentStatus.COMPLETED,
                metadata={"type": d.message_type}
            ))

        return {
            "agent_discussions": discussions,
            "proposed_actions": proposals,
            "decisions": [decision],
            "iteration_count": iteration,
            "investigation_phase": next_phase,
            "current_focus": decision.selected_action.target,
            "agent_messages": agent_messages,
            "_decision": decision,
            "_message": f"Iteration {iteration}: {decision.selected_action.action} on {decision.selected_action.target}"
        }

"""
Hypothesis Engine for adaptive RCA investigation.

Forms and evaluates hypotheses using LLM reasoning, enabling
dynamic investigation paths instead of fixed step sequences.
"""

import logging
from typing import Any, Dict, List, Optional

from core.models.hypothesis import Hypothesis, AgentAction
from core.models.evidence import Evidence
from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class HypothesisEngine:
    """
    Form and evaluate hypotheses using LLM reasoning.

    This engine enables adaptive investigation by:
    1. Forming initial hypotheses based on available data
    2. Updating hypothesis confidence based on new evidence
    3. Deciding next actions for sub-agents
    """

    KNOWN_ROOT_CAUSES = [
        # Network/Configuration
        "network_relationship_missing",
        "network_relationship_inactive",
        "carrier_config_missing",

        # JustTransform/ELD
        "jt_scraping_error",
        "jt_formatting_error",
        "eld_integration_error",

        # Carrier Issues
        "carrier_portal_down",
        "carrier_data_incorrect",
        "carrier_file_processing_error",
        "carrier_file_malformed",

        # TL/FTL Specific
        "asset_assignment_failure",
        "truck_trailer_missing",
        "location_processing_error",
        "location_validation_rejected",
        "file_ingestion_error",
        "data_mapping_error",
        "geocoding_failure",

        # System/Platform
        "subscription_inactive",
        "identifier_mismatch",
        "system_processing_error",
    ]

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def form_initial_hypotheses(
        self,
        identifiers: Dict[str, Any],
        initial_evidence: List[Evidence]
    ) -> List[Hypothesis]:
        """
        Use LLM to form 3-5 hypotheses based on initial data.

        Args:
            identifiers: Known identifiers (load_id, carrier, etc.)
            initial_evidence: Evidence from initial platform check

        Returns:
            List of Hypothesis objects ranked by initial confidence
        """
        # Format identifiers
        id_text = "\n".join([
            f"- {k}: {v}"
            for k, v in identifiers.items()
            if v is not None
        ])

        # Format evidence
        evidence_text = "\n".join([
            f"- {e.finding} [source={e.source.value}]"
            for e in initial_evidence
        ]) if initial_evidence else "No initial evidence collected yet."

        prompt = f"""Given this shipment tracking issue, form 3-5 hypotheses about the root cause.

AVAILABLE IDENTIFIERS:
{id_text}

INITIAL EVIDENCE:
{evidence_text}

KNOWN ROOT CAUSE TYPES (Network/Config):
- network_relationship_missing: Shipper-carrier relationship not set up
- network_relationship_inactive: Relationship exists but inactive
- carrier_config_missing: Carrier configuration missing or incorrect

KNOWN ROOT CAUSE TYPES (JT/ELD):
- jt_scraping_error: JustTransform RPA scraping failed
- jt_formatting_error: JT data transformation error
- eld_integration_error: ELD provider integration failure (KeepTruckin, Samsara, etc.)

KNOWN ROOT CAUSE TYPES (Carrier Issues):
- carrier_portal_down: Carrier tracking portal unavailable
- carrier_data_incorrect: Carrier shows wrong data
- carrier_file_processing_error: Carrier file failed to process
- carrier_file_malformed: Carrier file format incorrect/malformed

KNOWN ROOT CAUSE TYPES (TL/FTL Processing - see TL_FTL_PROCESSING_KNOWLEDGE.md):
- asset_assignment_failure: Truck/Trailer assignment failed (PROCESS_TRUCK_RECORD)
- truck_trailer_missing: TruckNumber or TrailerNumber missing from carrier data
- location_processing_error: Location data processing failed (PROCESS_TRUCK_LOCATION)
- location_validation_rejected: Location rejected by validation (PROCESS_NEW_LOCATION)
- file_ingestion_error: Carrier file ingestion failed (ProcessSuperFilesTask)
- data_mapping_error: Data mapping failed (PROCESS_SUPER_RECORD)
- geocoding_failure: Geocoding or timezone conversion error

KNOWN ROOT CAUSE TYPES (System):
- subscription_inactive: Tracking subscription not active
- identifier_mismatch: Container/booking doesn't match carrier
- system_processing_error: Internal processing error

TL/FTL PROCESSING FLOW (for context):
1. File Ingestion: ProcessSuperFilesTask (carrier-files-worker)
2. Data Mapping: PROCESS_SUPER_RECORD (carrier-files-worker)
3. Asset Assignment: PROCESS_TRUCK_RECORD (carrier-files-worker)
4. Location Processing: PROCESS_TRUCK_LOCATION (global-worker-ex)
5. Location Validation: PROCESS_NEW_LOCATION (location-worker)
6. ELD Integration: FETCH_ELD_LOCATION → PROCESS_ELD_LOCATION

If status is "Awaiting Tracking Info" for TL/FTL, consider:
- Asset assignment failure (no truck/trailer info)
- File processing error (carrier file not processed)
- Location processing error (no checkcalls created)
- ELD integration error (ELD provider not sending data)

For each hypothesis, provide:
1. description: What you think is wrong
2. root_cause_type: One of the types above
3. confidence: Initial probability (0.0-1.0, should sum to ~1.0)
4. suggested_tasks: What data sources to query to test this

Return JSON array:
[
  {{
    "description": "<hypothesis description>",
    "root_cause_type": "<type>",
    "confidence": <0.0-1.0>,
    "suggested_tasks": [
      {{"source": "<client_name>", "method": "<method_name>", "reason": "<why>"}}
    ]
  }}
]
"""

        response = self.llm.reason_json(prompt)

        # Parse response into Hypothesis objects
        hypotheses = []

        if isinstance(response, list):
            for h_data in response:
                try:
                    hypothesis = Hypothesis(
                        description=h_data.get("description", "Unknown hypothesis"),
                        root_cause_type=h_data.get("root_cause_type", "unknown"),
                        confidence=float(h_data.get("confidence", 0.5)),
                        suggested_tasks=h_data.get("suggested_tasks", [])
                    )
                    hypotheses.append(hypothesis)
                except Exception as e:
                    logger.warning(f"Failed to parse hypothesis: {e}")

        # If parsing failed, create default hypotheses
        if not hypotheses:
            logger.warning("LLM did not return valid hypotheses, using defaults")
            hypotheses = self._create_default_hypotheses(identifiers)

        # Sort by confidence (highest first)
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        logger.info(f"Formed {len(hypotheses)} hypotheses:")
        for h in hypotheses:
            logger.info(f"  - {h.description} (confidence={h.confidence:.2f})")

        return hypotheses

    def _create_default_hypotheses(self, identifiers: Dict[str, Any]) -> List[Hypothesis]:
        """Create default hypotheses when LLM fails"""
        defaults = [
            Hypothesis(
                description="Network relationship between shipper and carrier may be missing",
                root_cause_type="network_relationship_missing",
                confidence=0.4,
                suggested_tasks=[
                    {"source": "company_api", "method": "get_company_relationship", "reason": "Check if relationship exists"}
                ]
            ),
            Hypothesis(
                description="JustTransform scraping may have failed or returned incorrect data",
                root_cause_type="jt_scraping_error",
                confidence=0.3,
                suggested_tasks=[
                    {"source": "justtransform", "method": "get_subscription_history", "reason": "Check scraping history"}
                ]
            ),
            Hypothesis(
                description="Tracking subscription may be inactive or misconfigured",
                root_cause_type="subscription_inactive",
                confidence=0.2,
                suggested_tasks=[
                    {"source": "super_api", "method": "get_tracking_config", "reason": "Check subscription status"}
                ]
            ),
            Hypothesis(
                description="Carrier portal may be down or showing incorrect data",
                root_cause_type="carrier_portal_down",
                confidence=0.1,
                suggested_tasks=[
                    {"source": "tracking_api", "method": "get_tracking_by_id", "reason": "Check carrier status"}
                ]
            ),
        ]
        return defaults

    async def update_hypothesis(
        self,
        hypothesis: Hypothesis,
        new_evidence: Evidence
    ) -> Hypothesis:
        """
        Update hypothesis confidence based on new evidence.

        Args:
            hypothesis: Current hypothesis
            new_evidence: New evidence to evaluate

        Returns:
            Updated hypothesis with adjusted confidence
        """
        prompt = f"""Evaluate how this new evidence affects the hypothesis:

HYPOTHESIS:
- Description: {hypothesis.description}
- Type: {hypothesis.root_cause_type}
- Current confidence: {hypothesis.confidence:.2f}

NEW EVIDENCE:
- Finding: {new_evidence.finding}
- Source: {new_evidence.source.value}
- Raw data summary: {str(new_evidence.raw_data)[:500]}

Does this evidence:
1. SUPPORT the hypothesis (increase confidence)?
2. CONTRADICT the hypothesis (decrease confidence)?
3. Is IRRELEVANT to this hypothesis?

Return JSON:
{{
  "verdict": "support|contradict|irrelevant",
  "new_confidence": <0.0-1.0>,
  "reasoning": "<why this evidence affects the hypothesis this way>"
}}
"""

        response = self.llm.reason_json(prompt)

        # Get new confidence
        new_confidence = float(response.get("new_confidence", hypothesis.confidence))
        verdict = response.get("verdict", "irrelevant")
        reasoning = response.get("reasoning", "")

        logger.info(
            f"Hypothesis '{hypothesis.description[:50]}...' "
            f"evidence verdict: {verdict}, "
            f"confidence: {hypothesis.confidence:.2f} -> {new_confidence:.2f}"
        )

        # Update hypothesis
        supports = verdict == "support"
        hypothesis.update_confidence(new_confidence, new_evidence.id, supports)

        return hypothesis

    async def decide_next_action(
        self,
        hypothesis: Hypothesis,
        evidence_so_far: List[Evidence],
        available_clients: List[str]
    ) -> AgentAction:
        """
        Decide what action a sub-agent should take next.

        Args:
            hypothesis: The hypothesis being tested
            evidence_so_far: Evidence collected so far
            available_clients: List of available data source client names

        Returns:
            AgentAction describing what to do next
        """
        # Format evidence
        evidence_text = "\n".join([
            f"- {e.finding} [source={e.source.value}]"
            for e in evidence_so_far
        ]) if evidence_so_far else "No evidence collected yet."

        # Format suggested tasks
        suggested = hypothesis.suggested_tasks
        suggested_text = "\n".join([
            f"- {t.get('source')}.{t.get('method')}: {t.get('reason')}"
            for t in suggested
        ]) if suggested else "No specific tasks suggested."

        prompt = f"""Decide the next action for testing this hypothesis:

HYPOTHESIS:
- Description: {hypothesis.description}
- Type: {hypothesis.root_cause_type}
- Current confidence: {hypothesis.confidence:.2f}
- Status: {hypothesis.status}

EVIDENCE COLLECTED SO FAR:
{evidence_text}

SUGGESTED TASKS (not yet done):
{suggested_text}

AVAILABLE DATA SOURCES - YOU MUST USE THESE EXACT STRINGS:
| source | method | purpose |
|--------|--------|---------|
| tracking_api | get_tracking_by_id | Get load status and carrier info |
| company_api | get_company_relationship | Check if shipper-carrier network exists |
| redshift | find_similar_stuck_loads | Find similar loads with same issue |
| super_api | get_tracking_config | Check tracking subscription config |
| clickhouse | get_ocean_processing_logs | Check processing logs |

CRITICAL RULES:
1. "source" MUST BE EXACTLY ONE OF: tracking_api, company_api, redshift, super_api, clickhouse
2. DO NOT use: "Carrier Portal", "Network Database", "justtransform" or any other names
3. DO NOT include "params" - system fills them automatically
4. If you cannot find a relevant data source, use "conclude"

What should I do next?

Options:
1. query_data_source: Query a data source for more evidence
2. revisit: Query the same source with different parameters
3. spawn_child: Create a more specific sub-hypothesis to investigate
4. conclude: Enough evidence, conclude investigation of this hypothesis

Return JSON (DO NOT include params field):
{{
  "type": "query_data_source|revisit|spawn_child|conclude",
  "source": "<client_name if querying>",
  "method": "<method_name if querying>",
  "child_hypothesis": "<new hypothesis description if spawning>",
  "reason": "<why this action>"
}}
"""

        response = self.llm.reason_json(prompt)

        # Parse into AgentAction
        action_type = response.get("type", "conclude")

        # Valid sources - reject any others
        valid_sources = {"tracking_api", "company_api", "redshift", "super_api", "clickhouse"}
        source = response.get("source", "")

        # If LLM returned invalid source, force conclude
        if action_type in ["query_data_source", "revisit"] and source not in valid_sources:
            logger.warning(f"LLM returned invalid source '{source}', forcing conclude")
            return AgentAction.conclude(
                reason=f"No valid data source for this hypothesis (attempted: {source})"
            )

        if action_type == "query_data_source":
            return AgentAction.query(
                source=source,
                method=response.get("method", ""),
                params={},  # Params will be filled from identifiers by sub-agent
                reason=response.get("reason", "")
            )
        elif action_type == "revisit":
            return AgentAction.revisit(
                source=source,
                method=response.get("method", ""),
                params={},  # Params will be filled from identifiers by sub-agent
                reason=response.get("reason", "")
            )
        elif action_type == "spawn_child":
            return AgentAction.spawn(
                child_hypothesis=response.get("child_hypothesis", ""),
                reason=response.get("reason", "")
            )
        else:
            return AgentAction.conclude(
                reason=response.get("reason", "Sufficient evidence gathered")
            )

    async def should_continue(self, hypothesis: Hypothesis) -> bool:
        """
        Determine if investigation should continue for this hypothesis.

        Args:
            hypothesis: Current hypothesis state

        Returns:
            True if should continue, False if should stop
        """
        # Stop if hypothesis is confirmed or eliminated
        if hypothesis.status in ["confirmed", "eliminated"]:
            return False

        # Stop if confidence is very high or very low
        if hypothesis.confidence >= 0.9 or hypothesis.confidence <= 0.1:
            return False

        return True

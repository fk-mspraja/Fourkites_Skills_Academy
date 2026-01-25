"""
Hypothesis Formation Agent
Analyzes collected evidence and forms hypotheses about root causes

Enhanced with patterns extracted from Agent Cassie's knowledge base:
- Load not found scenarios (exists with different carrier, validation failure, deletion)
- Network/SCAC configuration issues
- Ocean tracking (JT scraping) patterns
- Duplicate load detection
"""
from typing import Dict, Any, List, Optional
import uuid
import logging

from app.agents.base import BaseAgent
from app.models import (
    InvestigationState,
    Hypothesis,
    Evidence,
    RootCauseCategory
)
from app.agents.hypothesis_patterns import (
    HypothesisPattern,
    EvidencePattern,
    get_all_patterns,
    match_triggers_to_patterns,
    LOAD_NOT_FOUND_PATTERNS,
    NETWORK_RELATIONSHIP_PATTERNS,
    SCAC_VALIDATION_PATTERNS,
    OCEAN_TRACKING_PATTERNS,
    DUPLICATE_LOAD_PATTERNS,
    RootCauseCategory as PatternCategory,
)

logger = logging.getLogger(__name__)


class HypothesisAgent(BaseAgent):
    """
    Forms hypotheses from collected evidence.

    Uses patterns extracted from Cassie's knowledge base for:
    - Pattern-based hypothesis generation
    - Evidence matching and confidence scoring
    - Resolution template selection based on case source
    """

    def __init__(self):
        super().__init__("Hypothesis Agent")
        self.patterns = get_all_patterns()

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Form hypotheses based on collected data.

        Uses a two-phase approach:
        1. Pattern-based: Match issue text to Cassie patterns for known scenarios
        2. Evidence-based: Analyze collected data for additional patterns

        Returns:
            State updates with hypotheses list
        """
        hypotheses = []

        # Phase 1: Pattern-based hypothesis generation (from Cassie's knowledge)
        issue_text = state.get("issue_text", "")
        matched_patterns = match_triggers_to_patterns(issue_text)

        for pattern in matched_patterns[:3]:  # Top 3 matching patterns
            hypothesis = self._evaluate_pattern(pattern, state)
            if hypothesis:
                hypotheses.append(hypothesis)
                logger.info(f"Pattern match: {pattern.id} -> {hypothesis.description}")

        # Phase 2: Evidence-based hypothesis generation (existing logic)
        # Pattern 1: Load not found in Tracking API
        tracking_data = state.get("tracking_data", {})
        if not tracking_data.get("exists"):
            hypotheses.append(self._create_hypothesis(
                "H1",
                "Load was never created in the system",
                RootCauseCategory.LOAD_CREATION_FAILURE,
                0.9,
                [Evidence(
                    source="Tracking API",
                    finding="Load not found",
                    supports_hypothesis=True,
                    weight=0.9
                )]
            ))

        # Pattern 2: Network relationship missing
        network_data = state.get("network_data", {})
        if network_data.get("relationship_exists") == False:
            hypotheses.append(self._create_hypothesis(
                "H2",
                "Carrier-shipper network relationship not configured",
                RootCauseCategory.NETWORK_RELATIONSHIP,
                0.85,
                [Evidence(
                    source="Network API",
                    finding="No network relationship found",
                    supports_hypothesis=True,
                    weight=0.85,
                    raw_data=network_data
                )]
            ))

        # Pattern 3: JT scraping errors (Ocean mode)
        jt_data = state.get("jt_data", {})
        if jt_data.get("has_errors"):
            error_count = jt_data.get("error_count", 0)
            hypotheses.append(self._create_hypothesis(
                "H3",
                "RPA scraping failed or encountered errors in Just Transform",
                RootCauseCategory.JT_ISSUE,
                min(0.75, 0.5 + (error_count * 0.05)),  # Higher errors = higher confidence
                [Evidence(
                    source="Just Transform",
                    finding=f"{error_count} scraping errors found",
                    supports_hypothesis=True,
                    weight=0.7,
                    raw_data=jt_data
                )]
            ))

        # Pattern 4: Super API configuration issues
        super_api_data = state.get("super_api_data", {})
        if super_api_data.get("exists") and not super_api_data.get("subscription_id"):
            hypotheses.append(self._create_hypothesis(
                "H4",
                "Tracking configuration incomplete - missing subscription",
                RootCauseCategory.CONFIGURATION_ISSUE,
                0.7,
                [Evidence(
                    source="Super API",
                    finding="Config exists but no subscription_id",
                    supports_hypothesis=True,
                    weight=0.7
                )]
            ))

        # Pattern 5: Subscription disabled
        sub_details = super_api_data.get("subscription_details", {})
        if sub_details.get("exists") and not sub_details.get("scraping_enabled"):
            hypotheses.append(self._create_hypothesis(
                "H5",
                "Carrier portal scraping is disabled",
                RootCauseCategory.CONFIGURATION_ISSUE,
                0.8,
                [Evidence(
                    source="Super API",
                    finding="Subscription exists but scraping disabled",
                    supports_hypothesis=True,
                    weight=0.8
                )]
            ))

        # Pattern 6: Load exists but mode-specific data missing
        if tracking_data.get("exists"):
            mode = tracking_data.get("mode")
            if mode == "OCEAN" and not super_api_data.get("exists"):
                hypotheses.append(self._create_hypothesis(
                    "H6",
                    "Ocean load missing internal tracking configuration",
                    RootCauseCategory.CONFIGURATION_ISSUE,
                    0.75,
                    [Evidence(
                        source="Tracking API + Super API",
                        finding=f"Load exists (mode={mode}) but no Super API config",
                        supports_hypothesis=True,
                        weight=0.75
                    )]
                ))

        # Pattern 7: Validation errors from Redshift
        redshift_data = state.get("redshift_data", {})
        if redshift_data.get("validation_attempts"):
            failed_attempts = redshift_data.get("failed_attempts", 0)
            total_attempts = redshift_data.get("total_attempts", 0)
            latest_error = redshift_data.get("latest_error", "")

            # High confidence if we have multiple consecutive failures with same error
            if failed_attempts >= 5 and total_attempts == failed_attempts:
                # Determine category and description based on error message
                category = RootCauseCategory.DATA_QUALITY
                description = "Load validation failures"
                confidence = 0.9

                # Specific error pattern detection
                if "port of loading and port of discharge" in latest_error.lower():
                    category = RootCauseCategory.CONFIGURATION_ISSUE
                    description = "Ocean load has invalid stop configuration (multiple POL/POD)"
                    confidence = 0.95
                elif "network relationship" in latest_error.lower():
                    category = RootCauseCategory.NETWORK_RELATIONSHIP
                    description = "Network relationship validation failures"
                    confidence = 0.9
                elif "duplicate" in latest_error.lower():
                    category = RootCauseCategory.DATA_QUALITY
                    description = "Duplicate load data causing validation failures"
                    confidence = 0.85

                hypotheses.append(self._create_hypothesis(
                    "H7",
                    description,
                    category,
                    confidence,
                    [Evidence(
                        source="Redshift Load Validation",
                        finding=f"{failed_attempts} consecutive validation failures: {latest_error}",
                        supports_hypothesis=True,
                        weight=0.95,
                        raw_data={"error": latest_error, "failures": failed_attempts}
                    )]
                ))

        # If no hypotheses formed, create a generic one
        if not hypotheses:
            hypotheses.append(self._create_hypothesis(
                "H_UNKNOWN",
                "Insufficient data to determine root cause",
                RootCauseCategory.UNKNOWN,
                0.3,
                [Evidence(
                    source="Multi-Agent System",
                    finding="No clear patterns found in collected data",
                    supports_hypothesis=True,
                    weight=0.3
                )]
            ))

        # Sort by confidence
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        summary = f"Formed {len(hypotheses)} hypotheses. Top: {hypotheses[0].description} ({hypotheses[0].confidence:.0%})"

        return {
            "hypotheses": hypotheses,
            "_message": summary
        }

    def _create_hypothesis(
        self,
        id_suffix: str,
        description: str,
        category: RootCauseCategory,
        confidence: float,
        evidence_for: List[Evidence]
    ) -> Hypothesis:
        """Helper to create a hypothesis"""
        return Hypothesis(
            id=f"{uuid.uuid4().hex[:8]}-{id_suffix}",
            description=description,
            category=category,
            confidence=confidence,
            evidence_for=evidence_for,
            evidence_against=[]
        )

    def _evaluate_pattern(
        self,
        pattern: HypothesisPattern,
        state: InvestigationState
    ) -> Optional[Hypothesis]:
        """
        Evaluate a hypothesis pattern against current state.

        Uses evidence patterns from Cassie's knowledge base to:
        1. Check if evidence conditions are met
        2. Calculate confidence based on weighted evidence
        3. Generate appropriate hypothesis

        Args:
            pattern: HypothesisPattern from Cassie's knowledge
            state: Current investigation state

        Returns:
            Hypothesis if pattern matches, None otherwise
        """
        evidence_for = []
        evidence_against = []
        total_for_weight = 0.0
        total_against_weight = 0.0

        for ep in pattern.evidence_patterns:
            evidence_result = self._check_evidence_pattern(ep, state)
            if evidence_result:
                finding, raw_data = evidence_result
                evidence = Evidence(
                    source=ep.source,
                    finding=finding,
                    supports_hypothesis=ep.supports_hypothesis,
                    weight=ep.weight,
                    raw_data=raw_data
                )

                if ep.supports_hypothesis:
                    evidence_for.append(evidence)
                    total_for_weight += ep.weight
                else:
                    evidence_against.append(evidence)
                    total_against_weight += ep.weight

        # Only create hypothesis if we have supporting evidence
        if not evidence_for:
            return None

        # Calculate confidence using Bayesian-style weighted evidence
        # Formula: (sum of for weights) / (sum of for weights + sum of against weights)
        total_weight = total_for_weight + total_against_weight
        if total_weight > 0:
            confidence = total_for_weight / total_weight
        else:
            confidence = 0.5  # Neutral if no evidence

        # Apply dampening for low evidence count
        evidence_count = len(evidence_for) + len(evidence_against)
        if evidence_count < 3:
            confidence *= 0.8  # Reduce confidence with less evidence

        # Map pattern category to model category
        category_mapping = {
            PatternCategory.LOAD_NOT_FOUND: RootCauseCategory.UNKNOWN,
            PatternCategory.LOAD_DELETED: RootCauseCategory.DATA_QUALITY,
            PatternCategory.LOAD_ASSIGNED_DIFFERENT_CARRIER: RootCauseCategory.CONFIGURATION_ISSUE,
            PatternCategory.LOAD_CREATION_FAILED: RootCauseCategory.LOAD_CREATION_FAILURE,
            PatternCategory.NETWORK_RELATIONSHIP_MISSING: RootCauseCategory.NETWORK_RELATIONSHIP,
            PatternCategory.NETWORK_RELATIONSHIP_INACTIVE: RootCauseCategory.NETWORK_RELATIONSHIP,
            PatternCategory.SCAC_NOT_CONFIGURED: RootCauseCategory.CONFIGURATION_ISSUE,
            PatternCategory.SCAC_NOT_SENT: RootCauseCategory.DATA_QUALITY,
            PatternCategory.SCAC_WRONG_CODE: RootCauseCategory.CONFIGURATION_ISSUE,
            PatternCategory.JT_SCRAPING_ERROR: RootCauseCategory.JT_ISSUE,
            PatternCategory.OCEAN_SUBSCRIPTION_ISSUE: RootCauseCategory.CONFIGURATION_ISSUE,
            PatternCategory.VALIDATION_ERROR: RootCauseCategory.DATA_QUALITY,
            PatternCategory.DUPLICATE_LOAD: RootCauseCategory.DATA_QUALITY,
        }

        model_category = category_mapping.get(pattern.category, RootCauseCategory.UNKNOWN)

        hypothesis = Hypothesis(
            id=f"{uuid.uuid4().hex[:8]}-{pattern.id}",
            description=pattern.description,
            category=model_category,
            confidence=confidence,
            evidence_for=evidence_for,
            evidence_against=evidence_against
        )

        return hypothesis

    def _check_evidence_pattern(
        self,
        ep: EvidencePattern,
        state: InvestigationState
    ) -> Optional[tuple]:
        """
        Check if an evidence pattern condition is met in the current state.

        Args:
            ep: EvidencePattern to check
            state: Current investigation state

        Returns:
            Tuple of (finding_string, raw_data) if condition met, None otherwise
        """
        source = ep.source.lower()
        condition = ep.condition.lower()

        # Check different data sources based on pattern source
        if "tracking" in source:
            tracking_data = state.get("tracking_data", {})
            if "load_found" in condition or "load exists" in condition:
                if tracking_data.get("exists"):
                    return (
                        ep.finding_template.format(**tracking_data),
                        tracking_data
                    )
            elif "not found" in condition or "not exist" in condition:
                if not tracking_data.get("exists"):
                    return (
                        ep.finding_template.format(**state.get("identifiers", {})),
                        tracking_data
                    )

        elif "redshift" in source or "dwh" in source:
            redshift_data = state.get("redshift_data", {})
            validation_data = redshift_data.get("validation_data", {})

            if "validation" in condition and "failure" in condition:
                if redshift_data.get("validation_failures", 0) > 0:
                    return (
                        ep.finding_template.format(
                            error_message=redshift_data.get("latest_error", "Unknown")
                        ),
                        redshift_data
                    )

            if "deleted" in condition:
                if redshift_data.get("deleted_at"):
                    return (
                        ep.finding_template.format(**redshift_data),
                        redshift_data
                    )

            if "load_validation_data_mart" in condition:
                if validation_data:
                    return (
                        ep.finding_template.format(**validation_data),
                        validation_data
                    )

        elif "network" in source:
            network_data = state.get("network_data", {})
            if "no record" in condition or "missing" in condition:
                if not network_data.get("relationship_exists"):
                    return (
                        ep.finding_template.format(**state.get("identifiers", {})),
                        network_data
                    )
            elif "active" in condition or "exists" in condition:
                if network_data.get("relationship_exists"):
                    return (
                        ep.finding_template.format(**network_data),
                        network_data
                    )

        elif "jt" in source:
            jt_data = state.get("jt_data", {})
            if "error" in condition or "has_errors" in condition:
                if jt_data.get("has_errors"):
                    return (
                        ep.finding_template.format(
                            error_count=jt_data.get("error_count", 0),
                            **jt_data
                        ),
                        jt_data
                    )
            elif "subscription not found" in condition:
                if not jt_data.get("subscription_exists"):
                    return (
                        ep.finding_template.format(**state.get("identifiers", {})),
                        jt_data
                    )

        elif "super" in source:
            super_data = state.get("super_api_data", {})
            if "not found" in condition or "missing" in condition:
                if not super_data.get("exists"):
                    return (
                        ep.finding_template.format(**state.get("identifiers", {})),
                        super_data
                    )

        # Generic fallback - check if condition string appears in state data
        return None

    def get_resolution_template(
        self,
        hypothesis: Hypothesis,
        case_source: str = "SHIPPER"
    ) -> Optional[str]:
        """
        Get the appropriate resolution template for a hypothesis.

        Uses templates from Cassie's knowledge base based on:
        - Hypothesis type/pattern
        - Case source (CARRIER vs SHIPPER perspective)

        Args:
            hypothesis: The hypothesis to get resolution for
            case_source: "CARRIER" or "SHIPPER" (from case context)

        Returns:
            Resolution template string, or None if not found
        """
        # Find matching pattern by ID suffix
        pattern_id = hypothesis.id.split("-")[-1] if "-" in hypothesis.id else None

        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern.resolution_templates.get(
                    case_source,
                    pattern.resolution_templates.get("SHIPPER", "")
                )

        return None

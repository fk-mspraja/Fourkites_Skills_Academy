"""
Skills Router - Hierarchical classification and routing.
Solves the 10-12 domain routing problem through multi-level classification.

Part of RCA Agent Platform - Phase 1 Implementation
References: Plan Part 2.3 and Part 5.1.2
"""
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re


class IntentCategory(Enum):
    """Top-level intent classification"""
    TRACKING_ISSUE = "tracking_issue"
    LOAD_CREATION = "load_creation"
    DATA_QUALITY = "data_quality"
    BILLING = "billing"
    UNKNOWN = "unknown"


class Domain(Enum):
    """Domain-level classification"""
    OTR = "otr"  # Ground tracking (ELD, GPS, Carrier API)
    OCEAN = "ocean"  # Container tracking (JT, vessel updates)
    DRAYAGE = "drayage"  # Dray-specific issues
    CARRIER_FILES = "carrier_files"  # File-based tracking
    AIR = "air"  # Air freight
    UNKNOWN = "unknown"


@dataclass
class RoutingDecision:
    """Result of routing decision with confidence and reasoning"""
    skill_id: str
    confidence: float
    intent: IntentCategory
    domain: Domain
    category: str
    reasoning: str
    matched_patterns: List[str]

    @property
    def confidence_level(self) -> str:
        """Human-readable confidence level"""
        if self.confidence >= 0.85:
            return "HIGH"
        elif self.confidence >= 0.60:
            return "MEDIUM"
        else:
            return "LOW"

    def should_auto_route(self, threshold: float = 0.85) -> bool:
        """Check if confidence is high enough for auto-routing"""
        return self.confidence >= threshold

    def needs_human_review(self, threshold: float = 0.60) -> bool:
        """Check if decision needs human review"""
        return self.confidence < threshold


class SkillsRouter:
    """
    Hierarchical router for selecting the right skill.

    Classification flow:
    1. Intent classification (TRACKING_ISSUE, LOAD_CREATION, etc.)
    2. Domain detection (OTR, OCEAN, DRAYAGE, etc.)
    3. Skill selection

    Example:
        router = SkillsRouter()
        router.register_skill("otr-rca", otr_skill_instance)

        decision = router.route({
            "description": "Load not tracking...",
            "load_number": "U110123982",
            "mode": "ground"
        })

        if decision.should_auto_route():
            skill = router.skills[decision.skill_id]
            result = skill.investigate(context)
    """

    def __init__(self):
        self.skills = {}  # skill_id -> Skill instance
        self._load_classification_rules()

    def register_skill(self, skill_id: str, skill_instance):
        """
        Register a skill with the router

        Args:
            skill_id: Unique identifier (e.g., "otr-rca", "ocean-tracking")
            skill_instance: Skill instance with investigate() method
        """
        self.skills[skill_id] = skill_instance

    def route(self, context: Dict[str, Any]) -> RoutingDecision:
        """
        Route request to appropriate skill.

        Args:
            context: {
                "description": "Load not tracking...",
                "load_number": "U110123982",
                "mode": "ground" | "ocean" | etc. (optional),
                "shipper": "walmart" (optional),
                "carrier": "crst-logistics" (optional)
            }

        Returns:
            RoutingDecision with skill_id and confidence
        """
        matched_patterns = []

        # Level 1: Intent classification
        intent, intent_confidence, intent_patterns = self._classify_intent(context)
        matched_patterns.extend(intent_patterns)

        if intent == IntentCategory.UNKNOWN:
            return RoutingDecision(
                skill_id="unknown",
                confidence=0.0,
                intent=intent,
                domain=Domain.UNKNOWN,
                category="unknown",
                reasoning="Could not classify intent from description",
                matched_patterns=matched_patterns
            )

        # Currently only supporting TRACKING_ISSUE intent
        if intent != IntentCategory.TRACKING_ISSUE:
            return RoutingDecision(
                skill_id="unknown",
                confidence=0.0,
                intent=intent,
                domain=Domain.UNKNOWN,
                category=intent.value,
                reasoning=f"Intent {intent.value} not yet supported",
                matched_patterns=matched_patterns
            )

        # Level 2: Domain detection
        domain, domain_confidence, domain_patterns = self._detect_domain(context)
        matched_patterns.extend(domain_patterns)

        # Level 3: Skill selection
        skill_id, category = self._select_skill(intent, domain)

        # Calculate overall confidence
        overall_confidence = (intent_confidence + domain_confidence) / 2.0

        # Build reasoning
        reasoning_parts = []
        if intent_patterns:
            reasoning_parts.append(f"Intent: {intent.value} (patterns: {', '.join(intent_patterns)})")
        if domain_patterns:
            reasoning_parts.append(f"Domain: {domain.value} (patterns: {', '.join(domain_patterns)})")
        reasoning_parts.append(f"Skill: {skill_id}")

        reasoning = " → ".join(reasoning_parts)

        return RoutingDecision(
            skill_id=skill_id,
            confidence=overall_confidence,
            intent=intent,
            domain=domain,
            category=category,
            reasoning=reasoning,
            matched_patterns=matched_patterns
        )

    def _classify_intent(self, context: Dict[str, Any]) -> Tuple[IntentCategory, float, List[str]]:
        """
        Classify top-level intent from context

        Returns:
            (IntentCategory, confidence, matched_patterns)
        """
        description = context.get("description", "").lower()
        matched_patterns = []

        # Tracking issue patterns
        tracking_patterns = [
            (r"not tracking", "not tracking"),
            (r"no updates?", "no updates"),
            (r"not receiving", "not receiving"),
            (r"positions? not showing", "positions not showing"),
            (r"tracking stopped", "tracking stopped"),
            (r"awaiting tracking", "awaiting tracking"),
            (r"no events?", "no events"),
            (r"missing (position|update)s?", "missing positions/updates"),
            (r"cannot track", "cannot track"),
            (r"visibility (issue|problem)", "visibility issue"),
            (r"no position", "no position"),
            (r"positions? (missing|stopped)", "positions missing/stopped")
        ]

        for pattern, label in tracking_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                matched_patterns.append(label)

        if matched_patterns:
            # Confidence based on number of patterns matched
            confidence = min(0.95, 0.7 + (len(matched_patterns) * 0.05))
            return IntentCategory.TRACKING_ISSUE, confidence, matched_patterns

        # Load creation patterns
        load_creation_patterns = [
            (r"create load", "create load"),
            (r"new (load|shipment)", "new load/shipment"),
            (r"book(ing)?", "booking"),
            (r"tender", "tender")
        ]

        for pattern, label in load_creation_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                matched_patterns.append(label)

        if matched_patterns:
            confidence = min(0.95, 0.7 + (len(matched_patterns) * 0.05))
            return IntentCategory.LOAD_CREATION, confidence, matched_patterns

        # Data quality patterns
        data_quality_patterns = [
            (r"incorrect data", "incorrect data"),
            (r"wrong (address|time|date)", "wrong field"),
            (r"duplicate", "duplicate"),
            (r"data (issue|problem)", "data issue")
        ]

        for pattern, label in data_quality_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                matched_patterns.append(label)

        if matched_patterns:
            confidence = min(0.95, 0.7 + (len(matched_patterns) * 0.05))
            return IntentCategory.DATA_QUALITY, confidence, matched_patterns

        return IntentCategory.UNKNOWN, 0.0, []

    def _detect_domain(self, context: Dict[str, Any]) -> Tuple[Domain, float, List[str]]:
        """
        Detect domain from context

        Returns:
            (Domain, confidence, matched_patterns)
        """
        mode = context.get("mode", "").lower()
        description = context.get("description", "").lower()
        matched_patterns = []

        # Explicit mode detection
        if mode:
            if mode in ["ocean", "multimodal", "intermodal"]:
                matched_patterns.append(f"mode:{mode}")
                return Domain.OCEAN, 0.95, matched_patterns
            elif mode in ["ground", "otr", "ltl", "ftl"]:
                matched_patterns.append(f"mode:{mode}")
                return Domain.OTR, 0.95, matched_patterns
            elif mode in ["drayage", "dray"]:
                matched_patterns.append(f"mode:{mode}")
                return Domain.DRAYAGE, 0.95, matched_patterns
            elif mode in ["air", "airfreight"]:
                matched_patterns.append(f"mode:{mode}")
                return Domain.AIR, 0.95, matched_patterns

        # Domain patterns in description
        ocean_patterns = [
            (r"container", "container"),
            (r"vessel", "vessel"),
            (r"b/?o/?l", "BOL"),
            (r"booking", "booking"),
            (r"ocean", "ocean"),
            (r"port", "port"),
            (r"terminal", "terminal"),
            (r"(imo|mmsi)\s*\d+", "vessel ID")
        ]

        otr_patterns = [
            (r"truck", "truck"),
            (r"eld", "ELD"),
            (r"gps", "GPS"),
            (r"driver", "driver"),
            (r"ground", "ground"),
            (r"over.?the.?road", "over-the-road"),
            (r"ftl|ltl", "FTL/LTL"),
            (r"tractor|trailer", "tractor/trailer")
        ]

        drayage_patterns = [
            (r"dray(age)?", "drayage"),
            (r"yard", "yard"),
            (r"facility", "facility"),
            (r"check.?in", "check-in"),
            (r"check.?out", "check-out"),
            (r"chassis", "chassis")
        ]

        air_patterns = [
            (r"air", "air"),
            (r"flight", "flight"),
            (r"awb", "AWB"),
            (r"aircraft", "aircraft"),
            (r"airport", "airport")
        ]

        # Score each domain
        ocean_score = sum(1 for pattern, label in ocean_patterns
                         if re.search(pattern, description, re.IGNORECASE))
        otr_score = sum(1 for pattern, label in otr_patterns
                       if re.search(pattern, description, re.IGNORECASE))
        drayage_score = sum(1 for pattern, label in drayage_patterns
                           if re.search(pattern, description, re.IGNORECASE))
        air_score = sum(1 for pattern, label in air_patterns
                       if re.search(pattern, description, re.IGNORECASE))

        # Collect matched patterns for winning domain
        if ocean_score > 0:
            for pattern, label in ocean_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    matched_patterns.append(label)

        if otr_score > 0:
            for pattern, label in otr_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    matched_patterns.append(label)

        if drayage_score > 0:
            for pattern, label in drayage_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    matched_patterns.append(label)

        if air_score > 0:
            for pattern, label in air_patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    matched_patterns.append(label)

        # Determine winner
        max_score = max(ocean_score, otr_score, drayage_score, air_score)

        if max_score == 0:
            # Default to OTR if no patterns match (most common case)
            return Domain.OTR, 0.5, ["default:ground"]

        # Calculate confidence based on score
        confidence = min(0.95, 0.6 + (max_score * 0.1))

        if ocean_score == max_score:
            return Domain.OCEAN, confidence, matched_patterns
        elif drayage_score == max_score:
            return Domain.DRAYAGE, confidence, matched_patterns
        elif air_score == max_score:
            return Domain.AIR, confidence, matched_patterns
        else:  # otr_score == max_score
            return Domain.OTR, confidence, matched_patterns

    def _select_skill(self, intent: IntentCategory, domain: Domain) -> Tuple[str, str]:
        """
        Select skill based on intent and domain

        Returns:
            (skill_id, category)
        """
        # Mapping: (intent, domain) -> (skill_id, category)
        skill_map = {
            # Tracking issues
            (IntentCategory.TRACKING_ISSUE, Domain.OTR):
                ("otr-rca", "LOAD_NOT_TRACKING"),
            (IntentCategory.TRACKING_ISSUE, Domain.OCEAN):
                ("ocean-tracking", "CONTAINER_NOT_TRACKING"),
            (IntentCategory.TRACKING_ISSUE, Domain.DRAYAGE):
                ("drayage-rca", "DRAYAGE_TRACKING_ISSUE"),
            (IntentCategory.TRACKING_ISSUE, Domain.CARRIER_FILES):
                ("carrier-files", "FILE_TRACKING_ISSUE"),
            (IntentCategory.TRACKING_ISSUE, Domain.AIR):
                ("air-tracking", "AIR_TRACKING_ISSUE"),

            # Load creation (future)
            (IntentCategory.LOAD_CREATION, Domain.OTR):
                ("load-creation", "OTR_LOAD_CREATION"),
            (IntentCategory.LOAD_CREATION, Domain.OCEAN):
                ("load-creation", "OCEAN_LOAD_CREATION"),

            # Data quality (future)
            (IntentCategory.DATA_QUALITY, Domain.OTR):
                ("data-quality", "OTR_DATA_QUALITY"),
            (IntentCategory.DATA_QUALITY, Domain.OCEAN):
                ("data-quality", "OCEAN_DATA_QUALITY"),
        }

        return skill_map.get((intent, domain), ("unknown", "UNKNOWN"))

    def _load_classification_rules(self):
        """
        Load classification rules from config.

        This method is a placeholder for future YAML-based configuration.
        Current implementation uses hardcoded rules in the methods above.

        Future enhancement:
        - Load from skills_router_config.yaml
        - Support custom pattern definitions
        - Enable domain-specific rule tuning
        """
        # TODO: Implement YAML-based rule loading
        # For now, rules are embedded in classification methods
        pass

    def get_supported_skills(self) -> List[str]:
        """Get list of registered skill IDs"""
        return list(self.skills.keys())

    def get_skill(self, skill_id: str):
        """Get skill instance by ID"""
        return self.skills.get(skill_id)

    def validate_context(self, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that context has required fields

        Returns:
            (is_valid, error_message)
        """
        if not context:
            return False, "Context is empty"

        if "description" not in context:
            return False, "Missing required field: description"

        description = context.get("description", "")
        if not description or not description.strip():
            return False, "Description is empty"

        return True, None

    def explain_routing(self, context: Dict[str, Any]) -> str:
        """
        Generate detailed explanation of routing decision

        Useful for debugging and understanding why a particular skill was chosen
        """
        decision = self.route(context)

        explanation = f"""
Routing Decision Explanation
============================

INPUT:
  Description: {context.get('description', 'N/A')}
  Mode: {context.get('mode', 'N/A')}

CLASSIFICATION:
  Intent: {decision.intent.value} (confidence: {decision.confidence:.0%})
  Domain: {decision.domain.value}
  Category: {decision.category}

MATCHED PATTERNS:
  {', '.join(decision.matched_patterns) if decision.matched_patterns else 'None'}

DECISION:
  Skill ID: {decision.skill_id}
  Confidence Level: {decision.confidence_level}
  Overall Confidence: {decision.confidence:.0%}

ROUTING RECOMMENDATION:
  Auto-route: {'Yes' if decision.should_auto_route() else 'No'}
  Human review needed: {'Yes' if decision.needs_human_review() else 'No'}

REASONING:
  {decision.reasoning}
"""
        return explanation


# Example usage and testing
if __name__ == "__main__":
    # Create router
    router = SkillsRouter()

    # Test cases
    test_cases = [
        {
            "description": "Load U110123982 not tracking for walmart",
            "mode": "ground",
            "shipper": "walmart",
            "carrier": "crst-logistics"
        },
        {
            "description": "Container ABCD1234567 not tracking, vessel updates missing",
            "mode": "ocean"
        },
        {
            "description": "Drayage load not tracking, check-in issue at facility"
        },
        {
            "description": "Load not tracking - ELD not enabled for carrier",
            "mode": "ground"
        },
        {
            "description": "No position updates, GPS timestamp null in tracking worker logs"
        },
        {
            "description": "AWB 123-45678901 not tracking",
            "mode": "air"
        },
        {
            "description": "Truck positions not showing for driver"
        },
        {
            "description": "Ocean container tracking stopped, no terminal updates"
        }
    ]

    print("Skills Router Test Cases")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Description: {test['description']}")

        # Validate context
        is_valid, error = router.validate_context(test)
        if not is_valid:
            print(f"ERROR: {error}")
            continue

        # Route
        decision = router.route(test)

        print(f"Skill: {decision.skill_id}")
        print(f"Confidence: {decision.confidence:.0%} ({decision.confidence_level})")
        print(f"Intent: {decision.intent.value}")
        print(f"Domain: {decision.domain.value}")
        print(f"Category: {decision.category}")
        print(f"Patterns: {', '.join(decision.matched_patterns)}")
        print(f"Auto-route: {decision.should_auto_route()}")
        print(f"Reasoning: {decision.reasoning}")

    print("\n" + "=" * 80)
    print("\nDetailed Explanation for First Test Case:")
    print(router.explain_routing(test_cases[0]))

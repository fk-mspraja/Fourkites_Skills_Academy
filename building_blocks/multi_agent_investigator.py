"""
Multi-Agent Investigator - Progressive investigation flow matching UX mock.

This module orchestrates a multi-agent investigation workflow that mimics the
UX mock's real-time progress display. Each agent specializes in a specific
data collection or analysis task.

Investigation Flow:
1. Identifier Agent - Extract IDs, validate load exists
2. Tracking API Agent - Query load status, carrier info
3. Redshift Agent - Historical patterns, past issues
4. Network Agent - Network relationships, ELD config
5. Hypothesis Agent - Generate hypotheses from evidence
6. Synthesis Agent - Determine root cause, create resolution

Matches UX mock's real-time progress display from RCA_UX_ANALYSIS.md.
"""
import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status for progress tracking."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentStep:
    """Represents one agent's execution in the investigation.

    Attributes:
        name: Display name of the agent (e.g., "Identifier Agent")
        status: Current execution status
        started_at: When agent started executing
        completed_at: When agent finished
        result: Data collected/computed by the agent
        error: Error message if agent failed
        duration_ms: Execution duration in milliseconds
        findings: List of key findings for display
    """
    name: str
    status: AgentStatus = AgentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "findings": self.findings,
            "error": self.error,
        }


@dataclass
class HypothesisResult:
    """A potential root cause hypothesis with confidence scoring.

    Attributes:
        pattern_id: Identifier for the pattern (e.g., "eld_not_enabled")
        description: Human-readable description
        confidence: Confidence score 0.0-1.0
        supporting_evidence: List of evidence supporting this hypothesis
        contradicting_evidence: List of evidence against this hypothesis
        resolution_steps: Recommended resolution steps
        email_template: Optional email template for carrier communication
    """
    pattern_id: str
    description: str
    confidence: float
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    resolution_steps: List[Dict[str, Any]] = field(default_factory=list)
    email_template: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern_id": self.pattern_id,
            "description": self.description,
            "confidence": self.confidence,
            "confidence_percent": int(self.confidence * 100),
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "resolution_steps": self.resolution_steps,
            "email_template": self.email_template,
        }


@dataclass
class InvestigationResult:
    """Final investigation result with all findings.

    Attributes:
        ticket_id: Original ticket ID (e.g., "SF-12345")
        load_number: Customer load number
        tracking_id: FourKites tracking ID
        confidence: Overall confidence score 0.0-1.0
        confidence_level: Human-readable level ("high", "medium", "low")
        root_cause: Primary root cause description
        hypotheses: All evaluated hypotheses sorted by confidence
        resolution: Recommended resolution with steps
        evidence_summary: Summary of all evidence collected
        investigation_time_seconds: Total investigation duration
        steps: All agent steps with status
        skill_used: Name of the skill used
        skill_version: Version of the skill
        shipper: Shipper company info
        carrier: Carrier company info
    """
    ticket_id: str
    load_number: Optional[str]
    tracking_id: Optional[str]
    confidence: float
    confidence_level: str
    root_cause: str
    hypotheses: List[HypothesisResult]
    resolution: Dict[str, Any]
    evidence_summary: List[Dict[str, Any]]
    investigation_time_seconds: float
    steps: List[AgentStep]
    skill_used: str
    skill_version: str
    shipper: Optional[Dict[str, str]] = None
    carrier: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticket_id": self.ticket_id,
            "load_number": self.load_number,
            "tracking_id": self.tracking_id,
            "confidence": self.confidence,
            "confidence_percent": int(self.confidence * 100),
            "confidence_level": self.confidence_level,
            "root_cause": self.root_cause,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "resolution": self.resolution,
            "evidence_summary": self.evidence_summary,
            "investigation_time_seconds": round(self.investigation_time_seconds, 2),
            "steps": [s.to_dict() for s in self.steps],
            "skill_used": self.skill_used,
            "skill_version": self.skill_version,
            "shipper": self.shipper,
            "carrier": self.carrier,
        }


class BaseInvestigationAgent(ABC):
    """Abstract base class for investigation agents.

    Each agent implements a specific investigation task:
    - Data collection from a specific source
    - Analysis of collected data
    - Pattern matching against known issues
    """

    def __init__(self, name: str):
        """Initialize agent with name for logging."""
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic.

        Args:
            context: Investigation context with identifiers and collected data

        Returns:
            Dictionary with agent results
        """
        pass

    def log_start(self, message: str):
        """Log agent start."""
        self.logger.info(f"[{self.name}] Starting: {message}")

    def log_success(self, message: str):
        """Log agent success."""
        self.logger.info(f"[{self.name}] Success: {message}")

    def log_error(self, message: str):
        """Log agent error."""
        self.logger.error(f"[{self.name}] Error: {message}")

    def log_warning(self, message: str):
        """Log agent warning."""
        self.logger.warning(f"[{self.name}] Warning: {message}")


class IdentifierAgent(BaseInvestigationAgent):
    """Agent 1: Extract and validate identifiers from ticket context.

    Responsibilities:
    - Extract tracking_id, load_number from description
    - Validate identifiers exist in system
    - Return normalized identifiers for downstream agents
    """

    # Patterns for extracting identifiers
    TRACKING_ID_PATTERNS = [
        r"tracking[_\s]?id[:\s]*(\d+)",
        r"tracking[:\s]*(\d{9,})",
        r"load[_\s]?id[:\s]*(\d+)",
        r"id[:\s]*(\d{9,})",
    ]

    LOAD_NUMBER_PATTERNS = [
        r"load[_\s]?number[:\s]*([A-Za-z0-9\-_]+)",
        r"load[#:\s]+([A-Za-z0-9\-_]+)",
        r"(?:customer\s+)?load[:\s]*([A-Za-z0-9\-_]+)",
        r"([A-Z]{1,3}\d{8,})",  # Common load number format
    ]

    def __init__(self):
        super().__init__("Identifier Agent")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate identifiers."""
        self.log_start("Extracting identifiers from context")

        # Get input identifiers
        tracking_id = context.get("tracking_id")
        load_number = context.get("load_number")
        description = context.get("description", "")

        # Try to extract from description if not provided
        if not tracking_id and description:
            tracking_id = self._extract_tracking_id(description)

        if not load_number and description:
            load_number = self._extract_load_number(description)

        # Build result
        result = {
            "tracking_id": tracking_id,
            "load_number": load_number,
            "identifiers_found": bool(tracking_id or load_number),
            "extraction_source": "provided" if context.get("tracking_id") or context.get("load_number") else "extracted",
        }

        if tracking_id:
            self.log_success(f"Found tracking_id: {tracking_id}")
        if load_number:
            self.log_success(f"Found load_number: {load_number}")
        if not result["identifiers_found"]:
            self.log_warning("No identifiers found in context")

        return result

    def _extract_tracking_id(self, text: str) -> Optional[str]:
        """Extract tracking ID from text using regex patterns."""
        text_lower = text.lower()
        for pattern in self.TRACKING_ID_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)
        return None

    def _extract_load_number(self, text: str) -> Optional[str]:
        """Extract load number from text using regex patterns."""
        for pattern in self.LOAD_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None


class TrackingAPIAgent(BaseInvestigationAgent):
    """Agent 2: Query Tracking API for load status and metadata.

    Responsibilities:
    - Fetch load metadata from Tracking API
    - Extract shipper/carrier information
    - Determine current tracking status
    - Identify tracking method (ELD, mobile, API)
    """

    def __init__(self, tracking_api_client=None):
        super().__init__("Tracking API Agent")
        self.tracking_api = tracking_api_client

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Query Tracking API for load data."""
        self.log_start("Querying Tracking API")

        tracking_id = context.get("tracking_id")
        load_number = context.get("load_number")
        shipper_id = context.get("shipper_id")

        if not tracking_id and not load_number:
            self.log_error("No tracking_id or load_number to query")
            return {"error": "No identifiers provided", "load_found": False}

        # If we have a real client, use it
        if self.tracking_api:
            return await self._query_real_api(tracking_id, load_number, shipper_id)

        # Otherwise return mock data for testing
        return self._get_mock_data(tracking_id, load_number)

    async def _query_real_api(
        self,
        tracking_id: Optional[str],
        load_number: Optional[str],
        shipper_id: Optional[str]
    ) -> Dict[str, Any]:
        """Query real Tracking API."""
        try:
            # Prefer tracking_id if available
            if tracking_id:
                data = self.tracking_api.get_tracking_by_id(int(tracking_id))
            elif load_number:
                data = self.tracking_api.get_tracking_by_load_number(
                    load_number,
                    company_id=shipper_id
                )
            else:
                return {"error": "No identifiers", "load_found": False}

            if not data:
                self.log_warning("No data returned from Tracking API")
                return {"error": "Load not found", "load_found": False}

            # Extract metadata
            metadata = self.tracking_api.extract_load_metadata(data)
            if not metadata:
                return {"error": "Failed to parse load data", "load_found": False}

            self.log_success(f"Found load {metadata.get('load_number')}")

            return {
                "load_found": True,
                "tracking_id": metadata.get("tracking_id"),
                "load_number": metadata.get("load_number"),
                "status": metadata.get("status"),
                "mappable_status": metadata.get("mappable_status"),
                "shipper": {
                    "id": metadata.get("shipper_id"),
                    "name": metadata.get("shipper_name"),
                },
                "carrier": {
                    "id": metadata.get("carrier_id"),
                    "name": metadata.get("carrier_name"),
                },
                "managing_carrier": {
                    "id": metadata.get("managing_carrier_id"),
                    "name": metadata.get("managing_carrier_name"),
                },
                "tracking_method": metadata.get("tracking_method"),
                "load_mode": metadata.get("load_mode"),
                "actual_load_mode": metadata.get("actual_load_mode"),
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at"),
                "first_checkcall_at": metadata.get("first_checkcall_at"),
                "latest_checkcall_at": metadata.get("latest_checkcall_at"),
                "stops": metadata.get("stops", []),
                "current_location": metadata.get("current_location"),
            }

        except Exception as e:
            self.log_error(f"API error: {e}")
            return {"error": str(e), "load_found": False}

    def _get_mock_data(
        self,
        tracking_id: Optional[str],
        load_number: Optional[str]
    ) -> Dict[str, Any]:
        """Return mock data for testing without real API."""
        return {
            "load_found": True,
            "tracking_id": tracking_id or "614258134",
            "load_number": load_number or "U110123982",
            "status": "in_transit",
            "mappable_status": "tracking",
            "shipper": {
                "id": "walmart",
                "name": "Walmart Inc",
            },
            "carrier": {
                "id": "hardy-brothers",
                "name": "Hardy Brothers Inc",
            },
            "tracking_method": "mobile_app",
            "load_mode": "TL",
            "created_at": "2025-01-20T10:00:00Z",
            "updated_at": "2025-01-25T15:30:00Z",
            "first_checkcall_at": None,
            "latest_checkcall_at": None,
            "stops": [],
            "current_location": None,
        }


class RedshiftAgent(BaseInvestigationAgent):
    """Agent 3: Query Redshift for historical patterns and data.

    Responsibilities:
    - Query historical load patterns
    - Check for past issues with same carrier/lane
    - Get validation errors from load creation
    - Identify recurring patterns
    """

    def __init__(self, redshift_client=None):
        super().__init__("Redshift Agent")
        self.redshift = redshift_client

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Query Redshift for historical data."""
        self.log_start("Querying Redshift DWH")

        tracking_id = context.get("tracking_id")
        load_number = context.get("load_number")
        carrier_id = context.get("carrier", {}).get("id") if isinstance(context.get("carrier"), dict) else None
        shipper_id = context.get("shipper", {}).get("id") if isinstance(context.get("shipper"), dict) else None

        # If we have a real client, query it
        if self.redshift and self.redshift.is_available:
            return await self._query_real_redshift(
                tracking_id, load_number, carrier_id, shipper_id
            )

        # Return mock data for testing
        return self._get_mock_data()

    async def _query_real_redshift(
        self,
        tracking_id: Optional[str],
        load_number: Optional[str],
        carrier_id: Optional[str],
        shipper_id: Optional[str],
    ) -> Dict[str, Any]:
        """Query real Redshift database."""
        import asyncio

        result = {
            "load_history": None,
            "validation_errors": [],
            "carrier_patterns": None,
            "lane_issues": [],
        }

        try:
            # Run synchronous Redshift queries in thread pool
            loop = asyncio.get_event_loop()

            # Get load from fact_loads
            if tracking_id or load_number:
                load_data = await loop.run_in_executor(
                    None,
                    lambda: self.redshift.get_load_by_identifiers(
                        tracking_ids=[tracking_id] if tracking_id else None,
                        load_numbers=[load_number] if load_number else None,
                        shipper_id=shipper_id,
                    )
                )
                if load_data:
                    result["load_history"] = load_data
                    self.log_success(f"Found load history in Redshift")

            self.log_success("Redshift queries completed")
            return result

        except Exception as e:
            self.log_error(f"Redshift error: {e}")
            return {"error": str(e)}

    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data for testing."""
        return {
            "load_history": {
                "status": "in_transit",
                "created_at": "2025-01-20T10:00:00Z",
                "first_ping_time": None,
                "latest_check_call_time": None,
            },
            "validation_errors": [],
            "carrier_patterns": {
                "total_loads_30d": 150,
                "tracking_success_rate": 0.85,
                "avg_first_ping_delay_hours": 2.5,
                "common_issues": ["eld_not_enabled", "late_first_ping"],
            },
            "lane_issues": [],
        }


class NetworkAgent(BaseInvestigationAgent):
    """Agent 4: Query network relationships and ELD configuration.

    Responsibilities:
    - Check shipper-carrier network relationship
    - Verify ELD/tracking configuration
    - Check carrier capabilities
    - Identify network misconfigurations
    """

    def __init__(self, company_api_client=None):
        super().__init__("Network Agent")
        self.company_api = company_api_client

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Query network relationships and configuration."""
        self.log_start("Checking network configuration")

        shipper = context.get("shipper", {})
        carrier = context.get("carrier", {})
        shipper_id = shipper.get("id") if isinstance(shipper, dict) else None
        carrier_id = carrier.get("id") if isinstance(carrier, dict) else None

        if not shipper_id or not carrier_id:
            self.log_warning("Missing shipper or carrier ID for network check")
            return {
                "network_found": False,
                "reason": "Missing shipper or carrier identifiers",
            }

        # If we have a real client, use it
        if self.company_api:
            return await self._query_real_api(shipper_id, carrier_id)

        # Return mock data for testing
        return self._get_mock_data(shipper_id, carrier_id)

    async def _query_real_api(
        self,
        shipper_id: str,
        carrier_id: str
    ) -> Dict[str, Any]:
        """Query real Company API for network data."""
        try:
            # Query network relationship
            network_data = self.company_api.get_network_relationship(
                shipper_id, carrier_id
            )

            if not network_data:
                self.log_warning(f"No network relationship found: {shipper_id} -> {carrier_id}")
                return {
                    "network_found": False,
                    "shipper_id": shipper_id,
                    "carrier_id": carrier_id,
                    "reason": "No network relationship configured",
                }

            self.log_success(f"Found network: {shipper_id} -> {carrier_id}")

            return {
                "network_found": True,
                "shipper_id": shipper_id,
                "carrier_id": carrier_id,
                "external_id": network_data.get("external_id"),
                "eld_enabled": network_data.get("eld_enabled", False),
                "mobile_enabled": network_data.get("mobile_enabled", False),
                "api_enabled": network_data.get("api_enabled", False),
                "carrier_capabilities": network_data.get("carrier_capabilities", []),
                "tracking_methods": network_data.get("tracking_methods", []),
            }

        except Exception as e:
            self.log_error(f"Company API error: {e}")
            return {"error": str(e), "network_found": False}

    def _get_mock_data(self, shipper_id: str, carrier_id: str) -> Dict[str, Any]:
        """Return mock data for testing."""
        return {
            "network_found": True,
            "shipper_id": shipper_id,
            "carrier_id": carrier_id,
            "external_id": "NET-123456",
            "eld_enabled": False,  # This is the issue!
            "mobile_enabled": True,
            "api_enabled": False,
            "carrier_capabilities": ["mobile_app", "manual_update"],
            "tracking_methods": ["mobile_app"],
        }


class HypothesisAgent(BaseInvestigationAgent):
    """Agent 5: Generate and evaluate hypotheses from collected evidence.

    Responsibilities:
    - Analyze all collected data
    - Match against known patterns
    - Calculate confidence scores
    - Rank hypotheses by likelihood
    """

    # Known patterns with evidence checks
    PATTERNS = {
        "eld_not_enabled": {
            "description": "ELD tracking is not enabled for this carrier relationship",
            "checks": [
                {"field": "network.eld_enabled", "expected": False, "weight": 10},
                {"field": "tracking.first_checkcall_at", "expected": None, "weight": 8},
                {"field": "tracking.tracking_method", "expected": "eld", "inverse": True, "weight": 5},
            ],
            "resolution_steps": [
                {"step": 1, "action": "Enable ELD in Connect settings", "button": "Enable ELD"},
                {"step": 2, "action": "Verify carrier ELD device is active", "button": "Check Carrier"},
                {"step": 3, "action": "Monitor for position updates", "button": "Monitor"},
            ],
            "email_template": "eld_enablement_request",
        },
        "network_missing": {
            "description": "No shipper-carrier network relationship configured",
            "checks": [
                {"field": "network.network_found", "expected": False, "weight": 10},
            ],
            "resolution_steps": [
                {"step": 1, "action": "Create network relationship in Connect", "button": "Create Network"},
                {"step": 2, "action": "Configure tracking methods", "button": "Configure"},
            ],
            "email_template": None,
        },
        "no_tracking_device": {
            "description": "Carrier has not assigned a driver phone or ELD device",
            "checks": [
                {"field": "tracking.first_checkcall_at", "expected": None, "weight": 8},
                {"field": "tracking.latest_checkcall_at", "expected": None, "weight": 8},
                {"field": "network.network_found", "expected": True, "weight": 3},
            ],
            "resolution_steps": [
                {"step": 1, "action": "Contact carrier to assign tracking device", "button": "Email Carrier"},
                {"step": 2, "action": "Request carrier use CarrierLink app", "button": "Send App Invite"},
                {"step": 3, "action": "Verify carrier has correct contact info", "button": "Verify Contact"},
            ],
            "email_template": "assign_tracking_device",
        },
        "carrier_api_down": {
            "description": "Carrier API is experiencing issues or is unavailable",
            "checks": [
                {"field": "carrier_patterns.tracking_success_rate", "expected_lt": 0.5, "weight": 8},
                {"field": "tracking.status", "expected": "in_transit", "weight": 3},
            ],
            "resolution_steps": [
                {"step": 1, "action": "Check carrier API status page", "button": "Check Status"},
                {"step": 2, "action": "Escalate to carrier operations", "button": "Escalate"},
                {"step": 3, "action": "Use fallback tracking method", "button": "Fallback"},
            ],
            "email_template": "api_issue_notification",
        },
        "load_not_found": {
            "description": "Load does not exist in the tracking system",
            "checks": [
                {"field": "tracking.load_found", "expected": False, "weight": 10},
            ],
            "resolution_steps": [
                {"step": 1, "action": "Verify load number is correct", "button": "Verify"},
                {"step": 2, "action": "Check if load was created correctly", "button": "Check Creation"},
                {"step": 3, "action": "Contact shipper to confirm load details", "button": "Contact Shipper"},
            ],
            "email_template": None,
        },
    }

    def __init__(self):
        super().__init__("Hypothesis Agent")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and evaluate hypotheses."""
        self.log_start("Generating hypotheses from evidence")

        data_results = context.get("data_results", [])

        # Flatten data results into a single dict for evaluation
        evidence = self._flatten_evidence(data_results, context)

        # Evaluate each pattern
        hypotheses = []
        for pattern_id, pattern in self.PATTERNS.items():
            confidence = self._evaluate_pattern(pattern, evidence)

            if confidence > 0:
                hypotheses.append(HypothesisResult(
                    pattern_id=pattern_id,
                    description=pattern["description"],
                    confidence=confidence,
                    supporting_evidence=self._get_supporting_evidence(pattern, evidence),
                    resolution_steps=pattern["resolution_steps"],
                    email_template=pattern.get("email_template"),
                ))

        # Sort by confidence (highest first)
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        self.log_success(f"Generated {len(hypotheses)} hypotheses")
        if hypotheses:
            self.log_success(f"Top hypothesis: {hypotheses[0].pattern_id} ({hypotheses[0].confidence:.0%})")

        return {
            "hypotheses": hypotheses,
            "top_hypothesis": hypotheses[0] if hypotheses else None,
            "total_evaluated": len(self.PATTERNS),
        }

    def _flatten_evidence(
        self,
        data_results: List[Dict],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Flatten all evidence into a single dict for pattern matching."""
        evidence = {
            "tracking": {},
            "network": {},
            "redshift": {},
            "carrier_patterns": {},
        }

        # Add context data
        for key in ["tracking_id", "load_number", "shipper", "carrier"]:
            if key in context:
                evidence["tracking"][key] = context[key]

        # Add data results
        for result in data_results:
            if result is None:
                continue
            if "load_found" in result:
                evidence["tracking"].update(result)
            elif "network_found" in result:
                evidence["network"].update(result)
            elif "load_history" in result:
                evidence["redshift"].update(result)
                if "carrier_patterns" in result and result["carrier_patterns"]:
                    evidence["carrier_patterns"].update(result["carrier_patterns"])

        return evidence

    def _evaluate_pattern(
        self,
        pattern: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> float:
        """Evaluate a pattern against evidence, return confidence 0.0-1.0."""
        total_weight = 0
        matched_weight = 0

        for check in pattern.get("checks", []):
            weight = check.get("weight", 1)
            total_weight += weight

            # Parse field path (e.g., "network.eld_enabled")
            field_path = check["field"].split(".")
            value = evidence
            for part in field_path:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            # Evaluate check
            matched = False
            if "expected" in check:
                expected = check["expected"]
                if check.get("inverse"):
                    matched = (value != expected)
                else:
                    matched = (value == expected)
            elif "expected_lt" in check:
                if value is not None:
                    matched = (value < check["expected_lt"])
            elif "expected_gt" in check:
                if value is not None:
                    matched = (value > check["expected_gt"])

            if matched:
                matched_weight += weight

        if total_weight == 0:
            return 0.0

        return matched_weight / total_weight

    def _get_supporting_evidence(
        self,
        pattern: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get list of evidence that supports this pattern."""
        supporting = []

        for check in pattern.get("checks", []):
            field_path = check["field"].split(".")
            value = evidence
            for part in field_path:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            if value is not None or check.get("expected") is None:
                supporting.append({
                    "field": check["field"],
                    "value": value,
                    "expected": check.get("expected", check.get("expected_lt", check.get("expected_gt"))),
                    "weight": check.get("weight", 1),
                })

        return supporting


class SynthesisAgent(BaseInvestigationAgent):
    """Agent 6: Synthesize final root cause and generate resolution.

    Responsibilities:
    - Select best hypothesis as root cause
    - Generate human-readable explanation
    - Create actionable resolution steps
    - Generate email template if applicable
    """

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.65
    LOW_CONFIDENCE = 0.40

    def __init__(self):
        super().__init__("Synthesis Agent")

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize root cause and resolution."""
        self.log_start("Synthesizing root cause and resolution")

        hypotheses = context.get("hypotheses", [])

        if not hypotheses:
            self.log_warning("No hypotheses to synthesize")
            return self._create_unknown_result(context)

        # Get top hypothesis
        top_hypothesis = hypotheses[0] if isinstance(hypotheses[0], HypothesisResult) else hypotheses[0]
        confidence = top_hypothesis.confidence if isinstance(top_hypothesis, HypothesisResult) else top_hypothesis.get("confidence", 0)

        # Determine confidence level
        confidence_level = self._get_confidence_level(confidence)

        # Generate resolution
        resolution = self._generate_resolution(top_hypothesis, context)

        self.log_success(f"Root cause: {top_hypothesis.description if isinstance(top_hypothesis, HypothesisResult) else top_hypothesis.get('description')}")
        self.log_success(f"Confidence: {confidence:.0%} ({confidence_level})")

        return {
            "root_cause": top_hypothesis.description if isinstance(top_hypothesis, HypothesisResult) else top_hypothesis.get("description"),
            "confidence": confidence,
            "confidence_level": confidence_level,
            "resolution": resolution,
            "primary_action": resolution.get("steps", [{}])[0] if resolution.get("steps") else None,
            "email_template": top_hypothesis.email_template if isinstance(top_hypothesis, HypothesisResult) else top_hypothesis.get("email_template"),
        }

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to human-readable level."""
        if confidence >= self.HIGH_CONFIDENCE:
            return "high"
        elif confidence >= self.MEDIUM_CONFIDENCE:
            return "medium"
        elif confidence >= self.LOW_CONFIDENCE:
            return "low"
        else:
            return "very_low"

    def _generate_resolution(
        self,
        hypothesis: HypothesisResult,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate resolution from hypothesis."""
        if isinstance(hypothesis, HypothesisResult):
            steps = hypothesis.resolution_steps
            pattern_id = hypothesis.pattern_id
        else:
            steps = hypothesis.get("resolution_steps", [])
            pattern_id = hypothesis.get("pattern_id")

        # Personalize steps with context
        carrier = context.get("carrier", {})
        carrier_name = carrier.get("name", "the carrier") if isinstance(carrier, dict) else "the carrier"
        load_number = context.get("load_number", "the load")

        personalized_steps = []
        for step in steps:
            step_copy = dict(step)
            # Replace placeholders
            if "action" in step_copy:
                step_copy["action"] = step_copy["action"].replace(
                    "{carrier_name}", carrier_name
                ).replace(
                    "{load_number}", str(load_number)
                )
            personalized_steps.append(step_copy)

        return {
            "pattern_id": pattern_id,
            "steps": personalized_steps,
            "estimated_resolution_time": self._estimate_resolution_time(pattern_id),
            "requires_human_approval": True,
            "escalation_path": self._get_escalation_path(pattern_id),
        }

    def _estimate_resolution_time(self, pattern_id: str) -> str:
        """Estimate time to resolve based on pattern."""
        time_estimates = {
            "eld_not_enabled": "5-10 minutes",
            "network_missing": "15-30 minutes",
            "no_tracking_device": "1-4 hours",
            "carrier_api_down": "1-24 hours",
            "load_not_found": "15-60 minutes",
        }
        return time_estimates.get(pattern_id, "Unknown")

    def _get_escalation_path(self, pattern_id: str) -> List[str]:
        """Get escalation path for pattern."""
        escalation_paths = {
            "eld_not_enabled": ["Carrier Ops", "CSM"],
            "network_missing": ["Network Team", "CSM"],
            "no_tracking_device": ["Carrier Ops", "Carrier Manager", "CSM"],
            "carrier_api_down": ["Carrier Ops", "Engineering", "CSM"],
            "load_not_found": ["Load Creation Team", "CSM"],
        }
        return escalation_paths.get(pattern_id, ["CSM"])

    def _create_unknown_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create result when no clear root cause found."""
        return {
            "root_cause": "Unable to determine root cause - manual investigation required",
            "confidence": 0.0,
            "confidence_level": "very_low",
            "resolution": {
                "pattern_id": "unknown",
                "steps": [
                    {"step": 1, "action": "Review load details manually", "button": "View Load"},
                    {"step": 2, "action": "Check recent system logs", "button": "View Logs"},
                    {"step": 3, "action": "Escalate to engineering if needed", "button": "Escalate"},
                ],
                "estimated_resolution_time": "Unknown",
                "requires_human_approval": True,
                "escalation_path": ["CSM", "Engineering"],
            },
            "primary_action": {"step": 1, "action": "Review load details manually", "button": "View Load"},
            "email_template": None,
        }


class MultiAgentInvestigator:
    """
    Orchestrates multi-agent investigation with real-time progress.

    This is the main entry point for running investigations. It coordinates
    all agents and provides progress callbacks for UI updates.

    Usage:
        investigator = MultiAgentInvestigator()
        result = await investigator.investigate(
            context={"ticket_id": "SF-12345", "load_number": "U110123982"},
            progress_callback=lambda step: print(f"{step.name}: {step.status}")
        )
    """

    def __init__(
        self,
        tracking_api_client=None,
        redshift_client=None,
        company_api_client=None,
    ):
        """Initialize investigator with optional API clients.

        Args:
            tracking_api_client: TrackingAPIClient instance (optional)
            redshift_client: RedshiftClient instance (optional)
            company_api_client: CompanyAPIClient instance (optional)
        """
        # Initialize agents
        self.identifier_agent = IdentifierAgent()
        self.tracking_api_agent = TrackingAPIAgent(tracking_api_client)
        self.redshift_agent = RedshiftAgent(redshift_client)
        self.network_agent = NetworkAgent(company_api_client)
        self.hypothesis_agent = HypothesisAgent()
        self.synthesis_agent = SynthesisAgent()

        self.logger = logging.getLogger(__name__)

    async def investigate(
        self,
        context: Dict[str, Any],
        progress_callback: Optional[Callable[[AgentStep], None]] = None,
    ) -> InvestigationResult:
        """
        Run investigation with progressive agent execution.

        Args:
            context: Investigation context containing:
                - ticket_id: str (e.g., "SF-12345")
                - load_number: str (optional)
                - tracking_id: str (optional)
                - shipper: str or dict (optional)
                - carrier: str or dict (optional)
                - description: str (optional, ticket description)
            progress_callback: Called after each agent step with status update

        Returns:
            InvestigationResult with root cause, confidence, and resolution
        """
        start_time = datetime.now()
        steps: List[AgentStep] = []

        self.logger.info(f"Starting investigation for ticket {context.get('ticket_id', 'unknown')}")

        # Step 1: Identifier Agent - Extract and validate IDs
        identifier_step = await self._run_agent(
            agent=self.identifier_agent,
            context=context,
            progress_callback=progress_callback,
        )
        steps.append(identifier_step)

        if identifier_step.status == AgentStatus.FAILED:
            return self._create_failed_result(context, steps, start_time)

        # Merge identifier results into context
        identifiers = identifier_step.result or {}
        merged_context = {**context, **identifiers}

        # Step 2: Tracking API Agent - Get load status
        tracking_step = await self._run_agent(
            agent=self.tracking_api_agent,
            context=merged_context,
            progress_callback=progress_callback,
        )
        steps.append(tracking_step)

        # Update context with tracking results
        if tracking_step.result:
            merged_context.update(tracking_step.result)

        # Steps 3-4: Run data collection agents in parallel
        data_agents = [
            (self.redshift_agent, merged_context),
            (self.network_agent, merged_context),
        ]

        parallel_results = await self._run_agents_parallel(
            agents=data_agents,
            progress_callback=progress_callback,
        )
        steps.extend(parallel_results)

        # Collect all data results for hypothesis generation
        data_results = [
            tracking_step.result,
            *[r.result for r in parallel_results],
        ]

        # Step 5: Hypothesis Agent - Generate hypotheses
        hypothesis_context = {
            **merged_context,
            "data_results": data_results,
        }
        hypothesis_step = await self._run_agent(
            agent=self.hypothesis_agent,
            context=hypothesis_context,
            progress_callback=progress_callback,
        )
        steps.append(hypothesis_step)

        # Step 6: Synthesis Agent - Determine root cause
        synthesis_context = {
            **merged_context,
            "hypotheses": hypothesis_step.result.get("hypotheses", []) if hypothesis_step.result else [],
        }
        synthesis_step = await self._run_agent(
            agent=self.synthesis_agent,
            context=synthesis_context,
            progress_callback=progress_callback,
        )
        steps.append(synthesis_step)

        # Build final result
        duration = (datetime.now() - start_time).total_seconds()

        synthesis = synthesis_step.result or {}
        hypotheses = hypothesis_step.result.get("hypotheses", []) if hypothesis_step.result else []

        return InvestigationResult(
            ticket_id=context.get("ticket_id", ""),
            load_number=merged_context.get("load_number"),
            tracking_id=str(merged_context.get("tracking_id")) if merged_context.get("tracking_id") else None,
            confidence=synthesis.get("confidence", 0.0),
            confidence_level=self._get_confidence_level(synthesis.get("confidence", 0.0)),
            root_cause=synthesis.get("root_cause", "Unknown"),
            hypotheses=hypotheses,
            resolution=synthesis.get("resolution", {}),
            evidence_summary=self._build_evidence_summary(steps),
            investigation_time_seconds=duration,
            steps=steps,
            skill_used=context.get("skill_used", "otr-rca"),
            skill_version=context.get("skill_version", "1.0.0"),
            shipper=merged_context.get("shipper"),
            carrier=merged_context.get("carrier"),
        )

    async def _run_agent(
        self,
        agent: BaseInvestigationAgent,
        context: Dict[str, Any],
        progress_callback: Optional[Callable[[AgentStep], None]],
    ) -> AgentStep:
        """Run a single agent with status tracking."""
        step = AgentStep(name=agent.name, status=AgentStatus.PENDING)

        if progress_callback:
            progress_callback(step)

        step.status = AgentStatus.RUNNING
        step.started_at = datetime.now()

        if progress_callback:
            progress_callback(step)

        try:
            result = await agent.execute(context)
            step.status = AgentStatus.COMPLETED
            step.result = result
            step.findings = self._extract_findings(agent.name, result)
        except Exception as e:
            step.status = AgentStatus.FAILED
            step.error = str(e)
            self.logger.error(f"Agent {agent.name} failed: {e}")

        step.completed_at = datetime.now()
        step.duration_ms = int((step.completed_at - step.started_at).total_seconds() * 1000)

        if progress_callback:
            progress_callback(step)

        return step

    async def _run_agents_parallel(
        self,
        agents: List[Tuple[BaseInvestigationAgent, Dict[str, Any]]],
        progress_callback: Optional[Callable[[AgentStep], None]],
    ) -> List[AgentStep]:
        """Run multiple agents in parallel."""
        tasks = [
            self._run_agent(agent, context, progress_callback)
            for agent, context in agents
        ]
        return await asyncio.gather(*tasks)

    def _extract_findings(
        self,
        agent_name: str,
        result: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings from agent result for display."""
        findings = []

        if not result:
            return findings

        if agent_name == "Identifier Agent":
            if result.get("tracking_id"):
                findings.append(f"Tracking ID: {result['tracking_id']}")
            if result.get("load_number"):
                findings.append(f"Load Number: {result['load_number']}")

        elif agent_name == "Tracking API Agent":
            if result.get("load_found"):
                findings.append(f"Load found: {result.get('status', 'unknown')}")
                if result.get("tracking_method"):
                    findings.append(f"Tracking: {result['tracking_method']}")
            else:
                findings.append("Load not found in system")

        elif agent_name == "Redshift Agent":
            if result.get("carrier_patterns"):
                patterns = result["carrier_patterns"]
                if "tracking_success_rate" in patterns:
                    findings.append(f"Carrier success rate: {patterns['tracking_success_rate']:.0%}")

        elif agent_name == "Network Agent":
            if result.get("network_found"):
                findings.append("Network relationship found")
                if result.get("eld_enabled") is False:
                    findings.append("ELD NOT enabled")
                elif result.get("eld_enabled"):
                    findings.append("ELD enabled")
            else:
                findings.append("No network relationship")

        elif agent_name == "Hypothesis Agent":
            hypotheses = result.get("hypotheses", [])
            findings.append(f"Evaluated {result.get('total_evaluated', 0)} patterns")
            if hypotheses:
                top = hypotheses[0]
                if isinstance(top, HypothesisResult):
                    findings.append(f"Top: {top.pattern_id} ({top.confidence:.0%})")
                else:
                    findings.append(f"Top: {top.get('pattern_id')} ({top.get('confidence', 0):.0%})")

        elif agent_name == "Synthesis Agent":
            if result.get("confidence"):
                findings.append(f"Confidence: {result['confidence']:.0%}")
            if result.get("root_cause"):
                # Truncate long root cause
                cause = result["root_cause"]
                if len(cause) > 50:
                    cause = cause[:47] + "..."
                findings.append(f"Cause: {cause}")

        return findings

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to human-readable level."""
        if confidence >= 0.85:
            return "high"
        elif confidence >= 0.65:
            return "medium"
        elif confidence >= 0.40:
            return "low"
        else:
            return "very_low"

    def _build_evidence_summary(self, steps: List[AgentStep]) -> List[Dict[str, Any]]:
        """Build summary of evidence from all agent steps."""
        summary = []

        for step in steps:
            if step.status == AgentStatus.COMPLETED and step.result:
                summary.append({
                    "agent": step.name,
                    "status": "success",
                    "duration_ms": step.duration_ms,
                    "findings": step.findings,
                })
            elif step.status == AgentStatus.FAILED:
                summary.append({
                    "agent": step.name,
                    "status": "failed",
                    "error": step.error,
                })

        return summary

    def _create_failed_result(
        self,
        context: Dict[str, Any],
        steps: List[AgentStep],
        start_time: datetime,
    ) -> InvestigationResult:
        """Create result when investigation fails early."""
        duration = (datetime.now() - start_time).total_seconds()

        return InvestigationResult(
            ticket_id=context.get("ticket_id", ""),
            load_number=context.get("load_number"),
            tracking_id=context.get("tracking_id"),
            confidence=0.0,
            confidence_level="very_low",
            root_cause="Investigation failed - unable to extract identifiers",
            hypotheses=[],
            resolution={
                "steps": [
                    {"step": 1, "action": "Verify ticket contains valid load information"},
                    {"step": 2, "action": "Manually search for load in system"},
                ],
                "requires_human_approval": True,
            },
            evidence_summary=self._build_evidence_summary(steps),
            investigation_time_seconds=duration,
            steps=steps,
            skill_used=context.get("skill_used", "otr-rca"),
            skill_version=context.get("skill_version", "1.0.0"),
        )

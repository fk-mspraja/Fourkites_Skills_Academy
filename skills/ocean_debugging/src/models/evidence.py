"""Evidence models for tracking investigation findings"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Type of evidence source"""
    DATABASE = "database"
    API = "api"
    LOG = "log"
    LLM = "llm"
    COMPUTED = "computed"


class EvidenceSource(str, Enum):
    """Source system for evidence"""
    PLATFORM = "platform"
    TRACKING_API = "tracking_api"
    SUPER_API = "super_api"
    JUSTTRANSFORM = "justtransform"
    SIGNOZ = "signoz"
    REDSHIFT = "redshift"
    DATA_HUB = "data_hub"
    S3 = "s3"
    LLM = "llm"


class Finding(BaseModel):
    """A single finding from evidence analysis"""
    key: str
    value: Any
    is_anomaly: bool = False
    anomaly_description: Optional[str] = None


class Evidence(BaseModel):
    """
    A piece of evidence collected during investigation.

    Evidence is accumulated from multiple sources and used
    by the decision engine to determine root cause.
    """

    id: str = Field(default_factory=lambda: f"ev_{datetime.utcnow().timestamp()}")

    # Classification
    type: EvidenceType
    source: EvidenceSource
    step_id: str

    # Content
    finding: str  # Human-readable summary
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)

    # Scoring
    confidence: float = 1.0  # How confident we are in this evidence
    weight: float = 1.0  # How important this evidence is for decisions

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query_time_ms: Optional[float] = None

    def supports_root_cause(self, root_cause: str) -> bool:
        """Check if this evidence supports a particular root cause"""
        # Map root causes to evidence patterns
        patterns = {
            "network_relationship_missing": [
                "no relationship",
                "relationship not found",
                "count: 0",
                "empty result"
            ],
            "jt_scraping_error": [
                "crawled differs from formatted",
                "parsing error",
                "jt error"
            ],
            "carrier_portal_issue": [
                "carrier data incorrect",
                "portal shows wrong"
            ],
            "configuration_issue": [
                "subscription not found",
                "identifier mismatch",
                "tracking not configured"
            ],
            "system_bug": [
                "all sources agree",
                "platform shows different"
            ]
        }

        keywords = patterns.get(root_cause, [])
        finding_lower = self.finding.lower()

        return any(kw in finding_lower for kw in keywords)

    @classmethod
    def from_database_query(
        cls,
        source: EvidenceSource,
        step_id: str,
        finding: str,
        raw_data: Dict[str, Any],
        query_time_ms: float
    ) -> "Evidence":
        """Create evidence from a database query result"""
        return cls(
            type=EvidenceType.DATABASE,
            source=source,
            step_id=step_id,
            finding=finding,
            raw_data=raw_data,
            query_time_ms=query_time_ms
        )

    @classmethod
    def from_api_response(
        cls,
        source: EvidenceSource,
        step_id: str,
        finding: str,
        raw_data: Dict[str, Any],
        query_time_ms: float
    ) -> "Evidence":
        """Create evidence from an API response"""
        return cls(
            type=EvidenceType.API,
            source=source,
            step_id=step_id,
            finding=finding,
            raw_data=raw_data,
            query_time_ms=query_time_ms
        )

    @classmethod
    def from_log_analysis(
        cls,
        step_id: str,
        finding: str,
        raw_data: Dict[str, Any],
        query_time_ms: float
    ) -> "Evidence":
        """Create evidence from log analysis"""
        return cls(
            type=EvidenceType.LOG,
            source=EvidenceSource.SIGNOZ,
            step_id=step_id,
            finding=finding,
            raw_data=raw_data,
            query_time_ms=query_time_ms
        )

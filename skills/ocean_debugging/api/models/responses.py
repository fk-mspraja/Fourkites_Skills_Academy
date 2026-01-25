"""Response models for Auto-RCA API"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class SSEEvent(BaseModel):
    """Base SSE event"""
    event: str
    data: Dict[str, Any]


class InvestigationResponse(BaseModel):
    """Complete investigation result"""
    investigation_id: str
    case_number: str
    root_cause: Optional[str]
    confidence: float
    evidence_count: int
    duration_seconds: float
    recommendations: List[str]

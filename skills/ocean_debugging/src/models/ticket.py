"""Salesforce ticket models"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TicketIdentifiers(BaseModel):
    """Identifiers extracted from a support ticket"""

    # Load identifiers
    load_id: Optional[str] = None
    tracking_id: Optional[str] = None

    # Ocean-specific identifiers
    container_number: Optional[str] = None
    booking_number: Optional[str] = None
    bill_of_lading: Optional[str] = None

    # Entity identifiers
    carrier_id: Optional[str] = None
    carrier_name: Optional[str] = None
    shipper_id: Optional[str] = None
    shipper_name: Optional[str] = None

    # Time context
    issue_date: Optional[datetime] = None
    expected_event_date: Optional[datetime] = None

    # Additional context
    mode: str = "OCEAN"
    raw_extractions: Dict[str, Any] = Field(default_factory=dict)

    @property
    def primary_identifier(self) -> Optional[str]:
        """Get the primary identifier for tracking lookup"""
        # Priority: booking_number > bill_of_lading > container_number
        if self.booking_number:
            return self.booking_number
        if self.bill_of_lading:
            return self.bill_of_lading
        if self.container_number:
            return self.container_number
        return self.load_id

    @property
    def primary_identifier_type(self) -> Optional[str]:
        """Get the type of primary identifier"""
        if self.booking_number:
            return "booking_number"
        if self.bill_of_lading:
            return "bill_of_lading"
        if self.container_number:
            return "container_number"
        if self.load_id:
            return "load_id"
        return None

    def has_minimum_identifiers(self) -> bool:
        """Check if we have minimum identifiers for investigation"""
        return bool(self.primary_identifier)

    def to_query_params(self) -> Dict[str, Any]:
        """Convert to parameters for API/database queries"""
        params = {}
        if self.load_id:
            params["load_id"] = self.load_id
        if self.container_number:
            params["container_number"] = self.container_number
        if self.booking_number:
            params["booking_number"] = self.booking_number
        if self.carrier_id:
            params["carrier_id"] = self.carrier_id
        if self.shipper_id:
            params["shipper_id"] = self.shipper_id
        return params


class SalesforceTicket(BaseModel):
    """A Salesforce support ticket/case"""

    # Salesforce IDs
    id: str  # Salesforce record ID
    case_number: str  # Human-readable case number

    # Content
    subject: str
    description: Optional[str] = None

    # Status
    status: str = "New"
    priority: str = "Medium"

    # Customer context
    account_name: Optional[str] = None
    contact_name: Optional[str] = None

    # Timestamps
    created_date: datetime = Field(default_factory=datetime.utcnow)
    last_modified_date: Optional[datetime] = None

    # Custom fields (FourKites specific)
    load_id: Optional[str] = None
    issue_category: Optional[str] = None
    mode: Optional[str] = None

    # Metadata
    raw_record: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_sf_record(cls, record: Dict[str, Any]) -> "SalesforceTicket":
        """Create ticket from Salesforce API response"""
        return cls(
            id=record.get("Id", ""),
            case_number=record.get("CaseNumber", ""),
            subject=record.get("Subject", ""),
            description=record.get("Description"),
            status=record.get("Status", "New"),
            priority=record.get("Priority", "Medium"),
            account_name=record.get("Account", {}).get("Name") if record.get("Account") else None,
            contact_name=record.get("Contact", {}).get("Name") if record.get("Contact") else None,
            created_date=datetime.fromisoformat(
                record.get("CreatedDate", "").replace("Z", "+00:00")
            ) if record.get("CreatedDate") else datetime.utcnow(),
            last_modified_date=datetime.fromisoformat(
                record.get("LastModifiedDate", "").replace("Z", "+00:00")
            ) if record.get("LastModifiedDate") else None,
            load_id=record.get("Load_ID__c"),
            issue_category=record.get("Issue_Category__c"),
            mode=record.get("Mode__c"),
            raw_record=record
        )

    def get_searchable_text(self) -> str:
        """Get combined text for identifier extraction"""
        parts = [self.subject]
        if self.description:
            parts.append(self.description)
        return "\n".join(parts)

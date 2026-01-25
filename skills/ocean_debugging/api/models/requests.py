"""Request models for Auto-RCA API"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class InvestigateRequest(BaseModel):
    """Request to investigate a case"""

    case_number: Optional[str] = Field(
        None,
        description="Salesforce case number (e.g., 00123456)"
    )

    load_id: Optional[str] = Field(
        None,
        description="FourKites load ID (tracking_id)"
    )

    load_number: Optional[str] = Field(
        None,
        description="Customer load number"
    )

    shipper_id: Optional[str] = Field(
        None,
        description="Shipper company ID (optional, improves lookup speed when using load_number)"
    )

    mode: str = Field(
        default="ocean",
        description="Investigation mode: ocean, rail, air, otr, yard"
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        allowed = ['ocean', 'rail', 'air', 'otr', 'yard']
        if v not in allowed:
            raise ValueError(f'mode must be one of {allowed}')
        return v

    @model_validator(mode='after')
    def check_identifier_provided(self):
        # Check if at least one identifier is provided
        if not any([self.case_number, self.load_id, self.load_number]):
            raise ValueError('Must provide at least one identifier: case_number, load_id, or load_number')
        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "case_number": "00123456",
                    "mode": "ocean"
                },
                {
                    "load_id": "614258134",
                    "mode": "ocean"
                },
                {
                    "load_number": "U110123982",
                    "shipper_id": "nestle-usa",
                    "mode": "ocean"
                }
            ]
        }

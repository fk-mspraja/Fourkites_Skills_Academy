"""Salesforce API client for ticket retrieval"""

from typing import Any, Dict, List, Optional

from simple_salesforce import Salesforce

from core.clients.base_client import BaseClient, ClientError
from core.models.ticket import SalesforceTicket
from core.utils.config import SalesforceConfig
from core.utils.logging import get_logger

logger = get_logger(__name__)


class TicketNotFoundError(ClientError):
    """Ticket not found in Salesforce"""
    pass


class SalesforceClient(BaseClient):
    """
    Salesforce API client for reading support tickets.

    Uses simple_salesforce library for API communication.
    """

    def __init__(self, config: Optional[SalesforceConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or SalesforceConfig.from_env()

    def _create_connection(self) -> Salesforce:
        """Create Salesforce connection"""
        return Salesforce(
            instance_url=self.config.instance_url,
            username=self.config.username,
            password=self.config.password,
            security_token=self.config.security_token,
        )

    def _query_case(self, case_number: str) -> Dict[str, Any]:
        """Execute SOQL query for case"""
        sf = self._get_connection()

        query = f"""
            SELECT
                Id,
                CaseNumber,
                Subject,
                Description,
                Status,
                Priority,
                CreatedDate,
                LastModifiedDate,
                Account.Name,
                Contact.Name,
                Load_ID__c,
                Issue_Category__c,
                Mode__c
            FROM Case
            WHERE CaseNumber = '{case_number}'
            LIMIT 1
        """

        result = sf.query(query)

        if not result.get("records"):
            raise TicketNotFoundError(f"Case {case_number} not found")

        return result["records"][0]

    async def get_ticket(self, case_number: str) -> SalesforceTicket:
        """
        Get a support ticket by case number.

        Args:
            case_number: Salesforce case number (e.g., "00123456")

        Returns:
            SalesforceTicket model

        Raises:
            TicketNotFoundError: If case not found
        """
        record = await self.execute_with_retry(
            self._query_case,
            case_number,
            operation_name="get_ticket"
        )

        return SalesforceTicket.from_sf_record(record)

    def _query_cases_by_load(self, load_id: str) -> List[Dict[str, Any]]:
        """Query cases by load ID"""
        sf = self._get_connection()

        query = f"""
            SELECT
                Id,
                CaseNumber,
                Subject,
                Status,
                CreatedDate
            FROM Case
            WHERE Load_ID__c = '{load_id}'
            ORDER BY CreatedDate DESC
            LIMIT 10
        """

        result = sf.query(query)
        return result.get("records", [])

    async def get_cases_by_load(self, load_id: str) -> List[Dict[str, Any]]:
        """Get all cases for a load ID"""
        return await self.execute_with_retry(
            self._query_cases_by_load,
            load_id,
            operation_name="get_cases_by_load"
        )

    def _update_case(self, case_id: str, fields: Dict[str, Any]) -> None:
        """Update case fields"""
        sf = self._get_connection()
        sf.Case.update(case_id, fields)

    async def update_case_with_rca(
        self,
        case_id: str,
        root_cause: str,
        category: str,
        confidence: float,
        explanation: str
    ) -> None:
        """
        Update case with RCA analysis results.

        Args:
            case_id: Salesforce case ID
            root_cause: Determined root cause
            category: Root cause category
            confidence: Confidence score
            explanation: Analysis explanation
        """
        fields = {
            "RCA_Root_Cause__c": root_cause,
            "RCA_Category__c": category,
            "RCA_Confidence__c": confidence,
            "RCA_Explanation__c": explanation[:32000] if explanation else None,
            "RCA_Status__c": "Analyzed",
        }

        await self.execute_with_retry(
            self._update_case,
            case_id,
            fields,
            operation_name="update_case_with_rca"
        )

        logger.info(f"Updated case {case_id} with RCA results")

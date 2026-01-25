"""FourKites Super API client for internal tracking configuration"""

from typing import Any, Dict, Optional

import requests

from .base_client import BaseClient
from utils.config import SuperApiConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class SuperApiClient(BaseClient):
    """
    FourKites Super API client.

    Internal API for tracking configuration, subscriptions, and system details.
    """

    def __init__(self, config: Optional[SuperApiConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or SuperApiConfig.from_env()
        self._session: Optional[requests.Session] = None

    def _create_connection(self) -> requests.Session:
        """Create requests session with API key"""
        session = requests.Session()
        session.headers.update({
            "X-Super-Key": self.config.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        return session

    def _http_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Execute HTTP GET request"""
        session = self._get_connection()
        url = f"{self.config.base_url}{endpoint}"

        response = session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    async def get_tracking_config(self, load_id: str) -> Dict[str, Any]:
        """
        Get tracking configuration for a load.

        Shows how the load is being tracked (identifier, source, subscription).

        Args:
            load_id: FourKites load ID

        Returns:
            Dict with tracking configuration
        """
        endpoint = f"/v1/tracking/config/{load_id}"

        try:
            result = await self.execute_with_retry(
                self._http_get,
                endpoint,
                operation_name="get_tracking_config"
            )

            return {
                "exists": True,
                "tracking_id": result.get("tracking_id"),
                "primary_identifier": result.get("primary_identifier"),
                "identifier_value": result.get("identifier_value"),
                "subscription_id": result.get("subscription_id"),
                "tracking_source": result.get("tracking_source"),
                "is_active": result.get("is_active", False),
                "multi_source": result.get("multi_source", False),
                "sources": result.get("sources", [])
            }

        except Exception as e:
            if "404" in str(e):
                return {
                    "exists": False,
                    "load_id": load_id,
                    "error": "No tracking configuration found"
                }
            raise

    async def get_subscription_details(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Get details of a tracking subscription.

        Args:
            subscription_id: Subscription ID (usually JT subscription)

        Returns:
            Dict with subscription details
        """
        endpoint = f"/v1/subscriptions/{subscription_id}"

        try:
            result = await self.execute_with_retry(
                self._http_get,
                endpoint,
                operation_name="get_subscription_details"
            )

            return {
                "exists": True,
                "subscription_id": subscription_id,
                "status": result.get("status"),
                "source": result.get("source"),
                "identifier_type": result.get("identifier_type"),
                "identifier_value": result.get("identifier_value"),
                "carrier_id": result.get("carrier_id"),
                "created_date": result.get("created_date"),
                "last_update": result.get("last_update")
            }

        except Exception as e:
            if "404" in str(e):
                return {
                    "exists": False,
                    "subscription_id": subscription_id,
                    "error": "Subscription not found"
                }
            raise

    async def get_load_identifiers(self, load_id: str) -> Dict[str, Any]:
        """
        Get all identifiers associated with a load.

        Args:
            load_id: FourKites load ID

        Returns:
            Dict with all load identifiers
        """
        endpoint = f"/v1/loads/{load_id}/identifiers"

        result = await self.execute_with_retry(
            self._http_get,
            endpoint,
            operation_name="get_load_identifiers"
        )

        return {
            "load_id": load_id,
            "container_number": result.get("container_number"),
            "booking_number": result.get("booking_number"),
            "bill_of_lading": result.get("bill_of_lading"),
            "carrier_booking_ref": result.get("carrier_booking_ref"),
            "additional": result.get("additional_identifiers", {})
        }

    async def get_carrier_integration(
        self,
        carrier_id: str
    ) -> Dict[str, Any]:
        """
        Get integration details for a carrier.

        Shows what tracking methods are available for this carrier.

        Args:
            carrier_id: Carrier ID

        Returns:
            Dict with carrier integration info
        """
        endpoint = f"/v1/carriers/{carrier_id}/integration"

        result = await self.execute_with_retry(
            self._http_get,
            endpoint,
            operation_name="get_carrier_integration"
        )

        return {
            "carrier_id": carrier_id,
            "carrier_name": result.get("name"),
            "has_api": result.get("api_integration", False),
            "has_edi": result.get("edi_integration", False),
            "has_rpa": result.get("rpa_integration", False),
            "preferred_source": result.get("preferred_source"),
            "supported_identifiers": result.get("supported_identifiers", [])
        }

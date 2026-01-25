"""FourKites Super API client for internal tracking configuration"""

from typing import Any, Dict, Optional
import base64

import requests

from core.clients.base_client import BaseClient
from core.utils.config import SuperApiConfig, config
from core.utils.logging import get_logger

logger = get_logger(__name__)


class SuperApiClient(BaseClient):
    """
    FourKites Super API client (DataHub API).

    Internal API for tracking configuration, subscriptions, and system details.
    Uses Basic Auth with FK_API credentials.
    """

    def __init__(self, config_obj: Optional[SuperApiConfig] = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config_obj or SuperApiConfig.from_env()
        self._session: Optional[requests.Session] = None

        # Use FK_API credentials for Basic Auth
        self.user = config.FK_API_USER
        self.password = config.FK_API_PASSWORD

    def _create_connection(self) -> requests.Session:
        """Create requests session with Basic Auth"""
        session = requests.Session()

        # Use Basic Auth (same as Tracking API)
        if self.user and self.password:
            credentials = f"{self.user}:{self.password}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            session.headers.update({
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
        else:
            logger.warning("Super API credentials not configured")

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
        Get tracking configuration for a load from DataHub API.

        Shows how the load is being tracked (identifier, source, subscription).

        Args:
            load_id: FourKites load ID

        Returns:
            Dict with tracking configuration
        """
        # DataHub API endpoint: /api/v1/super/{load_id}
        endpoint = f"/api/v1/super/{load_id}"

        logger.info("=" * 80)
        logger.info(f"🌐 SUPER API (DataHub) CALL")
        logger.info("-" * 80)
        logger.info(f"Endpoint: GET {self.config.base_url}{endpoint}")
        logger.info(f"Load ID: {load_id}")
        logger.info(f"Auth: Basic {self.user}")
        logger.info("=" * 80)

        try:
            result = await self.execute_with_retry(
                self._http_get,
                endpoint,
                operation_name="get_tracking_config"
            )

            logger.info("=" * 80)
            logger.info(f"✅ SUPER API SUCCESS")
            logger.info("-" * 80)
            logger.info(f"Load ID: {load_id}")
            logger.info(f"Response keys: {list(result.keys())[:10]}")
            logger.info("=" * 80)

            # DataHub API returns full load data - extract tracking config
            return {
                "exists": True,
                "tracking_id": result.get("tracking_id") or result.get("id"),
                "primary_identifier": result.get("primary_identifier") or result.get("containerNumber") or result.get("loadNumber"),
                "identifier_value": result.get("identifier_value"),
                "subscription_id": result.get("subscription_id"),
                "tracking_source": result.get("tracking_source") or result.get("trackingMethod"),
                "is_active": result.get("is_active", True),
                "multi_source": result.get("multi_source", False),
                "sources": result.get("sources", []),
                "_raw": result  # Keep full response for debugging
            }

        except requests.exceptions.HTTPError as e:
            logger.error("=" * 80)
            logger.error(f"❌ SUPER API HTTP ERROR")
            logger.error("-" * 80)
            logger.error(f"Load ID: {load_id}")
            logger.error(f"Status Code: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)

            if hasattr(e, 'response') and e.response.status_code == 404:
                return {
                    "exists": False,
                    "load_id": load_id,
                    "error": "No tracking configuration found"
                }
            raise
        except Exception as e:
            logger.error(f"Super API error: {e}")
            return {
                "exists": False,
                "load_id": load_id,
                "error": str(e)
            }

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

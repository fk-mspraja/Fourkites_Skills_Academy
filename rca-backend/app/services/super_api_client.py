"""
Super API Client (DataHub)
Internal tracking configuration and subscription management
"""
import os
import logging
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class SuperAPIClient:
    """Client for Super API (DataHub) - internal tracking configuration"""

    def __init__(self):
        self.base_url = os.getenv("DATAHUB_API_BASE_URL")
        self.username = os.getenv("FK_API_USER")
        self.password = os.getenv("FK_API_PASSWORD")
        self.timeout = 20.0

        if not self.base_url:
            logger.warning("DataHub API base URL not configured")
        if not self.username or not self.password:
            logger.warning("DataHub API credentials not configured")

    async def get_tracking_config(self, load_id: str) -> Dict:
        """
        Get internal tracking configuration for a load

        Args:
            load_id: Tracking ID or load number

        Returns:
            {
                "load_id": str,
                "primary_identifier": str,
                "subscription_id": str,
                "tracking_source": str (e.g., "JT", "API", "EDI"),
                "carrier_code": str,
                "subscription_status": str,
                "config": Dict
            }
        """
        try:
            url = f"{self.base_url}/v1/tracking/config/{load_id}"
            auth = (self.username, self.password)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "load_id": load_id,
                    "primary_identifier": data.get("primary_identifier"),
                    "subscription_id": data.get("subscription_id"),
                    "tracking_source": data.get("tracking_source"),
                    "carrier_code": data.get("carrier_code"),
                    "subscription_status": data.get("subscription_status"),
                    "config": data.get("config", {}),
                    "exists": True
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Tracking config not found for load: {load_id}")
                return {
                    "load_id": load_id,
                    "exists": False,
                    "error": "Not found"
                }
            logger.error(f"Super API HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "load_id": load_id,
                "exists": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Super API error: {str(e)}")
            return {
                "load_id": load_id,
                "exists": False,
                "error": str(e)
            }

    async def get_subscription_details(self, subscription_id: str) -> Dict:
        """
        Get detailed subscription information

        Args:
            subscription_id: JT/carrier subscription ID

        Returns:
            {
                "subscription_id": str,
                "carrier": str,
                "portal_url": str,
                "credentials_status": str,
                "last_scrape": str (ISO),
                "scraping_enabled": bool,
                "error_count": int
            }
        """
        try:
            url = f"{self.base_url}/v1/subscriptions/{subscription_id}"
            auth = (self.username, self.password)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "subscription_id": subscription_id,
                    "carrier": data.get("carrier_name"),
                    "portal_url": data.get("portal_url"),
                    "credentials_status": data.get("credentials_status"),
                    "last_scrape": data.get("last_scrape_timestamp"),
                    "scraping_enabled": data.get("enabled", False),
                    "error_count": data.get("recent_error_count", 0),
                    "exists": True
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "subscription_id": subscription_id,
                    "exists": False,
                    "error": "Subscription not found"
                }
            logger.error(f"Subscription API error: {e.response.status_code}")
            return {
                "subscription_id": subscription_id,
                "exists": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Subscription API error: {str(e)}")
            return {
                "subscription_id": subscription_id,
                "exists": False,
                "error": str(e)
            }

    async def get_ocean_events(self, identifier: str, identifier_type: str = "container") -> Dict:
        """
        Get all ocean events from DataHub Ocean SuperAPI.
        This returns the complete list of carrier events for a container/booking.

        Args:
            identifier: Container number, booking number, or BL number
            identifier_type: One of "container", "booking", "bl"

        Returns:
            {
                "identifier": str,
                "events": [
                    {
                        "event_code": str (e.g., "VA", "VD", "GT", "DL"),
                        "event_name": str,
                        "event_time": str (ISO),
                        "location": str,
                        "vessel": str,
                        "voyage": str,
                        "source": str (e.g., "carrier_api", "edi", "scraped"),
                        "received_at": str (ISO)
                    }
                ],
                "carrier_code": str,
                "carrier_name": str,
                "last_update": str (ISO),
                "exists": bool
            }
        """
        try:
            # DataHub Ocean SuperAPI endpoint
            url = f"{self.base_url}/v1/ocean/events"
            params = {
                identifier_type: identifier
            }
            auth = (self.username, self.password)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    auth=auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                events = data.get("events", [])

                return {
                    "identifier": identifier,
                    "identifier_type": identifier_type,
                    "events": events,
                    "event_count": len(events),
                    "carrier_code": data.get("carrier_code"),
                    "carrier_name": data.get("carrier_name"),
                    "last_update": data.get("last_update"),
                    "vessel": data.get("vessel"),
                    "voyage": data.get("voyage"),
                    "exists": len(events) > 0
                }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Ocean events not found for {identifier_type}: {identifier}")
                return {
                    "identifier": identifier,
                    "identifier_type": identifier_type,
                    "events": [],
                    "event_count": 0,
                    "exists": False,
                    "error": "Not found"
                }
            logger.error(f"Ocean events API error: {e.response.status_code} - {e.response.text}")
            return {
                "identifier": identifier,
                "identifier_type": identifier_type,
                "events": [],
                "event_count": 0,
                "exists": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Ocean events API error: {str(e)}")
            return {
                "identifier": identifier,
                "identifier_type": identifier_type,
                "events": [],
                "event_count": 0,
                "exists": False,
                "error": str(e)
            }

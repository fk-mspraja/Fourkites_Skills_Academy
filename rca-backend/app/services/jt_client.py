"""
Just Transform (JT) API Client
RPA scraping history from carrier portals for Ocean tracking
"""
import os
import logging
from typing import Dict, List, Optional
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JTClient:
    """Client for Just Transform RPA scraping history API"""

    def __init__(self):
        self.base_url = os.getenv("JT_API_BASE_URL", "https://just-transform.fourkites.com")
        self.username = os.getenv("FK_API_USER")
        self.password = os.getenv("FK_API_PASSWORD")
        self.timeout = 30.0

        if not self.username or not self.password:
            logger.warning("JT API credentials not configured")

    async def get_subscription_history(
        self,
        subscription_id: str,
        days: int = 7
    ) -> Dict:
        """
        Get RPA scraping history for a subscription

        Args:
            subscription_id: JT subscription ID
            days: Number of days to look back (default 7)

        Returns:
            {
                "subscription_id": str,
                "events_count": int,
                "history": List[Dict],
                "discrepancies": List[Dict],
                "has_errors": bool,
                "error_count": int,
                "last_successful_scrape": str (ISO),
                "scraping_frequency": str
            }
        """
        try:
            url = f"{self.base_url}/api/v1/ocean/subscriptions/{subscription_id}/history"
            params = {"days": days}
            auth = (self.username, self.password)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                # Enrich with error analysis
                events = data.get("history", [])
                errors = [e for e in events if e.get("status") == "error"]

                return {
                    "subscription_id": subscription_id,
                    "events_count": len(events),
                    "history": events,
                    "discrepancies": data.get("discrepancies", []),
                    "has_errors": len(errors) > 0,
                    "error_count": len(errors),
                    "last_successful_scrape": self._find_last_success(events),
                    "scraping_frequency": data.get("frequency", "unknown")
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"JT API HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "subscription_id": subscription_id,
                "error": f"HTTP {e.response.status_code}",
                "has_errors": True,
                "events_count": 0
            }
        except Exception as e:
            logger.error(f"JT API error: {str(e)}")
            return {
                "subscription_id": subscription_id,
                "error": str(e),
                "has_errors": True,
                "events_count": 0
            }

    def _find_last_success(self, events: List[Dict]) -> Optional[str]:
        """Find the most recent successful scrape timestamp"""
        successes = [
            e for e in events
            if e.get("status") == "success" and e.get("timestamp")
        ]
        if successes:
            # Sort by timestamp descending
            successes.sort(key=lambda x: x["timestamp"], reverse=True)
            return successes[0]["timestamp"]
        return None

    async def get_container_events(
        self,
        container_number: str,
        days: int = 14
    ) -> Dict:
        """
        Get all scraping events for a specific container

        Args:
            container_number: Container number (e.g., ABCD1234567)
            days: Number of days to look back

        Returns:
            {
                "container_number": str,
                "events": List[Dict],
                "has_data": bool,
                "last_update": str (ISO)
            }
        """
        try:
            url = f"{self.base_url}/api/v1/ocean/containers/{container_number}/events"
            params = {"days": days}
            auth = (self.username, self.password)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                events = data.get("events", [])
                return {
                    "container_number": container_number,
                    "events": events,
                    "has_data": len(events) > 0,
                    "last_update": events[0].get("timestamp") if events else None
                }

        except httpx.HTTPStatusError as e:
            logger.warning(f"Container not found in JT: {container_number}")
            return {
                "container_number": container_number,
                "events": [],
                "has_data": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"JT container events error: {str(e)}")
            return {
                "container_number": container_number,
                "events": [],
                "has_data": False,
                "error": str(e)
            }

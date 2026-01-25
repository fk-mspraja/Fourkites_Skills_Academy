"""Just Transform API client for scraping history"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import requests
from requests.auth import HTTPBasicAuth

from .base_client import BaseClient
from utils.config import JustTransformConfig
from utils.logging import get_logger

logger = get_logger(__name__)


class JustTransformClient(BaseClient):
    """
    Just Transform (JT) API client for web scraping history.

    JT is the RPA/web scraping vendor that scrapes carrier portals.
    """

    def __init__(self, config: Optional[JustTransformConfig] = None, **kwargs):
        super().__init__(timeout=60.0, **kwargs)  # JT can be slow
        self.config = config or JustTransformConfig.from_env()
        self._session: Optional[requests.Session] = None

    def _create_connection(self) -> requests.Session:
        """Create requests session with auth"""
        session = requests.Session()
        session.auth = HTTPBasicAuth(
            self.config.username,
            self.config.password
        )
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        return session

    def _http_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Execute HTTP GET request"""
        session = self._get_connection()
        url = f"{self.config.api_url}{endpoint}"

        response = session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.json()

    async def get_subscription_history(
        self,
        subscription_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get scraping history for a JT subscription.

        Args:
            subscription_id: JT subscription ID
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            days_back: Days to look back if dates not specified

        Returns:
            Dict with scraping history
        """
        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.utcnow().strftime("%Y-%m-%d")

        endpoint = f"/api/v1/ocean/subscriptions/{subscription_id}/history"
        params = {
            "from_date": from_date,
            "to_date": to_date
        }

        result = await self.execute_with_retry(
            self._http_get,
            endpoint,
            params,
            operation_name="get_subscription_history"
        )

        # Process history to identify issues
        history = result.get("history", [])
        events_count = len(history)

        # Analyze for discrepancies
        discrepancies = []
        for event in history:
            crawled = event.get("crawled_output", {})
            formatted = event.get("response", {})

            # Compare key fields
            crawled_time = crawled.get("event_time")
            formatted_time = formatted.get("event_time")

            if crawled_time and formatted_time and crawled_time != formatted_time:
                discrepancies.append({
                    "event_id": event.get("event_id"),
                    "field": "event_time",
                    "crawled": crawled_time,
                    "formatted": formatted_time
                })

        return {
            "subscription_id": subscription_id,
            "events_count": events_count,
            "history": history[:50],  # Return first 50 for detail
            "discrepancies": discrepancies,
            "has_discrepancies": len(discrepancies) > 0,
            "date_range": {"from": from_date, "to": to_date}
        }

    async def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific JT event.

        Includes raw crawled data vs formatted response for comparison.

        Args:
            event_id: JT event ID

        Returns:
            Dict with event details
        """
        endpoint = f"/api/v1/ocean/events/{event_id}"

        result = await self.execute_with_retry(
            self._http_get,
            endpoint,
            operation_name="get_event_details"
        )

        # Compare crawled vs formatted
        crawled = result.get("crawled_output", {})
        formatted = result.get("formatted_response", {})

        differences = {}
        for key in set(crawled.keys()) | set(formatted.keys()):
            crawled_val = crawled.get(key)
            formatted_val = formatted.get(key)
            if crawled_val != formatted_val:
                differences[key] = {
                    "crawled": crawled_val,
                    "formatted": formatted_val
                }

        return {
            "event_id": event_id,
            "crawled_output": crawled,
            "formatted_response": formatted,
            "differences": differences,
            "has_differences": len(differences) > 0,
            "screenshot_url": result.get("carrier_portal_screenshot")
        }

    async def check_subscription_status(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Check the status of a JT subscription.

        Args:
            subscription_id: JT subscription ID

        Returns:
            Dict with subscription status
        """
        endpoint = f"/api/v1/ocean/subscriptions/{subscription_id}"

        result = await self.execute_with_retry(
            self._http_get,
            endpoint,
            operation_name="check_subscription_status"
        )

        return {
            "subscription_id": subscription_id,
            "status": result.get("status", "unknown"),
            "carrier": result.get("carrier_name"),
            "identifier_type": result.get("identifier_type"),
            "identifier_value": result.get("identifier_value"),
            "last_crawl": result.get("last_crawl_time"),
            "crawl_frequency": result.get("crawl_frequency_hours"),
            "is_active": result.get("status") == "ACTIVE"
        }

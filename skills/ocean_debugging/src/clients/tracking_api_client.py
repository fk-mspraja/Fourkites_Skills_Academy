"""
Tracking API Client for FourKites
Queries live tracking data using HMAC-SHA1 authentication
"""

import base64
import hashlib
import hmac
import urllib.parse as urlparse
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import logging

from utils.config import config

logger = logging.getLogger(__name__)


class TrackingAPIClient:
    """Client for FourKites Tracking API with HMAC or Basic authentication."""

    def __init__(self):
        """Initialize the Tracking API client."""
        self.base_url = config.TRACKING_API_BASE_URL
        self.auth_method = config.FK_API_AUTH_METHOD

        # HMAC auth credentials
        self.app_id = config.FK_API_APP_ID
        self.secret = config.FK_API_SECRET

        # Basic auth credentials
        self.user = config.FK_API_USER
        self.password = config.FK_API_PASSWORD

        # Validate configuration based on auth method
        if self.auth_method == "basic":
            if not self.user or not self.password:
                logger.warning(
                    "FK_API_USER or FK_API_PASSWORD not configured. "
                    "Tracking API queries will not be available."
                )
        elif self.auth_method == "hmac":
            if not self.secret:
                logger.warning(
                    "FK_API_SECRET not configured. "
                    "Tracking API queries will not be available."
                )
        else:
            logger.error(
                f"Invalid FK_API_AUTH_METHOD: {self.auth_method}. "
                "Must be 'basic' or 'hmac'."
            )

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers based on configured auth method.

        Returns:
            Dict with Authorization header
        """
        if self.auth_method == "basic":
            # Basic Auth: Base64 encode "username:password"
            credentials = f"{self.user}:{self.password}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            return {
                "Authorization": f"Basic {encoded}"
            }
        else:
            # HMAC auth doesn't use headers - uses URL parameters
            return {}

    def build_url(
        self,
        endpoint: str,
        query_params: Dict[str, str]
    ) -> str:
        """
        Build URL with authentication.
        For Basic Auth: simple URL with query params
        For HMAC: URL with signature in query params

        Args:
            endpoint: API endpoint (e.g., "/api/v1/tracking")
            query_params: Query parameters dict

        Returns:
            Full URL (with HMAC signature if using HMAC auth)
        """
        if self.auth_method == "basic":
            # Basic auth: simple URL construction
            if query_params:
                url = f"{self.base_url}{endpoint}?{urlparse.urlencode(query_params, doseq=True)}"
            else:
                url = f"{self.base_url}{endpoint}"
            logger.debug(f"Basic auth URL: {url}")
            return url
        else:
            # HMAC auth: build signed URL
            return self._build_signed_url_hmac(endpoint, query_params)

    def _build_signed_url_hmac(
        self,
        endpoint: str,
        query_params: Dict[str, str]
    ) -> str:
        """
        Build a fully-signed URL for HMAC-protected endpoints.

        Args:
            endpoint: API endpoint (e.g., "/api/v1/tracking")
            query_params: Query parameters dict

        Returns:
            Fully signed URL with HMAC signature
        """
        # Use UTC time for timestamp
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        # Generate HMAC-SHA1 signature using standard base64 (not urlsafe)
        signature_bytes = hmac.new(
            self.secret.encode('utf-8'),
            f"{self.app_id}--{ts}".encode('utf-8'),
            hashlib.sha1
        ).digest()

        # Use standard base64 encoding (produces +, /, = characters)
        signature = base64.b64encode(signature_bytes).decode('utf-8')

        # Build query parameters (signature will be URL-encoded by urlencode)
        qp = dict(query_params)
        qp.update({
            "app_id": self.app_id,
            "timestamp": ts,
            "signature": signature
        })

        # Build the full URL
        url = f"{self.base_url}{endpoint}?{urlparse.urlencode(qp, doseq=True)}"

        # Debug logging
        logger.debug(f"HMAC signature generation:")
        logger.debug(f"  Secret length: {len(self.secret)} chars")
        logger.debug(f"  Message: {self.app_id}--{ts}")
        logger.debug(f"  Signature (base64): {signature}")
        logger.debug(f"  Final URL: {url}")

        return url

    def get_tracking_by_load_number(
        self,
        load_number: str,
        company_id: Optional[str] = None,
        locale: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Get tracking data using load_ids query parameter (simple GET endpoint).

        This is the FASTEST way to lookup a load by load_number.
        Uses: GET /api/v1/tracking?load_ids=X&company_id=Y

        Args:
            load_number: The load number to search for
            company_id: Optional company permalink (shipper). If not provided, searches across all companies.
            locale: Language locale (default: "en")

        Returns:
            Tracking data dict with 'loads' array if successful, None if failed

        Example:
            get_tracking_by_load_number("U110123982", "nestle-usa")
            get_tracking_by_load_number("U110123982")  # No company_id filter
        """
        # Check if API is configured
        if self.auth_method == "basic" and (not self.user or not self.password):
            logger.warning("Tracking API not configured (Basic Auth), skipping query")
            return None
        elif self.auth_method == "hmac" and not self.secret:
            logger.warning("Tracking API not configured (HMAC), skipping query")
            return None

        try:
            # Build query parameters
            query_params = {
                "load_ids": load_number,
                "locale": locale
            }

            # Add company_id only if provided
            if company_id:
                query_params["company_id"] = company_id

            # Build URL (with signature if HMAC)
            url = self.build_url(
                endpoint="/api/v1/tracking",
                query_params=query_params
            )

            # Get auth headers (Basic Auth header or empty dict for HMAC)
            headers = self.get_auth_headers()

            # Log the API call
            logger.info("=" * 80)
            logger.info(f"🌐 TRACKING API GET BY LOAD_NUMBER")
            logger.info("-" * 80)
            logger.info(f"Endpoint: GET {self.base_url}/api/v1/tracking")
            logger.info(f"Load Number: {load_number}")
            logger.info(f"Company ID: {company_id or 'Not provided (search all companies)'}")
            logger.info(f"Locale: {locale}")
            logger.info(f"Auth Method: {self.auth_method.upper()}")
            if self.auth_method == "hmac":
                logger.info(f"App ID: {self.app_id}")
            elif self.auth_method == "basic":
                logger.info(f"User: {self.user}")
            logger.info(f"Full URL: {url}")
            logger.info("=" * 80)

            # Make the GET request with timing
            import time
            start_time = time.time()

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            elapsed_time = time.time() - start_time
            data = response.json()

            # Log success with timing
            logger.info("=" * 80)
            logger.info(f"✅ TRACKING API GET SUCCESS")
            logger.info("-" * 80)
            logger.info(f"Load Number: {load_number}")
            logger.info(f"Company ID: {company_id or 'N/A'}")
            logger.info(f"Response Time: {elapsed_time:.2f} seconds")
            logger.info(f"Status Code: {response.status_code}")

            # Log results count
            if isinstance(data, dict):
                loads = data.get("loads", [])
                logger.info(f"Results Found: {len(loads)} load(s)")
                if loads:
                    load = loads[0]
                    logger.info(f"Tracking ID: {load.get('id', 'N/A')}")
                    logger.info(f"Load Number: {load.get('loadNumber', 'N/A')}")
                    logger.info(f"Status: {load.get('status', 'N/A')}")
                    logger.info(f"Shipper: {load.get('shipperName', 'N/A')}")
                    logger.info(f"Carrier: {load.get('carrierName', 'N/A')}")
            logger.info("=" * 80)

            return data

        except requests.exceptions.Timeout:
            logger.error("=" * 80)
            logger.error(f"⏱️  TRACKING API TIMEOUT")
            logger.error("-" * 80)
            logger.error(f"Load Number: {load_number}")
            logger.error(f"Company ID: {company_id or 'N/A'}")
            logger.error(f"Error: Request timed out after 30 seconds")
            logger.error("=" * 80)
            return None
        except requests.exceptions.HTTPError as http_err:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API HTTP ERROR")
            logger.error("-" * 80)
            logger.error(f"Load Number: {load_number}")
            logger.error(f"Company ID: {company_id or 'N/A'}")
            logger.error(f"Status Code: {http_err.response.status_code if hasattr(http_err, 'response') else 'Unknown'}")
            logger.error(f"Error: {http_err}")
            if hasattr(http_err, 'response') and hasattr(http_err.response, 'text'):
                logger.error(f"Response Body: {http_err.response.text[:500]}")
            logger.error("=" * 80)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API REQUEST ERROR")
            logger.error("-" * 80)
            logger.error(f"Load Number: {load_number}")
            logger.error(f"Company ID: {company_id or 'N/A'}")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)
            return None
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API UNEXPECTED ERROR")
            logger.error("-" * 80)
            logger.error(f"Load Number: {load_number}")
            logger.error(f"Company ID: {company_id or 'N/A'}")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)
            return None

    def search_tracking_by_load(
        self,
        load_number: str,
        company_id: str,
        locale: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Search for tracking data using load_number and company_id (shipper permalink).

        Args:
            load_number: The load number to search for
            company_id: The company permalink (e.g., 'fritolay', 'walmart')
            locale: Language locale (default: "en")

        Returns:
            Tracking data dict if successful, None if failed

        Example:
            search_tracking_by_load("51319037", "fritolay")
        """
        # Check if API is configured
        if self.auth_method == "basic" and (not self.user or not self.password):
            logger.warning("Tracking API not configured (Basic Auth), skipping query")
            return None
        elif self.auth_method == "hmac" and not self.secret:
            logger.warning("Tracking API not configured (HMAC), skipping query")
            return None

        try:
            # Build the search payload
            search_payload = {
                "show": "transitDays,latestEvent,lateReasonCodes,stops(etaProperties,reschedules,files,stop_attributes,appointment_time_am,extension),carrierDeliveryEta,consignmentsCount,events,ltlLoadInfo,latestEventFromUpdates,bargeLoadInfo,simultaneousTrackingReferenceNumber,splitShipments",
                "page": 0,
                "sort_by": "created_at",
                "sort_order": "desc",
                "with_files": "",
                "container_validation": "",
                "tracking_status": "",
                "all_test_loads": True,
                "onboarding_status": None,
                "skip_test_loads": False,
                "duration": 365,
                "customer": "",
                "customer_condition": "or",
                "remaining_miles": None,
                "shipper": "",
                "shipper_condition": "or",
                "linked_with": "",
                "per_page": 20,
                "load_ids": load_number,
                "search_after": []
            }

            # Build URL (with signature if HMAC)
            url = self.build_url(
                endpoint="/api/v1/tracking/search",
                query_params={
                    "company_id": company_id,
                    "locale": locale
                }
            )

            # Get auth headers (Basic Auth header or empty dict for HMAC)
            headers = self.get_auth_headers()

            # Log the API call
            logger.info("=" * 80)
            logger.info(f"🌐 TRACKING API SEARCH CALL")
            logger.info("-" * 80)
            logger.info(f"Endpoint: POST {self.base_url}/api/v1/tracking/search")
            logger.info(f"Load Number: {load_number}")
            logger.info(f"Company ID: {company_id}")
            logger.info(f"Locale: {locale}")
            logger.info(f"Auth Method: {self.auth_method.upper()}")
            if self.auth_method == "hmac":
                logger.info(f"App ID: {self.app_id}")
            elif self.auth_method == "basic":
                logger.info(f"User: {self.user}")
            logger.info(f"Full URL: {url}")
            logger.info(f"Payload Keys: {list(search_payload.keys())}")
            logger.info(f"Payload load_ids: {search_payload.get('load_ids')}")
            logger.info("=" * 80)

            # Make the POST request with timing
            import time
            start_time = time.time()

            response = requests.post(url, json=search_payload, headers=headers, timeout=30)
            response.raise_for_status()

            elapsed_time = time.time() - start_time
            data = response.json()

            # Log success with timing
            logger.info("=" * 80)
            logger.info(f"✅ TRACKING API SEARCH SUCCESS")
            logger.info("-" * 80)
            logger.info(f"Load Number: {load_number}")
            logger.info(f"Company ID: {company_id}")
            logger.info(f"Response Time: {elapsed_time:.2f} seconds")
            logger.info(f"Status Code: {response.status_code}")

            # Log results count
            if isinstance(data, dict):
                loads = data.get("loads", [])
                logger.info(f"Results Found: {len(loads)} load(s)")
                if loads:
                    load = loads[0]
                    logger.info(f"Tracking ID: {load.get('id', 'N/A')}")
                    logger.info(f"Load Number: {load.get('loadNumber', 'N/A')}")
                    logger.info(f"Status: {load.get('status', 'N/A')}")
                    logger.info(f"Shipper: {load.get('shipperName', 'N/A')}")
                    logger.info(f"Carrier: {load.get('carrierName', 'N/A')}")
                    logger.debug(f"Full load keys: {list(load.keys())}")
            logger.info("=" * 80)

            return data

        except requests.exceptions.Timeout:
            logger.error(f"Tracking API search timed out for load {load_number}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Tracking API search failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Tracking API search: {e}")
            return None

    def get_tracking_by_id(
        self,
        tracking_id: int,
        locale: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch tracking data for a specific tracking ID.

        Args:
            tracking_id: The tracking/load ID to query
            locale: Language locale (default: "en")

        Returns:
            Tracking data dict if successful, None if failed

        Example response structure:
        {
            "load": {
                "id": 613270496,
                "loadNumber": "LOAD123",
                "shipperName": "ACME Corp",
                "carrierName": "Best Transport",
                "status": "in_transit",
                "currentLocation": {...},
                "stops": [...]
            }
        }
        """
        # Check if API is configured
        if self.auth_method == "basic" and (not self.user or not self.password):
            logger.warning("Tracking API not configured (Basic Auth), skipping query")
            return None
        elif self.auth_method == "hmac" and not self.secret:
            logger.warning("Tracking API not configured (HMAC), skipping query")
            return None

        try:
            # Build URL (with signature if HMAC)
            url = self.build_url(
                endpoint="/api/v1/tracking",
                query_params={
                    "tracking_ids": str(tracking_id),
                    "locale": locale
                }
            )

            # Get auth headers (Basic Auth header or empty dict for HMAC)
            headers = self.get_auth_headers()

            # Log the API call
            logger.info("=" * 80)
            logger.info(f"🌐 TRACKING API CALL")
            logger.info("-" * 80)
            logger.info(f"Endpoint: GET {self.base_url}/api/v1/tracking")
            logger.info(f"Tracking ID: {tracking_id}")
            logger.info(f"Locale: {locale}")
            logger.info(f"Auth Method: {self.auth_method.upper()}")
            if self.auth_method == "hmac":
                logger.info(f"App ID: {self.app_id}")
            elif self.auth_method == "basic":
                logger.info(f"User: {self.user}")
            logger.info(f"Full URL: {url}")
            logger.info("=" * 80)

            # Make the request with timing
            import time
            start_time = time.time()

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            elapsed_time = time.time() - start_time
            data = response.json()

            # Log success with timing
            logger.info("=" * 80)
            logger.info(f"✅ TRACKING API SUCCESS")
            logger.info("-" * 80)
            logger.info(f"Tracking ID: {tracking_id}")
            logger.info(f"Response Time: {elapsed_time:.2f} seconds")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Size: {len(response.content)} bytes")

            # Log key fields if available
            if "load" in data:
                load = data["load"]
                logger.info(f"Load Number: {load.get('loadNumber', 'N/A')}")
                logger.info(f"Status: {load.get('status', 'N/A')}")
                logger.info(f"Shipper: {load.get('shipperName', 'N/A')}")
                logger.info(f"Carrier: {load.get('carrierName', 'N/A')}")

            logger.info("=" * 80)

            return data

        except requests.exceptions.HTTPError as http_err:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API HTTP ERROR")
            logger.error("-" * 80)
            logger.error(f"Tracking ID: {tracking_id}")
            logger.error(f"Status Code: {http_err.response.status_code if hasattr(http_err, 'response') else 'Unknown'}")
            logger.error(f"Error: {http_err}")
            if hasattr(http_err, 'response') and hasattr(http_err.response, 'text'):
                logger.error(f"Response Body: {http_err.response.text[:500]}")  # First 500 chars
            logger.error("=" * 80)
            return None

        except requests.exceptions.Timeout as timeout_err:
            logger.error("=" * 80)
            logger.error(f"⏱️  TRACKING API TIMEOUT")
            logger.error("-" * 80)
            logger.error(f"Tracking ID: {tracking_id}")
            logger.error(f"Timeout: 30 seconds")
            logger.error(f"Error: {timeout_err}")
            logger.error("=" * 80)
            return None

        except requests.exceptions.RequestException as req_err:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API REQUEST ERROR")
            logger.error("-" * 80)
            logger.error(f"Tracking ID: {tracking_id}")
            logger.error(f"Error: {req_err}")
            logger.error("=" * 80)
            return None

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ TRACKING API UNEXPECTED ERROR")
            logger.error("-" * 80)
            logger.error(f"Tracking ID: {tracking_id}")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)
            return None

    def extract_load_metadata(self, tracking_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract key metadata from tracking API response.

        Args:
            tracking_data: Raw tracking API response

        Returns:
            Extracted metadata dict or None if parsing fails

        Example output:
        {
            "tracking_id": 613270496,
            "load_number": "LOAD123",
            "shipper_id": "acme-corp",
            "shipper_name": "ACME Corp",
            "carrier_id": "best-transport",
            "carrier_name": "Best Transport",
            "status": "in_transit",
            "created_at": "2024-12-01T10:00:00Z",
            "updated_at": "2024-12-05T15:30:00Z",
            "stops": [...],
            "current_location": {...}
        }
        """
        try:
            # Handle different response structures:
            # 1. {"load": {...}} - single load
            # 2. {"loads": [{...}]} - array of loads
            # 3. {"statusCode": 200, "loads": [{...}]} - wrapped response

            logger.debug(f"extract_load_metadata received keys: {list(tracking_data.keys())}")

            load = None
            if "loads" in tracking_data:
                # Array response
                loads = tracking_data.get("loads", [])
                logger.debug(f"Found 'loads' array with {len(loads)} items")
                if loads and len(loads) > 0:
                    load = loads[0]  # Take first load
                    logger.debug(f"Extracted first load with keys: {list(load.keys())[:10]}...")
            elif "load" in tracking_data:
                # Single load response
                load = tracking_data.get("load", {})
                logger.debug(f"Found 'load' object with keys: {list(load.keys())[:10]}...")

            if not load:
                logger.warning(f"Invalid tracking data structure - no load found. tracking_data keys: {list(tracking_data.keys())}")
                return None

            logger.debug(f"Successfully extracted load object (type: {type(load).__name__}, has {len(load)} keys)")

            # Extract shipper and carrier information
            # Handle two response formats:
            # 1. GET /tracking/{id} - nested objects: {"shipper": {"id": "...", "name": "..."}}
            # 2. POST /tracking/search - flat fields: {"shipperId": "...", "shipperName": "..."}

            # Check if we have nested objects (GET response)
            if "shipper" in load and isinstance(load.get("shipper"), dict):
                # GET response format
                shipper = load.get("shipper", {})
                carrier = load.get("carrier", {})
                managing_carrier = load.get("managingCarrier", {})
                operating_carrier = load.get("operatingCarrier", {})
            else:
                # SEARCH response format (flat fields) - normalize to nested format
                shipper = {
                    "id": load.get("shipperId"),
                    "name": load.get("shipperName")
                }
                carrier = {
                    "id": load.get("carrierId"),
                    "name": load.get("carrierName")
                }
                managing_carrier = {
                    "id": load.get("managingCarrierId"),
                    "name": load.get("managingCarrierName")
                }
                operating_carrier = {
                    "id": load.get("operatingCarrierId"),
                    "name": load.get("operatingCarrierName")
                }

            # Extract latest location from trackingStatus if available
            tracking_status = load.get("trackingStatus", {})
            latest_location = tracking_status.get("latestLocation", {})

            metadata = {
                "tracking_id": load.get("id"),
                "load_number": load.get("loadNumber"),
                "shipper_id": shipper.get("id"),
                "shipper_name": shipper.get("name"),
                "carrier_id": carrier.get("id"),
                "carrier_name": carrier.get("name"),
                "managing_carrier_id": managing_carrier.get("id"),
                "managing_carrier_name": managing_carrier.get("name"),
                "operating_carrier_id": operating_carrier.get("id"),
                "operating_carrier_name": operating_carrier.get("name"),
                "status": load.get("status"),
                "mappable_status": load.get("mappableStatus"),
                "created_at": load.get("createdAt"),
                "updated_at": load.get("updatedAt"),
                "delivered_at": load.get("deliveredAt"),
                "terminated_at": load.get("terminatedAt"),
                "expired_at": load.get("expiredAt"),
                "picked_up": load.get("pickedUp"),
                "pickup_checkcall_at": load.get("pickupCheckCallAt"),
                "delivery_checkcall_at": load.get("deliveryCheckCallAt"),
                "stops": load.get("stops", []),
                "number_of_delivery_stops": load.get("numberOfDeliveryStops"),
                "current_location": latest_location if latest_location else None,
                "tracking_method": load.get("trackingMethod"),
                "eta": tracking_status.get("deliverySchedule", {}).get("nextStopETA"),
                "carrier_eta": tracking_status.get("deliverySchedule", {}).get("nextStopCarrierETA"),
                "display_load_number": load.get("loadNumber"),  # loadNumber is the display version
                "origin": load.get("origin"),
                "destination": load.get("destination"),
                "origin_appointment_time": load.get("originAppointmentTime"),
                "destination_appointment_time": load.get("destinationAppointmentTime"),
                "load_mode": load.get("loadMode"),
                "actual_load_mode": load.get("actualLoadMode"),
                "tracking_number": load.get("trackingNumber"),
                "trailer_number": load.get("trailerNumber"),
                "truck_number": load.get("truckNumber"),
                "container_number": load.get("containerNumber"),
                "rail_equipment_initials": load.get("railEquipmentInitials"),
                "rail_equipment_number": load.get("railEquipmentNumber"),
                "latest_checkcall_at": load.get("latestCheckCallAt"),
                "first_checkcall_at": load.get("firstCheckCallAt"),
                # Load identifiers for carrier file matching
                "reference_numbers": load.get("referenceNumbers", []),
                "bol_number": load.get("bolNumber"),
                "po_number": load.get("poNumber"),
                "pro_number": load.get("proNumber"),
            }

            logger.info(
                f"Extracted metadata for {metadata['load_number']} "
                f"(tracking_id={metadata['tracking_id']})"
            )

            return metadata

        except Exception as e:
            logger.error(f"Error extracting load metadata: {e}")
            return None

    def extract_carrier_file_search_keys(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract search keys for finding carrier files in ClickHouse.

        Carrier files don't have tracking_id - they use logical identifiers:
        - load_identifier_1/2/3/4 (could be loadNumber, poNumber, bolNumber, proNumber)
        - external_id (network identifier from superFileConfigurations)

        Args:
            metadata: Extracted metadata from tracking API

        Returns:
            Dict with search keys: {
                "load_number": "...",
                "po_number": "...",
                "bol_number": "...",
                "pro_number": "...",
                "reference_numbers": [...],
                "carrier_id": "..."
            }
        """
        search_keys = {
            "load_number": metadata.get("load_number"),
            "po_number": metadata.get("po_number"),
            "bol_number": metadata.get("bol_number"),
            "pro_number": metadata.get("pro_number"),
            "reference_numbers": metadata.get("reference_numbers", []),
            "carrier_id": metadata.get("carrier_id"),
            "shipper_id": metadata.get("shipper_id"),
        }

        # Remove None values
        return {k: v for k, v in search_keys.items() if v is not None}


    def get_date_range_for_queries(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate appropriate date range for log/file queries based on load timestamps.

        Uses created_at as the anchor, and extends the window based on load lifecycle:
        - For active/in-transit loads: created_at to now
        - For delivered loads: created_at to delivered_at (+ buffer)
        - For terminated/expired: created_at to terminated_at/expired_at (+ buffer)

        Args:
            metadata: Extracted load metadata from extract_load_metadata()

        Returns:
            Dict with start_date, end_date, and time_window info

        Example:
        {
            "start_date": "2024-12-01",
            "end_date": "2024-12-08",
            "start_datetime": datetime(...),
            "end_datetime": datetime(...),
            "window_reason": "created_at to now (load in_transit)"
        }
        """
        from datetime import datetime, timedelta
        from dateutil import parser

        try:
            # Parse created_at (required)
            created_at_str = metadata.get("created_at")
            if not created_at_str:
                logger.warning("No created_at in metadata, using default 7-day window")
                end_dt = datetime.utcnow()
                start_dt = end_dt - timedelta(days=7)
                return {
                    "start_date": start_dt.strftime("%Y-%m-%d"),
                    "end_date": end_dt.strftime("%Y-%m-%d"),
                    "start_datetime": start_dt,
                    "end_datetime": end_dt,
                    "window_reason": "default 7-day window (no created_at)"
                }

            created_at = parser.parse(created_at_str) if isinstance(created_at_str, str) else created_at_str

            # Collect ALL available dates to find the true load lifecycle range
            status = metadata.get("status", "unknown").lower()
            dates = [created_at]  # Start with created_at

            # Parse and collect all available date fields
            terminated_at = metadata.get("terminated_at")
            if terminated_at:
                dates.append(parser.parse(terminated_at) if isinstance(terminated_at, str) else terminated_at)

            delivered_at = metadata.get("delivered_at")
            if delivered_at:
                dates.append(parser.parse(delivered_at) if isinstance(delivered_at, str) else delivered_at)

            expired_at = metadata.get("expired_at")
            if expired_at:
                dates.append(parser.parse(expired_at) if isinstance(expired_at, str) else expired_at)

            latest_checkcall_at = metadata.get("latest_checkcall_at")
            if latest_checkcall_at:
                dates.append(parser.parse(latest_checkcall_at) if isinstance(latest_checkcall_at, str) else latest_checkcall_at)

            delivery_checkcall_at = metadata.get("delivery_checkcall_at")
            if delivery_checkcall_at:
                dates.append(parser.parse(delivery_checkcall_at) if isinstance(delivery_checkcall_at, str) else delivery_checkcall_at)

            pickup_checkcall_at = metadata.get("pickup_checkcall_at")
            if pickup_checkcall_at:
                dates.append(parser.parse(pickup_checkcall_at) if isinstance(pickup_checkcall_at, str) else pickup_checkcall_at)

            first_checkcall_at = metadata.get("first_checkcall_at")
            if first_checkcall_at:
                dates.append(parser.parse(first_checkcall_at) if isinstance(first_checkcall_at, str) else first_checkcall_at)

            # Find min and max from all collected dates
            earliest_date = min(dates)
            latest_date = max(dates)

            # Add ±1 day buffer to ensure we capture all related data
            start_dt = earliest_date - timedelta(days=1)
            end_dt = latest_date + timedelta(days=1)

            window_reason = f"All dates ±1 day buffer (status: {status}, {len(dates)} dates analyzed)"

            logger.info(f"Date analysis: found {len(dates)} dates from {earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}")

            result = {
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "window_reason": window_reason,
                "created_at": created_at
            }

            logger.info(f"Calculated date range: {window_reason}")
            logger.info(f"  Start: {result['start_date']} ({start_dt.isoformat()})")
            logger.info(f"  End: {result['end_date']} ({end_dt.isoformat()})")

            return result

        except Exception as e:
            logger.error(f"Error calculating date range: {e}")
            # Fallback to 7-day window
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=7)
            return {
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "window_reason": "fallback 7-day window (error calculating)"
            }

    def is_configured(self) -> bool:
        """Check if Tracking API credentials are configured."""
        if self.auth_method == "basic":
            return bool(self.user and self.password and self.base_url)
        elif self.auth_method == "hmac":
            return bool(self.secret and self.app_id and self.base_url)
        else:
            return False

    def test_connection(self) -> bool:
        """
        Test Tracking API connection with a sample query.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_configured():
            logger.error("Tracking API not configured")
            return False

        try:
            # Test with a known tracking ID (you may want to use a real test ID)
            logger.info("Testing Tracking API connection...")
            result = self.get_tracking_by_id(tracking_id=610038256)

            if result:
                logger.info("✅ Tracking API connection successful")
                return True
            else:
                logger.warning("⚠️  Tracking API returned no data")
                return False

        except Exception as e:
            logger.error(f"❌ Tracking API connection failed: {e}")
            return False


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)

    client = TrackingAPIClient()

    if not client.is_configured():
        print("❌ Tracking API not configured. Set TRACKING_API_SECRET in .env")
    else:
        print("✅ Tracking API configured")
        print(f"   Base URL: {client.base_url}")
        print(f"   App ID: {client.app_id}")

        # Test with a real tracking ID
        tracking_id = 610683422
        print(f"\nQuerying tracking_id={tracking_id}...")

        data = client.get_tracking_by_id(tracking_id)

        if data:
            print("\n✅ Successfully retrieved tracking data")
            metadata = client.extract_load_metadata(data)
            if metadata:
                print("\nExtracted Metadata:")
                print(f"  Load Number: {metadata['load_number']}")
                print(f"  Shipper: {metadata['shipper_name']}")
                print(f"  Carrier: {metadata['carrier_name']}")
                print(f"  Status: {metadata['status']}")
                print(f"  Stops: {len(metadata['stops'])} stops")
        else:
            print("\n❌ Failed to retrieve tracking data")

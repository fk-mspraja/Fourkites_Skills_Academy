"""
Company API Client for FourKites
Queries company relationships using HMAC-SHA1 authentication
"""

import base64
import hashlib
import hmac
import urllib.parse as urlparse
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
import logging

from app.config import config

logger = logging.getLogger(__name__)


class CompanyAPIClient:
    """Client for FourKites Company API with HMAC or Basic authentication."""

    def __init__(self):
        """Initialize the Company API client."""
        self.base_url = config.COMPANY_API_BASE_URL or "https://company-api.fourkites.com"
        self.auth_method = config.FK_API_AUTH_METHOD

        # HMAC auth credentials
        self.app_id = config.FK_API_APP_ID or "airflow-worker"
        self.secret = config.FK_API_SECRET

        # Basic auth credentials
        self.user = config.FK_API_USER
        self.password = config.FK_API_PASSWORD

        # Validate configuration based on auth method
        if self.auth_method == "basic":
            if not self.user or not self.password:
                logger.warning(
                    "FK_API_USER or FK_API_PASSWORD not configured. "
                    "Company API queries will not be available."
                )
        elif self.auth_method == "hmac":
            if not self.secret:
                logger.warning(
                    "FK_API_SECRET not configured. "
                    "Company API queries will not be available."
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
            endpoint: API endpoint (e.g., "/api/v1/companies/shipper/relationships")
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
            endpoint: API endpoint (e.g., "/api/v1/companies/shipper/relationships")
            query_params: Query parameters dict

        Returns:
            Fully signed URL with HMAC signature
        """
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        # Use standard base64 encoding (not urlsafe) to match tracking_api_client
        signature_bytes = hmac.new(
            self.secret.encode('utf-8'),
            f"{self.app_id}--{ts}".encode('utf-8'),
            hashlib.sha1
        ).digest()
        signature = base64.b64encode(signature_bytes).decode('utf-8')

        qp = dict(query_params)
        qp.update({
            "app_id": self.app_id,
            "timestamp": ts,
            "signature": signature
        })

        url = f"{self.base_url}{endpoint}?{urlparse.urlencode(qp, doseq=True)}"

        # Debug logging
        logger.debug(f"HMAC signature generation:")
        logger.debug(f"  Secret length: {len(self.secret)} chars")
        logger.debug(f"  Message: {self.app_id}--{ts}")
        logger.debug(f"  Signature (base64): {signature}")

        return url

    def get_company_relationship(
        self,
        company_permalink: str,
        related_company_id: str,
        locale: str = "en",
        page: int = 1,
        per_page: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch company relationship data.

        Args:
            company_permalink: The company permalink (shipper_id)
            related_company_id: The related company ID (carrier_id)
            locale: Language locale (default: "en")
            page: Page number (default: 1)
            per_page: Results per page (default: 50)

        Returns:
            Relationship data dict if successful, None if failed

        Example response structure:
        {
            "statusCode": 200,
            "relationships": [{
                "id": 55,
                "allowTracking": true,
                "active": true,
                "externalId": "...",
                "allScacs": ["hirs", "hirp"],
                "superFileConfigurations": [...],
                "tlTrackingConfigurations": {...},
                "loadUpdatesConfiguration": {...},
                "targetCompany": {...},
                "modePriorityConfigurations": {...},
                "status": "live"
            }],
            "pagination": {
                "page": 1,
                "perPage": 50,
                "totalPages": 1,
                "count": 1
            }
        }
        """
        # Check if API is configured
        if self.auth_method == "basic" and (not self.user or not self.password):
            logger.warning("Company API not configured (Basic Auth), skipping query")
            return None
        elif self.auth_method == "hmac" and not self.secret:
            logger.warning("Company API not configured (HMAC), skipping query")
            return None

        try:
            endpoint = f"/api/v1/companies/{company_permalink}/relationships"
            query_params = {
                "locale": locale,
                "page": str(page),
                "per_page": str(per_page),
                "related_company_id": related_company_id
            }

            # Build URL (with signature if HMAC)
            url = self.build_url(endpoint, query_params)

            # Get auth headers (Basic Auth header or empty dict for HMAC)
            headers = self.get_auth_headers()

            # Log the API call
            logger.info("=" * 80)
            logger.info(f"🌐 COMPANY API CALL")
            logger.info("-" * 80)
            logger.info(f"Endpoint: GET {self.base_url}{endpoint}")
            logger.info(f"Company (Shipper): {company_permalink}")
            logger.info(f"Related Company (Carrier): {related_company_id}")
            logger.info(f"Locale: {locale}")
            logger.info(f"Page: {page}, Per Page: {per_page}")
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

            # Log success
            logger.info("=" * 80)
            logger.info(f"✅ COMPANY API SUCCESS")
            logger.info("-" * 80)
            logger.info(f"Response Time: {elapsed_time:.2f} seconds")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Size: {len(response.content)} bytes")

            if data.get("statusCode") == 200:
                relationships = data.get("relationships", [])
                logger.info(f"Relationships Found: {len(relationships)}")
                if relationships:
                    rel = relationships[0]
                    logger.info(f"Relationship ID: {rel.get('id', 'N/A')}")
                    logger.info(f"Active: {rel.get('active', 'N/A')}")
                    logger.info(f"Status: {rel.get('status', 'N/A')}")
                    logger.info(f"Allow Tracking: {rel.get('allowTracking', 'N/A')}")

                # Full response logging disabled (too verbose)
                # Uncomment below for debugging if needed:
                # logger.info("-" * 80)
                # logger.info("📋 FULL COMPANY API RESPONSE:")
                # logger.info("-" * 80)
                # import json
                # logger.info(json.dumps(data, indent=2, default=str))
                logger.info("=" * 80)
                return data
            else:
                logger.warning(f"Company API returned non-200 status: {data.get('statusCode')}")
                logger.info("=" * 80)
                return None

        except requests.exceptions.Timeout:
            logger.error("=" * 80)
            logger.error(f"⏱️  COMPANY API TIMEOUT")
            logger.error("-" * 80)
            logger.error(f"Company: {company_permalink}")
            logger.error(f"Related Company: {related_company_id}")
            logger.error(f"Error: Request timed out after 30 seconds")
            logger.error("=" * 80)
            return None
        except requests.exceptions.HTTPError as http_err:
            logger.error("=" * 80)
            logger.error(f"❌ COMPANY API HTTP ERROR")
            logger.error("-" * 80)
            logger.error(f"Company: {company_permalink}")
            logger.error(f"Related Company: {related_company_id}")
            logger.error(f"Status Code: {http_err.response.status_code if hasattr(http_err, 'response') else 'Unknown'}")
            logger.error(f"Error: {http_err}")
            if hasattr(http_err, 'response') and hasattr(http_err.response, 'text'):
                logger.error(f"Response Body: {http_err.response.text[:500]}")  # First 500 chars
            logger.error("=" * 80)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("=" * 80)
            logger.error(f"❌ COMPANY API REQUEST ERROR")
            logger.error("-" * 80)
            logger.error(f"Company: {company_permalink}")
            logger.error(f"Related Company: {related_company_id}")
            logger.error(f"Error: {e}")
            logger.error("=" * 80)
            return None
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ COMPANY API UNEXPECTED ERROR")
            logger.error("-" * 80)
            logger.error(f"Company: {company_permalink}")
            logger.error(f"Related Company: {related_company_id}")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error("=" * 80)
            return None

    def extract_relationship_details(
        self,
        relationship_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract key relationship details from API response.

        Args:
            relationship_data: Raw API response

        Returns:
            Simplified relationship dict with key fields
        """
        if not relationship_data or "relationships" not in relationship_data:
            return None

        relationships = relationship_data.get("relationships", [])
        if not relationships:
            return {
                "issue": "NO_RELATIONSHIP",
                "relationship_found": False
            }

        # Get first relationship (should only be one for specific carrier filter)
        rel = relationships[0]

        # Determine issue status
        issue = "RELATIONSHIP_OK"
        if not rel.get("active"):
            issue = "RELATIONSHIP_INACTIVE"
        elif rel.get("status") != "live":
            issue = "RELATIONSHIP_NOT_LIVE"
        elif not rel.get("allowTracking"):
            issue = "TRACKING_DISABLED"

        extracted = {
            "issue": issue,
            "relationship_found": True,
            "relationship_id": rel.get("id"),
            "active": rel.get("active"),
            "status": rel.get("status"),
            "allow_tracking": rel.get("allowTracking"),
            "external_id": rel.get("externalId"),
            "all_scacs": rel.get("allScacs", []),
            "super_file_configurations": rel.get("superFileConfigurations", []),
            "tl_tracking_configurations": rel.get("tlTrackingConfigurations", {}),
            "load_updates_configuration": rel.get("loadUpdatesConfiguration", {}),
            "target_company": rel.get("targetCompany", {}),
            "mode_priority_configurations": rel.get("modePriorityConfigurations", {}),
            "relationship_type": rel.get("relationshipType"),
            "created_at": rel.get("createdAt")
        }

        # Print extracted relationship details
        logger.info("=" * 80)
        logger.info("🔍 EXTRACTED RELATIONSHIP DETAILS:")
        logger.info("-" * 80)
        import json
        logger.info(json.dumps(extracted, indent=2, default=str))
        logger.info("=" * 80)

        return extracted

    def extract_carrier_file_identifiers(
        self,
        relationship_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract carrier file identifier configuration from superFileConfigurations.

        This tells us which logical identifiers the carrier uses when sending files:
        - identifier1 could be "loadNumber"
        - identifier2 could be "poNumber"
        - etc.

        Args:
            relationship_details: Output from extract_relationship_details()

        Returns:
            Dict with:
            {
                "external_id": "USPSTMS",
                "identifier_mappings": {
                    "identifier1": "loadNumber",
                    "identifier2": "poNumber",
                    "identifier3": "bolNumber",
                    "identifier4": "proNumber"
                }
            }

        Example superFileConfigurations:
        [
            {
                "id": 67145,
                "identifier1": {"key": "loadNumber", "type": "identifier", "regex": null},
                "identifier2": {"key": null, "type": "identifier", "regex": null},
                "identifier3": {"key": null, "type": "identifier", "regex": null},
                "identifier4": {"key": null, "type": "identifier", "regex": null}
            }
        ]
        """
        if not relationship_details:
            return {"external_id": None, "identifier_mappings": {}}

        external_id = relationship_details.get("external_id")
        super_file_configs = relationship_details.get("super_file_configurations", [])

        if not super_file_configs:
            return {"external_id": external_id, "identifier_mappings": {}}

        # Take first configuration (usually only one)
        config = super_file_configs[0]

        # Extract identifier mappings
        identifier_mappings = {}
        for i in range(1, 5):  # identifier1 through identifier4
            identifier_key = f"identifier{i}"
            identifier_config = config.get(identifier_key, {})
            if identifier_config and isinstance(identifier_config, dict):
                key = identifier_config.get("key")
                if key:
                    identifier_mappings[f"load_identifier_{i}"] = key.lower()

        return {
            "external_id": external_id,
            "identifier_mappings": identifier_mappings
        }

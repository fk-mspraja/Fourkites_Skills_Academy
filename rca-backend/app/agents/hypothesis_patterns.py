"""
Hypothesis Patterns - Extracted from Agent Cassie Knowledge Base

This module contains structured hypothesis patterns for root cause analysis,
derived from Cassie's investigation prompts and knowledge base. These patterns
help the hypothesis agent form and validate hypotheses during investigation.

Categories of Root Causes (from Cassie's load_not_found_prompt.py):
1. Load Not Found - Various reasons why loads aren't visible
2. Network/Relationship Issues - Configuration problems between companies
3. SCAC Validation Failures - Carrier code issues
4. Load Creation Failures - Validation errors during creation
5. Data/Integration Issues - TMS/API problems

Evidence patterns follow a Bayesian-style approach where:
- evidence_for increases confidence
- evidence_against decreases confidence
- Weight indicates strength of evidence (0.0-1.0)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class RootCauseCategory(str, Enum):
    """Root cause categories from Cassie's knowledge base"""

    # Load Visibility Issues
    LOAD_NOT_FOUND = "load_not_found"
    LOAD_DELETED = "load_deleted"
    LOAD_ASSIGNED_DIFFERENT_CARRIER = "load_assigned_different_carrier"
    LOAD_CREATION_FAILED = "load_creation_failed"

    # Network/Configuration Issues
    NETWORK_RELATIONSHIP_MISSING = "network_relationship_missing"
    NETWORK_RELATIONSHIP_INACTIVE = "network_relationship_inactive"
    SCAC_NOT_CONFIGURED = "scac_not_configured"
    SCAC_NOT_SENT = "scac_not_sent"
    SCAC_WRONG_CODE = "scac_wrong_code"

    # Tracking Issues
    TRACKING_NOT_STARTED = "tracking_not_started"
    TRACKING_SOURCE_ISSUE = "tracking_source_issue"
    JT_SCRAPING_ERROR = "jt_scraping_error"
    OCEAN_SUBSCRIPTION_ISSUE = "ocean_subscription_issue"

    # Data/Integration Issues
    VALIDATION_ERROR = "validation_error"
    DUPLICATE_LOAD = "duplicate_load"
    MISSING_REQUIRED_FIELDS = "missing_required_fields"
    TMS_INTEGRATION_ISSUE = "tms_integration_issue"

    # GPS/Device Tracking Issues (from Cassie feedback - LOAD_NOT_TRACKING)
    GPS_NULL_TIMESTAMPS = "gps_null_timestamps"
    GPS_STALE_LOCATION = "gps_stale_location"
    DEVICE_TYPE_MISMATCH = "device_type_mismatch"
    ELD_NOT_ENABLED = "eld_not_enabled"
    GPS_PROVIDER_ISSUE = "gps_provider_issue"
    DEVICE_NOT_ASSIGNED = "device_not_assigned"

    # System Issues
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class EvidencePattern:
    """Pattern for evidence that supports or refutes a hypothesis"""
    source: str  # Data source: "Tracking API", "Redshift", "JT", etc.
    condition: str  # What to check
    finding_template: str  # Template for the finding description
    supports_hypothesis: bool  # True = evidence for, False = evidence against
    weight: float  # 0.0-1.0, how strong is this evidence
    validation_query: Optional[str] = None  # SQL/API call to validate


@dataclass
class HypothesisPattern:
    """
    A pattern for a specific hypothesis type.

    This captures the investigation logic from Cassie's prompts
    into a structured format our hypothesis agent can use.
    """
    id: str
    category: RootCauseCategory
    description: str
    triggers: List[str]  # What symptoms trigger this hypothesis
    evidence_patterns: List[EvidencePattern] = field(default_factory=list)
    validation_queries: List[str] = field(default_factory=list)
    resolution_templates: Dict[str, str] = field(default_factory=dict)  # By case_source
    confidence_threshold: float = 0.80  # Min confidence to conclude


# =============================================================================
# HYPOTHESIS PATTERNS FROM CASSIE'S KNOWLEDGE BASE
# =============================================================================

LOAD_NOT_FOUND_PATTERNS = [
    HypothesisPattern(
        id="H_LOAD_EXISTS_DIFFERENT_CARRIER",
        category=RootCauseCategory.LOAD_ASSIGNED_DIFFERENT_CARRIER,
        description="Load exists in FourKites but is assigned to a different carrier",
        triggers=[
            "carrier cannot find load",
            "load not showing in portal",
            "load missing from dashboard",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking API",
                condition="load_found AND carrier_permalink != case_source_carrier",
                finding_template="Load {load_number} found but assigned to different carrier",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="load exists in fact_loads with different carrier_id",
                finding_template="DWH confirms load assigned to carrier_id={carrier_id}",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load_found AND carrier_permalink == case_source_carrier",
                finding_template="Load correctly assigned to requesting carrier",
                supports_hypothesis=False,
                weight=0.90,
            ),
        ],
        validation_queries=[
            # From Cassie's load_not_found_prompt.py
            """
            SELECT tracking_id, load_number, carrier_name, carrier_permalink,
                   shipper_name, shipper_permalink, status
            FROM hadoop.fact_loads
            WHERE load_number = '{load_number}'
              AND etl_active_flag = 'Y'
            ORDER BY created_at DESC
            LIMIT 1
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The load is available for the given shipper but not assigned to your company. "
                "Please reach out to the shipper ({shipper_name}) to verify the carrier assignment "
                "if this load is expected to be assigned to your company."
            ),
            "SHIPPER": (
                "Load {load_number} is currently assigned to {carrier_name}. "
                "If this assignment is incorrect, you can reassign the load to the correct carrier "
                "in your FourKites portal or TMS system."
            ),
        },
    ),

    HypothesisPattern(
        id="H_LOAD_CREATION_FAILED_VALIDATION",
        category=RootCauseCategory.LOAD_CREATION_FAILED,
        description="Load creation failed due to validation errors",
        triggers=[
            "load not found",
            "load never created",
            "validation error",
            "load creation failure",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="record in load_validation_data_mart with status='Create Failure'",
                finding_template="Load creation failed: {error_message}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="load_id IS NULL in load_validation_data_mart",
                finding_template="No FourKites load_id generated - creation never succeeded",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load exists with valid tracking_id",
                finding_template="Load exists in system with tracking_id={tracking_id}",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # From Cassie's load_not_found_prompt.py - OPTIMIZED with date filter
            """
            SELECT load_number, load_id, status, error, company_name, processed_at
            FROM hadoop.load_validation_data_mart
            WHERE load_number = '{load_number}'
              AND processed_at >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY processed_at DESC
            LIMIT 10
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "Load {load_number} failed to create due to validation errors. "
                "Please contact the shipper ({shipper_name}) to verify the load was sent correctly "
                "and request they correct any issues and resubmit."
            ),
            "SHIPPER": (
                "Load {load_number} creation failed with error: {error_message}. "
                "Please correct the issue and resubmit the load through your TMS or integration."
            ),
        },
    ),

    HypothesisPattern(
        id="H_LOAD_DELETED",
        category=RootCauseCategory.LOAD_DELETED,
        description="Load was created but later deleted from the system",
        triggers=[
            "load disappeared",
            "load was visible before",
            "load no longer showing",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="load exists with deleted_at IS NOT NULL",
                finding_template="Load was deleted on {deleted_at}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="load status = 'deleted' or 'cancelled'",
                finding_template="Load status is {status}",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load exists and is active",
                finding_template="Load is currently active in the system",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            """
            SELECT tracking_id, load_number, status, deleted_at,
                   carrier_name, shipper_name
            FROM hadoop.fact_loads
            WHERE load_number = '{load_number}'
              AND (deleted_at IS NOT NULL OR status IN ('deleted', 'cancelled'))
            ORDER BY created_at DESC
            LIMIT 1
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "Load {load_number} was deleted from the system on {deleted_at}. "
                "Please contact the shipper ({shipper_name}) to recreate the load if needed."
            ),
            "SHIPPER": (
                "Load {load_number} was deleted on {deleted_at}. "
                "To track this shipment again, please recreate the load in your system."
            ),
        },
    ),

    HypothesisPattern(
        id="H_LOAD_NEVER_SUBMITTED",
        category=RootCauseCategory.LOAD_NOT_FOUND,
        description="Load was never submitted to FourKites",
        triggers=[
            "load not found",
            "no records",
            "never received",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking API",
                condition="load not found in tracking search",
                finding_template="Load {load_number} not found in tracking system",
                supports_hypothesis=True,
                weight=0.70,  # Lower weight - could be other reasons
            ),
            EvidencePattern(
                source="Redshift",
                condition="no record in load_validation_data_mart",
                finding_template="No validation record found - load never submitted",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Redshift",
                condition="no record in fact_loads",
                finding_template="No record in DWH - load never created",
                supports_hypothesis=True,
                weight=0.85,
            ),
        ],
        validation_queries=[
            """
            SELECT COUNT(*) as record_count
            FROM hadoop.load_validation_data_mart
            WHERE load_number = '{load_number}'
              AND processed_at >= CURRENT_DATE - INTERVAL '60 days'
            """,
            """
            SELECT COUNT(*) as record_count
            FROM hadoop.fact_loads
            WHERE load_number = '{load_number}'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "No record found for load {load_number} in the last 60 days. "
                "Please contact the shipper to verify if the load was sent to FourKites "
                "and confirm the load number is correct."
            ),
            "SHIPPER": (
                "No record found for load {load_number} in the last 60 days. "
                "Please verify the load was sent to FourKites through your integration "
                "and check the load number format matches your TMS."
            ),
        },
    ),
]


NETWORK_RELATIONSHIP_PATTERNS = [
    HypothesisPattern(
        id="H_NETWORK_RELATIONSHIP_MISSING",
        category=RootCauseCategory.NETWORK_RELATIONSHIP_MISSING,
        description="No network relationship exists between shipper and carrier",
        triggers=[
            "carrier not found in network",
            "network relationship missing",
            "companies not connected",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="no record in company_relationships for shipper-carrier pair",
                finding_template="No network relationship found between {shipper_name} and {carrier_name}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Network API",
                condition="relationship_exists = False",
                finding_template="Network API confirms no relationship",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Redshift",
                condition="active relationship exists",
                finding_template="Active relationship found (ID: {relationship_id})",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # From Cassie's fourkites-query-reference-guide.md - Bidirectional check
            """
            SELECT cr.id as relationship_id, cr.status, cr.active,
                   c1.name as company_1, c2.name as company_2
            FROM hadoop.company_relationships cr
            JOIN hadoop.companies c1 ON cr.company_id = c1.id
            JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
            WHERE ((c1.permalink = '{shipper_permalink}' AND c2.permalink = '{carrier_permalink}')
                OR (c1.permalink = '{carrier_permalink}' AND c2.permalink = '{shipper_permalink}'))
              AND cr.etl_active_flag = 'Y'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "There is no network relationship configured between your company and {shipper_name}. "
                "Please contact {shipper_name} to add your company to their carrier network in FourKites Connect."
            ),
            "SHIPPER": (
                "There is no network relationship configured with carrier {carrier_name}. "
                "Please add {carrier_name} to your carrier network in FourKites Connect "
                "to enable load tracking with this carrier."
            ),
        },
    ),

    HypothesisPattern(
        id="H_NETWORK_RELATIONSHIP_INACTIVE",
        category=RootCauseCategory.NETWORK_RELATIONSHIP_INACTIVE,
        description="Network relationship exists but is inactive or not live",
        triggers=[
            "relationship inactive",
            "network not live",
            "pending relationship",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="relationship exists with active=false OR status != 'live'",
                finding_template="Relationship exists but is {status} (active={active})",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="relationship is active and live",
                finding_template="Relationship is active and live",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            """
            SELECT cr.id, cr.status, cr.active, cr.created_at, cr.updated_at
            FROM hadoop.company_relationships cr
            JOIN hadoop.companies c1 ON cr.company_id = c1.id
            JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
            WHERE ((c1.permalink = '{shipper_permalink}' AND c2.permalink = '{carrier_permalink}')
                OR (c1.permalink = '{carrier_permalink}' AND c2.permalink = '{shipper_permalink}'))
              AND cr.etl_active_flag = 'Y'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "A network relationship exists with {shipper_name} but is currently {status}. "
                "Please contact {shipper_name} to activate the relationship in FourKites Connect."
            ),
            "SHIPPER": (
                "The relationship with {carrier_name} is currently {status}. "
                "Please update the relationship status to 'live' in FourKites Connect."
            ),
        },
    ),
]


SCAC_VALIDATION_PATTERNS = [
    HypothesisPattern(
        id="H_SCAC_NOT_CONFIGURED",
        category=RootCauseCategory.SCAC_NOT_CONFIGURED,
        description="SCAC code sent in load creation is not configured in network",
        triggers=[
            "carrier not found in network",
            "SCAC not configured",
            "invalid SCAC",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="error contains 'Carrier not found in Network' AND carrier_id != 'unavailable'",
                finding_template="SCAC '{scac}' sent but not configured in network",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="SCAC exists in company_scacs for this relationship",
                finding_template="SCAC '{scac}' is properly configured",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # From Cassie's load_not_found_prompt.py - SCAC validation query
            """
            SELECT cs.scac, cs.created_at as scac_created_at, cr.id as relationship_id
            FROM hadoop.company_scacs cs
            JOIN hadoop.company_relationships cr ON cs.relationship_id = cr.id
            JOIN hadoop.companies c1 ON cr.company_id = c1.id
            JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
            WHERE UPPER(cs.scac) = UPPER('{scac}')
              AND ((cr.company_type = 'shipper' AND c1.name = '{shipper_name}')
                OR (cr.target_company_type = 'shipper' AND c2.name = '{shipper_name}'))
              AND cs.etl_active_flag = 'Y'
              AND cr.etl_active_flag = 'Y'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The SCAC code '{scac}' sent in load creation is not configured in the network "
                "with {shipper_name}. Please contact {shipper_name} to either:\n"
                "1. Add SCAC '{scac}' to your carrier relationship in FourKites Connect, OR\n"
                "2. Use a different SCAC that is already configured"
            ),
            "SHIPPER": (
                "The SCAC code '{scac}' is not configured in your network relationship. "
                "Please add this SCAC in FourKites Connect:\n"
                "1. Navigate to Carriers > [Search for carrier]\n"
                "2. Add SCAC '{scac}' to the carrier relationship\n"
                "3. Resend the load creation request"
            ),
        },
    ),

    HypothesisPattern(
        id="H_SCAC_NOT_SENT",
        category=RootCauseCategory.SCAC_NOT_SENT,
        description="No SCAC code was sent in load creation request",
        triggers=[
            "carrier not found in network",
            "carrier unavailable",
            "no SCAC",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="carrier_id = 'unavailable' OR carrier_name = 'Unavailable'",
                finding_template="No SCAC was sent in load creation request",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="carrier_id contains actual SCAC code",
                finding_template="SCAC '{scac}' was sent in request",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            """
            SELECT load_number, carrier_id, carrier_name, status, error
            FROM hadoop.load_validation_data_mart
            WHERE load_number = '{load_number}'
              AND processed_at >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY processed_at DESC
            LIMIT 1
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The load creation requests did not include a carrier SCAC code. "
                "Please contact the shipper ({shipper_name}) to verify their TMS is configured "
                "to send the carrier SCAC in load creation payloads."
            ),
            "SHIPPER": (
                "The load creation requests did not include a carrier SCAC code. "
                "Please verify that your TMS/integration is configured to send the carrier SCAC "
                "in the load creation payload. Without a carrier SCAC, FourKites cannot assign "
                "the load to a specific carrier."
            ),
        },
    ),

    HypothesisPattern(
        id="H_SCAC_ADDED_AFTER_FAILURE",
        category=RootCauseCategory.SCAC_NOT_CONFIGURED,
        description="SCAC was added to network after load creation failed",
        triggers=[
            "SCAC recently added",
            "carrier not found in network",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="scac_created_at > load_validation_processed_at",
                finding_template="SCAC was added on {scac_created_at}, after load failed on {load_failure_date}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="scac_created_at < load_validation_processed_at",
                finding_template="SCAC existed before load creation attempt",
                supports_hypothesis=False,
                weight=0.90,
            ),
        ],
        validation_queries=[
            # Compare SCAC creation date with load failure date
            """
            SELECT cs.scac, cs.created_at as scac_added_date,
                   lv.processed_at as load_failure_date
            FROM hadoop.company_scacs cs
            JOIN hadoop.company_relationships cr ON cs.relationship_id = cr.id
            CROSS JOIN (
                SELECT processed_at FROM hadoop.load_validation_data_mart
                WHERE load_number = '{load_number}'
                  AND processed_at >= CURRENT_DATE - INTERVAL '60 days'
                ORDER BY processed_at DESC LIMIT 1
            ) lv
            WHERE UPPER(cs.scac) = UPPER('{scac}')
              AND cs.etl_active_flag = 'Y'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The SCAC '{scac}' was added to the network on {scac_created_at}, "
                "but the load creation failed on {load_failure_date}. "
                "Since the SCAC is now configured, future loads should succeed. "
                "Please ask the shipper ({shipper_name}) to resend the failed loads."
            ),
            "SHIPPER": (
                "The SCAC '{scac}' was added to your network on {scac_created_at}, "
                "after the load creation failed on {load_failure_date}. "
                "Please resend the load creation request - it should now succeed."
            ),
        },
    ),
]


OCEAN_TRACKING_PATTERNS = [
    HypothesisPattern(
        id="H_OCEAN_SUBSCRIPTION_NOT_FOUND",
        category=RootCauseCategory.OCEAN_SUBSCRIPTION_ISSUE,
        description="Ocean tracking subscription not found in JT system",
        triggers=[
            "ocean tracking not working",
            "container not tracking",
            "no ocean updates",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="JT",
                condition="subscription not found for container",
                finding_template="No JT subscription found for container {container}",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Super API",
                condition="tracking_source != 'JT'",
                finding_template="Load configured for {tracking_source}, not JT scraping",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="JT",
                condition="active subscription exists",
                finding_template="Active JT subscription found",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[],
        resolution_templates={
            "CARRIER": (
                "Ocean tracking subscription not found for this container. "
                "Please verify the container number format and contact the shipper "
                "to confirm the tracking configuration."
            ),
            "SHIPPER": (
                "Ocean tracking subscription not found. Please verify:\n"
                "1. Container number is correct\n"
                "2. Shipping line is supported\n"
                "3. Subscription was created in DataHub"
            ),
        },
    ),

    HypothesisPattern(
        id="H_JT_SCRAPING_ERROR",
        category=RootCauseCategory.JT_SCRAPING_ERROR,
        description="JT RPA scraping encountered errors for this shipment",
        triggers=[
            "ocean tracking errors",
            "scraping failed",
            "JT errors",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="JT",
                condition="has_errors = True in subscription history",
                finding_template="JT scraping encountered {error_count} errors",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="JT",
                condition="recent successful scrapes",
                finding_template="JT scraping working - last success: {last_success}",
                supports_hypothesis=False,
                weight=0.85,
            ),
        ],
        validation_queries=[],
        resolution_templates={
            "CARRIER": (
                "Ocean tracking is experiencing scraping issues. "
                "This is typically a temporary issue with the carrier's portal. "
                "FourKites is monitoring and will resume tracking once resolved."
            ),
            "SHIPPER": (
                "JT scraping encountered errors for this container. "
                "Error details: {error_details}\n"
                "Our team is investigating. If the issue persists, please open a support ticket."
            ),
        },
    ),
]


DUPLICATE_LOAD_PATTERNS = [
    HypothesisPattern(
        id="H_DUPLICATE_LOAD_SUBMISSION",
        category=RootCauseCategory.DUPLICATE_LOAD,
        description="Multiple loads created with the same external reference",
        triggers=[
            "duplicate loads",
            "multiple loads same number",
            "load created twice",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Redshift",
                condition="multiple records in fact_loads with same load_number",
                finding_template="Found {count} loads with number {load_number}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Redshift",
                condition="single record exists",
                finding_template="Only one load found with this number",
                supports_hypothesis=False,
                weight=0.90,
            ),
        ],
        validation_queries=[
            """
            SELECT tracking_id, load_number, carrier_name, status,
                   created_at, deleted_at
            FROM hadoop.fact_loads
            WHERE load_number = '{load_number}'
              AND etl_active_flag = 'Y'
            ORDER BY created_at DESC
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "Multiple loads exist with reference {load_number}:\n{load_details}\n"
                "This indicates duplicate submissions. Please contact the shipper "
                "to clarify which load is the correct one."
            ),
            "SHIPPER": (
                "Load {load_number} was created multiple times:\n{load_details}\n"
                "This occurred because duplicate creation requests were sent. "
                "Please verify which load is correct and delete the duplicates "
                "to avoid confusion."
            ),
        },
    ),
]


# =============================================================================
# LOAD NOT TRACKING PATTERNS (from Cassie Feedback - 4 Failed Cases)
# =============================================================================
# These patterns address cases where load exists but is not tracking properly
# due to GPS/ELD/device configuration issues.
#
# Failed Cases from Cassie:
# 1. Case 2693837: GPS returning null timestamps
# 2. Case 2688628: GPS returning old locations
# 3. Case 2692749: Trailer assigned but only Truck GPS supported
# 4. Case 2682612: ELD not enabled at network level

LOAD_NOT_TRACKING_PATTERNS = [
    HypothesisPattern(
        id="H_GPS_NULL_TIMESTAMPS",
        category=RootCauseCategory.GPS_NULL_TIMESTAMPS,
        description="GPS provider returning null timestamps - no valid location data",
        triggers=[
            "load not tracking",
            "no location updates",
            "missing GPS",
            "null timestamps",
            "no tracking data",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking Database",
                condition="latest position has timestamp IS NULL",
                finding_template="GPS data has null timestamp - no valid location received",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load exists with tracking_source = 'GPS'",
                finding_template="Load configured for GPS tracking",
                supports_hypothesis=True,
                weight=0.70,
            ),
            EvidencePattern(
                source="SigNoz Logs",
                condition="GPS provider errors or null response",
                finding_template="GPS provider returning null/empty data: {error_pattern}",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="Tracking Database",
                condition="valid position with recent timestamp",
                finding_template="Valid GPS position found: {last_position_time}",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # Check latest position data
            """
            SELECT tracking_id, latitude, longitude, position_timestamp,
                   source, created_at
            FROM tracking_positions
            WHERE tracking_id = '{tracking_id}'
            ORDER BY created_at DESC
            LIMIT 10
            """,
            # Check for GPS provider errors in logs
            """
            -- SigNoz query for GPS null responses
            service.name = 'tracking-service' AND
            body LIKE '%{tracking_id}%' AND
            (body LIKE '%null%timestamp%' OR body LIKE '%no location%')
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The GPS provider is not returning valid location data for this load. "
                "The timestamps are null, indicating the GPS device may be:\n"
                "1. Not powered on or connected\n"
                "2. In an area with poor cellular coverage\n"
                "3. Experiencing hardware issues\n\n"
                "Please verify the GPS device is operational and connected."
            ),
            "SHIPPER": (
                "GPS tracking is not receiving valid location data. Root cause: null timestamps.\n"
                "This typically indicates a device connectivity issue with the carrier's GPS provider.\n"
                "Recommended actions:\n"
                "1. Contact the carrier to verify GPS device status\n"
                "2. Check if the carrier has a backup tracking method\n"
                "3. Consider enabling ELD tracking as backup if available"
            ),
        },
    ),

    HypothesisPattern(
        id="H_GPS_STALE_LOCATION",
        category=RootCauseCategory.GPS_STALE_LOCATION,
        description="GPS returning outdated/stale location data",
        triggers=[
            "load not tracking",
            "old location",
            "stale GPS",
            "not updating",
            "outdated position",
            "last update hours ago",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking Database",
                condition="latest position timestamp > 4 hours old",
                finding_template="Last GPS update was {hours_ago} hours ago ({last_update_time})",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load status is IN_TRANSIT but no recent updates",
                finding_template="Load is IN_TRANSIT but last update >4 hours old",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="SigNoz Logs",
                condition="GPS provider returning old data",
                finding_template="GPS provider returning stale data for device {device_id}",
                supports_hypothesis=True,
                weight=0.80,
            ),
            EvidencePattern(
                source="Tracking Database",
                condition="recent position within 1 hour",
                finding_template="Recent GPS update found ({minutes_ago} minutes ago)",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # Check position freshness
            """
            SELECT tracking_id,
                   position_timestamp,
                   EXTRACT(EPOCH FROM (NOW() - position_timestamp))/3600 as hours_since_update,
                   latitude, longitude, source
            FROM tracking_positions
            WHERE tracking_id = '{tracking_id}'
            ORDER BY position_timestamp DESC
            LIMIT 1
            """,
            # Check if device is expected to update (load is active)
            """
            SELECT tracking_id, status, mode, pickup_date, delivery_date
            FROM hadoop.fact_loads
            WHERE tracking_id = '{tracking_id}'
              AND etl_active_flag = 'Y'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "The GPS device is returning stale location data. "
                "Last update was {hours_ago} hours ago.\n\n"
                "Possible causes:\n"
                "1. GPS device lost cellular connectivity\n"
                "2. Driver stopped for extended period (rest stop, traffic)\n"
                "3. Device battery is low or device powered off\n\n"
                "Please check with the driver to verify device status."
            ),
            "SHIPPER": (
                "GPS tracking data is stale - last update was {hours_ago} hours ago.\n"
                "The load status shows as IN_TRANSIT but no recent location updates received.\n\n"
                "Recommended actions:\n"
                "1. Contact the carrier to check on the driver/shipment status\n"
                "2. Request carrier verify GPS device connectivity\n"
                "3. Check if there's an alternate tracking source available"
            ),
        },
    ),

    HypothesisPattern(
        id="H_DEVICE_TYPE_MISMATCH",
        category=RootCauseCategory.DEVICE_TYPE_MISMATCH,
        description="Trailer assigned to load but only Truck GPS is supported",
        triggers=[
            "load not tracking",
            "trailer not tracking",
            "device type mismatch",
            "truck GPS only",
            "wrong device type",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Device Configuration",
                condition="load assigned to trailer device but carrier only has truck GPS",
                finding_template="Load assigned to TRAILER but carrier only supports TRUCK GPS",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Network Configuration",
                condition="carrier GPS configuration shows truck_only = true",
                finding_template="Carrier GPS configuration is TRUCK ONLY",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load has trailer_number but no truck assignment",
                finding_template="Load has trailer {trailer_number} but no truck assigned",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="Device Configuration",
                condition="carrier supports both truck and trailer GPS",
                finding_template="Carrier supports both truck and trailer GPS tracking",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # Check device assignment
            """
            SELECT fl.tracking_id, fl.trailer_number, fl.truck_number,
                   dc.device_type, dc.supported_types
            FROM hadoop.fact_loads fl
            LEFT JOIN device_configuration dc ON fl.carrier_id = dc.carrier_id
            WHERE fl.tracking_id = '{tracking_id}'
              AND fl.etl_active_flag = 'Y'
            """,
            # Check carrier GPS capability
            """
            SELECT carrier_permalink, gps_provider, supports_truck, supports_trailer
            FROM carrier_tracking_config
            WHERE carrier_permalink = '{carrier_permalink}'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "This load is assigned to a trailer but your company's GPS configuration "
                "only supports truck-mounted GPS devices.\n\n"
                "Options to resolve:\n"
                "1. Assign a truck to this load for GPS tracking\n"
                "2. Contact FourKites to enable trailer GPS if available\n"
                "3. Use ELD tracking instead (if ELD is enabled)"
            ),
            "SHIPPER": (
                "Load {load_number} is assigned to a TRAILER but the carrier ({carrier_name}) "
                "only has TRUCK GPS capability configured.\n\n"
                "Root cause: Device type mismatch - carrier cannot track trailers via GPS.\n\n"
                "Recommended actions:\n"
                "1. Request carrier assign a truck to this shipment\n"
                "2. Enable ELD tracking for this carrier relationship (if available)\n"
                "3. Contact carrier to upgrade their GPS capability"
            ),
        },
    ),

    HypothesisPattern(
        id="H_ELD_NOT_ENABLED_NETWORK",
        category=RootCauseCategory.ELD_NOT_ENABLED,
        description="ELD tracking not enabled at network relationship level",
        triggers=[
            "load not tracking",
            "ELD not enabled",
            "network configuration",
            "ELD tracking disabled",
            "no ELD data",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Network Configuration",
                condition="eld_enabled = false in company_relationships",
                finding_template="ELD tracking is NOT ENABLED in network relationship",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load tracking_source = 'ELD' but no data",
                finding_template="Load configured for ELD but no tracking data received",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="SigNoz Logs",
                condition="ELD data rejected due to network config",
                finding_template="ELD data blocked: network relationship not configured for ELD",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Network Configuration",
                condition="eld_enabled = true and eld_provider configured",
                finding_template="ELD is enabled with provider: {eld_provider}",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # Check network ELD configuration
            """
            SELECT cr.id, cr.eld_enabled, cr.eld_provider, cr.status,
                   c1.name as shipper_name, c2.name as carrier_name
            FROM hadoop.company_relationships cr
            JOIN hadoop.companies c1 ON cr.company_id = c1.id
            JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
            WHERE ((c1.permalink = '{shipper_permalink}' AND c2.permalink = '{carrier_permalink}')
                OR (c1.permalink = '{carrier_permalink}' AND c2.permalink = '{shipper_permalink}'))
              AND cr.etl_active_flag = 'Y'
            """,
            # Check carrier's ELD capability
            """
            SELECT carrier_permalink, eld_provider, eld_enabled, last_eld_sync
            FROM carrier_eld_config
            WHERE carrier_permalink = '{carrier_permalink}'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "ELD tracking is not enabled in your network relationship with {shipper_name}.\n\n"
                "To enable ELD tracking:\n"
                "1. Contact {shipper_name} to enable ELD in FourKites Connect\n"
                "2. Ensure your ELD provider is integrated with FourKites\n"
                "3. Verify your ELD configuration in your driver management system"
            ),
            "SHIPPER": (
                "ELD tracking is NOT ENABLED for carrier {carrier_name} in your network.\n\n"
                "Root cause: Network relationship configuration missing ELD enablement.\n\n"
                "To enable ELD tracking:\n"
                "1. Go to FourKites Connect > Carriers > {carrier_name}\n"
                "2. Enable 'ELD Tracking' in the carrier relationship settings\n"
                "3. Select the carrier's ELD provider\n"
                "4. Save changes - tracking should resume automatically"
            ),
        },
    ),

    HypothesisPattern(
        id="H_GPS_PROVIDER_ISSUE",
        category=RootCauseCategory.GPS_PROVIDER_ISSUE,
        description="GPS provider integration issue - data not flowing to FourKites",
        triggers=[
            "load not tracking",
            "GPS integration",
            "provider issue",
            "no GPS feed",
            "integration down",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="SigNoz Logs",
                condition="GPS provider API errors or timeouts",
                finding_template="GPS provider ({provider}) returning errors: {error_type}",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Tracking Database",
                condition="no positions for carrier in last 24 hours",
                finding_template="No GPS data from carrier {carrier_name} in 24 hours",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="Integration Health",
                condition="GPS provider status = degraded or down",
                finding_template="GPS provider {provider} status: {status}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Tracking Database",
                condition="other loads from same carrier tracking normally",
                finding_template="Other loads from {carrier_name} tracking normally",
                supports_hypothesis=False,
                weight=0.90,
            ),
        ],
        validation_queries=[
            # Check GPS provider health in logs
            """
            -- SigNoz query for GPS provider errors
            service.name IN ('tracking-service', 'gps-integration-service') AND
            severity_text = 'ERROR' AND
            body LIKE '%{gps_provider}%'
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            # Check if other loads from carrier are tracking
            """
            SELECT COUNT(*) as tracking_loads,
                   MAX(position_timestamp) as last_position
            FROM tracking_positions tp
            JOIN hadoop.fact_loads fl ON tp.tracking_id = fl.tracking_id
            WHERE fl.carrier_permalink = '{carrier_permalink}'
              AND fl.status = 'in_transit'
              AND fl.etl_active_flag = 'Y'
              AND tp.position_timestamp > NOW() - INTERVAL '4 hours'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "There appears to be an issue with the GPS provider integration.\n"
                "Provider: {gps_provider}\n\n"
                "This is typically a temporary issue. Please:\n"
                "1. Verify your GPS devices are online and connected\n"
                "2. Check with your GPS provider for any service alerts\n"
                "3. Contact FourKites support if the issue persists >4 hours"
            ),
            "SHIPPER": (
                "The carrier's GPS provider ({gps_provider}) is experiencing integration issues.\n"
                "Last successful data: {last_position_time}\n\n"
                "This is typically a temporary issue on the provider side.\n"
                "FourKites is monitoring the integration. If critical:\n"
                "1. Contact the carrier for a manual status update\n"
                "2. Open a support ticket referencing provider issue"
            ),
        },
    ),

    HypothesisPattern(
        id="H_DEVICE_NOT_ASSIGNED",
        category=RootCauseCategory.DEVICE_NOT_ASSIGNED,
        description="No tracking device assigned to the load",
        triggers=[
            "load not tracking",
            "no device",
            "device not assigned",
            "no GPS device",
            "missing device",
        ],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking API",
                condition="load exists but device_id is null",
                finding_template="No tracking device assigned to load {load_number}",
                supports_hypothesis=True,
                weight=0.95,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="load tracking_source is null or empty",
                finding_template="No tracking source configured for this load",
                supports_hypothesis=True,
                weight=0.90,
            ),
            EvidencePattern(
                source="Tracking Database",
                condition="no position records exist for this tracking_id",
                finding_template="No position history found for tracking ID",
                supports_hypothesis=True,
                weight=0.85,
            ),
            EvidencePattern(
                source="Tracking API",
                condition="device_id is assigned and valid",
                finding_template="Device {device_id} assigned to load",
                supports_hypothesis=False,
                weight=0.95,
            ),
        ],
        validation_queries=[
            # Check device assignment
            """
            SELECT fl.tracking_id, fl.load_number, fl.device_id,
                   fl.tracking_source, fl.carrier_name
            FROM hadoop.fact_loads fl
            WHERE fl.tracking_id = '{tracking_id}'
              AND fl.etl_active_flag = 'Y'
            """,
            # Check if any positions exist
            """
            SELECT COUNT(*) as position_count,
                   MIN(position_timestamp) as first_position,
                   MAX(position_timestamp) as last_position
            FROM tracking_positions
            WHERE tracking_id = '{tracking_id}'
            """,
        ],
        resolution_templates={
            "CARRIER": (
                "No tracking device is assigned to load {load_number}.\n\n"
                "To enable tracking, please:\n"
                "1. Assign a GPS device or truck to this load\n"
                "2. Ensure the driver's ELD device is configured\n"
                "3. Verify the load assignment in your TMS/tracking system"
            ),
            "SHIPPER": (
                "Load {load_number} does not have a tracking device assigned.\n"
                "Carrier: {carrier_name}\n\n"
                "Root cause: The carrier has not assigned a GPS device or "
                "ELD to this shipment.\n\n"
                "Recommended actions:\n"
                "1. Contact the carrier to assign tracking equipment\n"
                "2. Verify the tracking method expected for this lane\n"
                "3. Check if manual updates are available as a backup"
            ),
        },
    ),
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_patterns_for_category(category: RootCauseCategory) -> List[HypothesisPattern]:
    """Get all hypothesis patterns for a given category"""
    all_patterns = (
        LOAD_NOT_FOUND_PATTERNS +
        NETWORK_RELATIONSHIP_PATTERNS +
        SCAC_VALIDATION_PATTERNS +
        OCEAN_TRACKING_PATTERNS +
        DUPLICATE_LOAD_PATTERNS +
        LOAD_NOT_TRACKING_PATTERNS
    )
    return [p for p in all_patterns if p.category == category]


def get_all_patterns() -> List[HypothesisPattern]:
    """Get all available hypothesis patterns"""
    return (
        LOAD_NOT_FOUND_PATTERNS +
        NETWORK_RELATIONSHIP_PATTERNS +
        SCAC_VALIDATION_PATTERNS +
        OCEAN_TRACKING_PATTERNS +
        DUPLICATE_LOAD_PATTERNS +
        LOAD_NOT_TRACKING_PATTERNS
    )


def get_pattern_by_id(pattern_id: str) -> Optional[HypothesisPattern]:
    """Get a specific hypothesis pattern by ID"""
    for pattern in get_all_patterns():
        if pattern.id == pattern_id:
            return pattern
    return None


def match_triggers_to_patterns(issue_text: str) -> List[HypothesisPattern]:
    """
    Find hypothesis patterns whose triggers match the issue description.
    Returns patterns sorted by relevance (number of matching triggers).
    """
    issue_lower = issue_text.lower()
    matches = []

    for pattern in get_all_patterns():
        trigger_count = sum(1 for t in pattern.triggers if t in issue_lower)
        if trigger_count > 0:
            matches.append((pattern, trigger_count))

    # Sort by number of matching triggers (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches]


# =============================================================================
# VALIDATION QUERY TEMPLATES (From Cassie's Knowledge Base)
# =============================================================================

VALIDATION_QUERIES = {
    "company_by_name": """
        SELECT permalink, name, company_type, status
        FROM hadoop.companies
        WHERE name ILIKE '%{company_name}%'
          AND etl_active_flag = 'Y'
        ORDER BY CASE status WHEN 'approved' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END
        LIMIT 10
    """,

    "company_by_permalink": """
        SELECT id, permalink, name, company_type, status
        FROM hadoop.companies
        WHERE permalink = '{permalink}'
          AND etl_active_flag = 'Y'
    """,

    "network_relationship": """
        SELECT cr.id, cr.status, cr.active, cr.external_id,
               c1.name as company_1, c2.name as company_2
        FROM hadoop.company_relationships cr
        JOIN hadoop.companies c1 ON cr.company_id = c1.id
        JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
        WHERE ((c1.permalink = '{shipper}' AND c2.permalink = '{carrier}')
            OR (c1.permalink = '{carrier}' AND c2.permalink = '{shipper}'))
          AND cr.etl_active_flag = 'Y'
    """,

    "load_validation": """
        SELECT load_number, load_id, status, error, carrier_id,
               carrier_name, company_name, processed_at
        FROM hadoop.load_validation_data_mart
        WHERE load_number IN ({load_numbers})
          AND processed_at >= CURRENT_DATE - INTERVAL '60 days'
        ORDER BY processed_at DESC
    """,

    "scac_validation": """
        SELECT cs.scac, cs.created_at, cr.id as relationship_id,
               cr.status, cr.active
        FROM hadoop.company_scacs cs
        JOIN hadoop.company_relationships cr ON cs.relationship_id = cr.id
        JOIN hadoop.companies c1 ON cr.company_id = c1.id
        JOIN hadoop.companies c2 ON cr.target_company_id = c2.id
        WHERE UPPER(cs.scac) = UPPER('{scac}')
          AND ((cr.company_type = 'shipper' AND c1.permalink = '{shipper}')
            OR (cr.target_company_type = 'shipper' AND c2.permalink = '{shipper}'))
          AND cs.etl_active_flag = 'Y'
    """,

    "user_by_email": """
        SELECT email_address, first_name, last_name, role,
               active, company_id as company_permalink, last_login
        FROM hadoop.users
        WHERE email_address ILIKE '%{email}%'
          AND etl_active_flag = 'Y'
        ORDER BY last_login DESC NULLS LAST
    """,
}


# =============================================================================
# RESPONSE TEMPLATES (From Cassie's Prompts)
# =============================================================================

RESPONSE_TEMPLATES = {
    "load_found_active": (
        "Load {load_number} is active in our system. "
        "Current status: {status}. "
        "If you're unable to see it, please check if you have any filters applied in your dashboard."
    ),

    "load_found_deleted": (
        "Load {load_number} was in our system but is no longer active (deleted on {deleted_at}). "
        "To reactivate this load, please contact the shipper ({shipper_name}) to recreate it."
    ),

    "load_not_found": (
        "No record found for load {load_number} in the last 60 days. "
        "Please verify the load number is correct and check with your integration "
        "to confirm the load was sent to FourKites."
    ),

    "validation_failure": (
        "Load {load_number} creation failed with error: {error_message}. "
        "Please correct the issue and resubmit the load."
    ),

    "network_missing": (
        "No network relationship found between {shipper_name} and {carrier_name}. "
        "Please configure the network relationship in FourKites Connect."
    ),

    "scac_not_configured": (
        "SCAC '{scac}' is not configured in the network relationship. "
        "Please add this SCAC in FourKites Connect."
    ),

    "manual_intervention": (
        "**Manual Intervention Required**: {reason}\n"
        "**Manual Intervention Flag: TRUE**"
    ),
}

"""Redshift client for load metadata lookup."""

import psycopg2
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from core.utils.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedshiftClient:
    """Client for querying Redshift DWH for load metadata."""

    def __init__(self):
        """Initialize Redshift connection."""
        self.connection = None
        self.is_available = False
        self._connect()

    def _connect(self):
        """Establish connection to Redshift."""
        try:
            self.connection = psycopg2.connect(
                host=config.REDSHIFT_HOST,
                port=config.REDSHIFT_PORT,
                database=config.REDSHIFT_DATABASE,
                user=config.REDSHIFT_USER,
                password=config.REDSHIFT_PASSWORD,
                connect_timeout=10,
                options='-c statement_timeout=300000'  # 5 minute query timeout
            )
            # Enable autocommit to prevent transaction errors from cascading
            self.connection.autocommit = True
            self.is_available = True
            print("✅ Connected to Redshift DWH (autocommit enabled, 4min query timeout)")
        except Exception as e:
            print(f"⚠️  Failed to connect to Redshift: {e}")
            print("⚠️  Redshift queries will be skipped. Connect to VPN to enable Redshift.")
            self.connection = None
            self.is_available = False
            # Don't raise - allow app to continue without Redshift
    
    def _ensure_connection(self):
        """Ensure connection is open, reconnect if needed."""
        try:
            # Test if connection is alive
            if self.connection is None or self.connection.closed:
                print("🔄 Redshift connection closed, reconnecting...")
                self._connect()
            else:
                # Test with a simple query
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
        except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError) as e:
            print(f"🔄 Redshift connection lost ({e}), reconnecting...")
            self._connect()

    def get_load_by_identifiers(
        self,
        tracking_ids: List[str] = None,
        load_numbers: List[str] = None,
        pro_numbers: List[str] = None,
        shipper_id = None,  # Can be str or List[str]
        shipper_name: str = None,
        carrier_name: str = None  # Not used for filtering, kept for compatibility
    ) -> Optional[Dict]:
        """
        Look up load metadata from fact_loads table.

        Search criteria (in order of reliability):
        1. tracking_id (load_id) - exact match
        2. load_number - LIKE match
        3. pro_number - LIKE match
        4. shipper_id - IN or LIKE match (MUST be pre-validated permalink!)

        Note: carrier_name is NOT used for filtering as it can cause false negatives.

        Args:
            tracking_ids: List of tracking IDs (load_id in Redshift)
            load_numbers: List of load numbers
            pro_numbers: List of PRO numbers
            shipper_id: Pre-validated shipper permalink(s) - str or List[str]
                       Single: "church-and-dwight"
                       Multiple: ["church-and-dwight", "church-dwight"]
            shipper_name: Shipper company name (for display only, NOT used for filtering)
            carrier_name: Carrier company name (NOT used for filtering)

        Returns:
            Dictionary with load metadata or None if not found
        """
        if not any([tracking_ids, load_numbers, pro_numbers]):
            print("⚠️  No identifiers provided to query")
            return None

        print(f"\n🔍 Querying Redshift fact_loads with:")
        if tracking_ids:
            print(f"   ✅ Tracking IDs: {tracking_ids}")
        if load_numbers:
            print(f"   ✅ Load Numbers: {load_numbers}")
        if pro_numbers:
            print(f"   ✅ PRO Numbers: {pro_numbers}")
        if shipper_id:
            if isinstance(shipper_id, list):
                print(f"   ✅ Shipper IDs (validated): {shipper_id} ({len(shipper_id)} permalinks)")
            else:
                print(f"   ✅ Shipper ID (validated): {shipper_id}")
        if shipper_name:
            print(f"   ℹ️  Shipper Name: {shipper_name} (informational only)")
        if carrier_name:
            print(f"   ℹ️  Carrier Name: {carrier_name} (informational only, NOT used for filtering)")

        # Build WHERE clause
        conditions = []
        params = []

        # Tracking ID - exact match
        if tracking_ids:
            try:
                tracking_id_ints = [int(tid) for tid in tracking_ids if tid.isdigit()]
                if tracking_id_ints:
                    placeholders = ','.join(['%s'] * len(tracking_id_ints))
                    conditions.append(f"load_id IN ({placeholders})")
                    params.extend(tracking_id_ints)
            except ValueError:
                pass

        # Load Number - use LIKE for partial matching
        if load_numbers:
            load_conditions = []
            for ln in load_numbers:
                load_conditions.append("(load_number LIKE %s OR display_load_number LIKE %s)")
                params.append(f"%{ln}%")
                params.append(f"%{ln}%")
            conditions.append("(" + " OR ".join(load_conditions) + ")")

        # PRO Number - use LIKE for partial matching
        if pro_numbers:
            pro_conditions = []
            for pn in pro_numbers:
                pro_conditions.append("pro_number LIKE %s")
                params.append(f"%{pn}%")
            conditions.append("(" + " OR ".join(pro_conditions) + ")")

        if not conditions:
            print("⚠️  No valid identifiers to query")
            return None

        where_clause = " OR ".join(conditions)

        # Add shipper filter ONLY if pre-validated permalink(s) provided
        # (Carrier is NOT used for filtering to avoid false negatives)
        if shipper_id:
            # Use the pre-validated permalink(s) from validate_company_permalink()
            if isinstance(shipper_id, list):
                # Multiple permalinks - use IN clause
                placeholders = ','.join(['%s'] * len(shipper_id))
                where_clause = f"({where_clause}) AND shipper_id IN ({placeholders})"
                params.extend(shipper_id)
                print(f"   🔍 Filtering by shipper_id IN ({', '.join(shipper_id)}) (pre-validated)")
            else:
                # Single permalink - use LIKE
                where_clause = f"({where_clause}) AND shipper_id LIKE %s"
                params.append(f"%{shipper_id}%")
                print(f"   🔍 Filtering by shipper_id LIKE '%{shipper_id}%' (pre-validated)")

        # Query fact_loads
        query = f"""
        SELECT
            load_id,
            load_number,
            display_load_number,
            pro_number,
            shipper_id,
            carrier_id,
            managing_carrier_id,
            status,
            created_at,
            terminated_at,
            delivered_at,
            first_ping_time,
            latest_check_call_time,
            load_mode,
            modes,
            relay_load,
            reference_numbers,
            tags
        FROM platform_shared_db.platform.fact_loads
        WHERE ({where_clause})
          AND is_deleted = false
        ORDER BY created_at DESC
        LIMIT 1
        """

        try:
            # Ensure connection is open
            self._ensure_connection()
            
            # Log the query for debugging
            logger.info("=" * 80)
            logger.info("REDSHIFT QUERY - fact_loads lookup")
            logger.info("=" * 80)
            logger.info(f"SQL:\n{query}")
            logger.info(f"Parameters: {params}")
            logger.info("=" * 80)

            # Print SQL for debugging
            print(f"\n{'='*80}")
            print(f"REDSHIFT SQL - fact_loads:")
            print(f"{'='*80}")
            print(query)
            print(f"\nParameters: {params}")
            print(f"{'='*80}\n")

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()

            if not result:
                logger.info("RESULT: No load found")
                logger.info("=" * 80)
                print(f"⚠️  No load found in Redshift for identifiers")
                return None

            # Parse result into dictionary
            # IMPORTANT: Make all datetime fields timezone-aware (UTC)
            # Redshift returns timezone-naive datetimes by default
            from datetime import timezone as dt_timezone

            def make_tz_aware(dt):
                """Make datetime timezone-aware (UTC) if it's naive."""
                if dt and dt.tzinfo is None:
                    return dt.replace(tzinfo=dt_timezone.utc)
                return dt

            metadata = {
                'tracking_id': result[0],
                'load_number': result[1],
                'display_load_number': result[2],
                'pro_number': result[3],
                'shipper_id': result[4],
                'carrier_id': result[5],
                'managing_carrier_id': result[6],
                'status': result[7],
                'created_at': make_tz_aware(result[8]),
                'terminated_at': make_tz_aware(result[9]),
                'delivered_at': make_tz_aware(result[10]),
                'first_ping_time': make_tz_aware(result[11]),
                'latest_check_call_time': make_tz_aware(result[12]),
                'load_mode': result[13],
                'modes': result[14],
                'relay_load': result[15],
                'reference_numbers': result[16],
                'tags': result[17]
            }

            logger.info(f"RESULT: Found load {metadata['tracking_id']}")
            logger.info(f"  Load Number: {metadata['load_number']}")
            logger.info(f"  Shipper: {metadata['shipper_id']}")
            logger.info(f"  Carrier: {metadata['carrier_id']}")
            logger.info(f"  Status: {metadata['status']}")
            logger.info(f"  Created: {metadata['created_at']}")
            if metadata['terminated_at']:
                logger.info(f"  Terminated: {metadata['terminated_at']}")
            logger.info("=" * 80)

            print(f"✅ Found load in Redshift:")
            print(f"   Tracking ID: {metadata['tracking_id']}")
            print(f"   Load Number: {metadata['load_number']}")
            print(f"   Shipper: {metadata['shipper_id']}")
            print(f"   Carrier: {metadata['carrier_id']}")
            print(f"   Status: {metadata['status']}")
            print(f"   Created: {metadata['created_at']}")
            if metadata['terminated_at']:
                print(f"   Terminated: {metadata['terminated_at']}")

            return metadata

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.error(f"REDSHIFT CONNECTION ERROR: {e}")
            logger.info("Attempting to reconnect and retry...")
            try:
                self._connect()
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                cursor.close()
                if result:
                    # Reprocess result (same logic as above)
                    from datetime import timezone as dt_timezone
                    def make_tz_aware(dt):
                        if dt and dt.tzinfo is None:
                            return dt.replace(tzinfo=dt_timezone.utc)
                        return dt
                    metadata = {
                        'tracking_id': result[0],
                        'load_number': result[1],
                        'display_load_number': result[2],
                        'pro_number': result[3],
                        'shipper_id': result[4],
                        'carrier_id': result[5],
                        'managing_carrier_id': result[6],
                        'status': result[7],
                        'created_at': make_tz_aware(result[8]),
                        'terminated_at': make_tz_aware(result[9]),
                        'delivered_at': make_tz_aware(result[10]),
                        'first_ping_time': make_tz_aware(result[11]),
                        'latest_check_call_time': make_tz_aware(result[12]),
                        'load_mode': result[13],
                        'modes': result[14],
                        'relay_load': result[15],
                        'reference_numbers': result[16],
                        'tags': result[17]
                    }
                    logger.info("✅ Retry successful")
                    return metadata
            except Exception as retry_error:
                logger.error(f"REDSHIFT RETRY FAILED: {retry_error}")
            logger.info("=" * 80)
            print(f"❌ Error querying Redshift: {e}")
            return None
        except Exception as e:
            logger.error(f"REDSHIFT ERROR: {e}")
            logger.info("=" * 80)
            print(f"❌ Error querying Redshift: {e}")
            return None

    def get_stop_times(self, tracking_id: int) -> List[Dict]:
        """
        Get stop arrival/departure times from fact_stops.

        Args:
            tracking_id: Load ID (tracking ID)

        Returns:
            List of stop dictionaries with timing info
        """
        query = """
        SELECT
            stop_id,
            stop_type,
            stop_name,
            sequence,
            appointment_time,
            arrival_time,
            departure_time,
            status,
            on_time,
            delayed,
            delay
        FROM platform_shared_db.platform.fact_stops
        WHERE load_id = %s
        """

        try:
            # Ensure connection is open
            self._ensure_connection()
            
            # Log the query for debugging
            logger.info("=" * 80)
            logger.info("REDSHIFT QUERY - fact_stops lookup")
            logger.info("=" * 80)
            logger.info(f"SQL:\n{query}")
            logger.info(f"Parameters: [{tracking_id}]")
            logger.info("=" * 80)

            cursor = self.connection.cursor()
            cursor.execute(query, (tracking_id,))
            results = cursor.fetchall()
            cursor.close()

            stops = []
            for row in results:
                stops.append({
                    'stop_id': row[0],
                    'stop_type': row[1],
                    'stop_name': row[2],
                    'sequence': row[3],
                    'appointment_time': row[4],
                    'arrival_time': row[5],
                    'departure_time': row[6],
                    'status': row[7],
                    'on_time': row[8],
                    'delayed': row[9],
                    'delay': row[10]
                })

            if stops:
                logger.info(f"RESULT: Found {len(stops)} stops")
                for stop in stops:
                    logger.info(f"  Stop {stop['sequence']}: {stop['stop_type']} - {stop['stop_name']}")
                print(f"✅ Found {len(stops)} stops for tracking_id {tracking_id}")
            else:
                logger.info("RESULT: No stops found")

            logger.info("=" * 80)
            return stops

        except Exception as e:
            logger.error(f"REDSHIFT ERROR: {e}")
            logger.info("=" * 80)
            print(f"❌ Error querying stops: {e}")
            return []

    def get_load_validation_errors(
        self,
        load_number: Optional[str] = None,
        tracking_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get load validation errors for RCA analysis.

        Returns ALL validation attempts (success + failures) with summary stats.

        **Key Business Rule:** If load_id IS NULL, tracking_id was never generated
        because load creation FAILED.

        **Important:** This table does NOT have bol_number or pro_number columns.
        Only load_number and load_id (tracking_id) are available.

        Args:
            load_number: Customer load number
            tracking_id: FourKites tracking ID (load_id in table - may be NULL for failures)

        Returns:
            {
                "validation_attempts": [...],  # All attempts
                "total_attempts": int,
                "failed_attempts": int,
                "latest_error": str or None,
                "latest_file": str or None,
                "latest_status": str or None
            }
        """
        if not any([load_number, tracking_id]):
            print("⚠️  No identifiers provided for validation check")
            return {
                "error": "At least one identifier (load_number or tracking_id) required",
                "validation_attempts": [],
                "total_attempts": 0,
                "failed_attempts": 0,
                "latest_error": None,
                "failure_breakdown": {}
            }

        print(f"\n🔍 Querying hadoop.load_validation_data_mart with:")
        if tracking_id:
            print(f"   ✅ Tracking ID (load_id): {tracking_id}")
        if load_number:
            print(f"   ✅ Load Number: {load_number}")

        conditions = []
        params = []

        # Build WHERE clause - only load_number and load_id supported
        if load_number:
            conditions.append("load_number LIKE %s")
            params.append(f"%{load_number}%")

        if tracking_id:
            try:
                tracking_id_int = int(tracking_id) if str(tracking_id).isdigit() else None
                if tracking_id_int:
                    conditions.append("load_id = %s")
                    params.append(tracking_id_int)
            except ValueError:
                pass

        if not conditions:
            return {
                "error": "No valid identifiers to query",
                "validation_attempts": [],
                "total_attempts": 0,
                "failed_attempts": 0,
                "latest_error": None,
                "failure_breakdown": {}
            }

        where_clause = " OR ".join(conditions)

        # Query with actual table schema (no bol_number, pro_number, origin_state, dest_state)
        query = f"""
        SELECT
            load_id,
            company_id,
            company_name,
            load_number,
            status,
            error,
            processed_at,
            carrier_id,
            carrier_name,
            file_name,
            stop_count,
            origin_stop_name,
            origin_city,
            origin_country,
            pickup_appointment_time,
            dest_stop_name,
            dest_city,
            dest_country,
            dest_appointment_time,
            modes,
            shipper_name
        FROM hadoop.load_validation_data_mart
        WHERE {where_clause}
        ORDER BY processed_at DESC
        LIMIT 50
        """

        try:
            # Ensure connection is open
            self._ensure_connection()

            # Log the query for debugging
            logger.info("=" * 80)
            logger.info("REDSHIFT QUERY - load_validation_data_mart (RCA)")
            logger.info("=" * 80)
            logger.info(f"SQL:\n{query}")
            logger.info(f"Parameters: {params}")
            logger.info("=" * 80)

            # Print SQL for debugging
            print(f"\n{'='*80}")
            print(f"REDSHIFT SQL - load_validation_data_mart (RCA):")
            print(f"{'='*80}")
            print(query)
            print(f"\nParameters: {params}")
            print(f"{'='*80}\n")

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            if not results:
                logger.info("RESULT: No validation records found")
                logger.info("=" * 80)
                print("ℹ️  No validation records found in load_validation_data_mart")
                return {
                    "validation_attempts": [],
                    "total_attempts": 0,
                    "failed_attempts": 0,
                    "latest_error": None,
                    "latest_file": None,
                    "latest_status": None,
                    "failure_breakdown": {}
                }

            # Parse results into structured dictionaries
            validation_attempts = []
            for row in results:
                # Make datetime timezone-aware
                from datetime import timezone as dt_timezone

                processed_at = row[6]
                if processed_at and processed_at.tzinfo is None:
                    processed_at = processed_at.replace(tzinfo=dt_timezone.utc)

                pickup_appointment = row[14]
                if pickup_appointment and pickup_appointment.tzinfo is None:
                    pickup_appointment = pickup_appointment.replace(tzinfo=dt_timezone.utc)

                dest_appointment = row[18]
                if dest_appointment and dest_appointment.tzinfo is None:
                    dest_appointment = dest_appointment.replace(tzinfo=dt_timezone.utc)

                attempt = {
                    'load_id': row[0],  # tracking_id (NULL if creation failed!)
                    'company_id': row[1],
                    'company_name': row[2],
                    'load_number': row[3],
                    'status': row[4],
                    'error': row[5],
                    'processed_at': processed_at,
                    'carrier_id': row[7],
                    'carrier_name': row[8],
                    'file_name': row[9],
                    'stop_count': row[10],
                    'origin_stop_name': row[11],
                    'origin_city': row[12],
                    'origin_country': row[13],
                    'pickup_appointment_time': pickup_appointment,
                    'dest_stop_name': row[15],
                    'dest_city': row[16],
                    'dest_country': row[17],
                    'dest_appointment_time': dest_appointment,
                    'modes': row[19],
                    'shipper_name': row[20]
                }
                validation_attempts.append(attempt)

            logger.info(f"RESULT: Found {len(validation_attempts)} validation attempt(s)")

            # Analyze failed vs successful attempts
            # Based on production data analysis:
            # - Status can be: Create Failure, Update Failure, Delete Failure, Failure,
            #   Skipping load creation, Skipping load updation, Skipped, Reference Failure
            # - Even "Created" status can have errors! (1835 cases in 2-day sample)
            # - Success statuses: "Created", "Skipped" (WITHOUT errors)
            #
            # Failed if:
            # 1. Status contains "Failure" keyword
            # 2. Status is "Skipping load creation/updation" (validation blocked it)
            # 3. error IS NOT NULL (even if status is "Created")
            # 4. load_id IS NULL (tracking_id never generated)

            def is_failed_attempt(attempt):
                """Determine if validation attempt failed"""
                status = attempt.get('status', '')
                error = attempt.get('error', '')
                load_id = attempt.get('load_id')

                # Check for failure status keywords
                failure_keywords = ['Failure', 'Skipping']
                if any(keyword in status for keyword in failure_keywords):
                    return True

                # Check for errors (even if status is "Created")
                if error and error.strip():
                    return True

                # Check if tracking_id was never generated
                if load_id is None:
                    return True

                return False

            failed_attempts = [a for a in validation_attempts if is_failed_attempt(a)]

            logger.info(f"  Total Attempts: {len(validation_attempts)}")
            logger.info(f"  Failed Attempts: {len(failed_attempts)}")
            logger.info(f"  Successful Attempts: {len(validation_attempts) - len(failed_attempts)}")

            # Get latest attempt info
            latest_attempt = validation_attempts[0] if validation_attempts else None
            latest_error = latest_attempt['error'] if latest_attempt and latest_attempt.get('error') else None
            latest_file = latest_attempt['file_name'] if latest_attempt else None
            latest_status = latest_attempt['status'] if latest_attempt else None

            # Categorize failures by type (for RCA analysis)
            failure_breakdown = {
                'create_failures': 0,
                'update_failures': 0,
                'delete_failures': 0,
                'reference_failures': 0,
                'skipped': 0,
                'other_failures': 0
            }

            for attempt in failed_attempts:
                status = attempt.get('status', '')
                if 'Create Failure' in status or 'Skipping load creation' in status:
                    failure_breakdown['create_failures'] += 1
                elif 'Update Failure' in status or 'Skipping load updation' in status:
                    failure_breakdown['update_failures'] += 1
                elif 'Delete Failure' in status:
                    failure_breakdown['delete_failures'] += 1
                elif 'Reference Failure' in status:
                    failure_breakdown['reference_failures'] += 1
                elif 'Skipped' in status:
                    failure_breakdown['skipped'] += 1
                else:
                    failure_breakdown['other_failures'] += 1

            # Print summary with failure breakdown
            if failed_attempts:
                logger.info(f"  Most recent error: {latest_error[:100]}..." if latest_error else "  Most recent: Failed (no error message)")
                logger.info(f"  Failure Breakdown:")
                logger.info(f"    Create Failures: {failure_breakdown['create_failures']}")
                logger.info(f"    Update Failures: {failure_breakdown['update_failures']}")
                logger.info(f"    Delete Failures: {failure_breakdown['delete_failures']}")
                logger.info(f"    Reference Failures: {failure_breakdown['reference_failures']}")
                logger.info(f"    Skipped: {failure_breakdown['skipped']}")
                logger.info(f"    Other: {failure_breakdown['other_failures']}")

                print(f"\n⚠️  Found {len(failed_attempts)} FAILED validation attempt(s) out of {len(validation_attempts)} total:")
                print(f"\n   📊 Failure Breakdown:")
                if failure_breakdown['create_failures'] > 0:
                    print(f"      Create Failures: {failure_breakdown['create_failures']}")
                if failure_breakdown['update_failures'] > 0:
                    print(f"      Update Failures: {failure_breakdown['update_failures']}")
                if failure_breakdown['delete_failures'] > 0:
                    print(f"      Delete Failures: {failure_breakdown['delete_failures']}")
                if failure_breakdown['reference_failures'] > 0:
                    print(f"      Reference Failures: {failure_breakdown['reference_failures']}")
                if failure_breakdown['skipped'] > 0:
                    print(f"      Skipped: {failure_breakdown['skipped']}")
                if failure_breakdown['other_failures'] > 0:
                    print(f"      Other: {failure_breakdown['other_failures']}")

                print(f"\n   🔍 Sample Failed Attempts:")
                for i, attempt in enumerate(failed_attempts[:3], 1):  # Show first 3
                    print(f"\n   {i}. Load Number: {attempt['load_number']}")
                    if attempt['load_id']:
                        print(f"      Tracking ID: {attempt['load_id']}")
                    else:
                        print(f"      Tracking ID: NULL (tracking_id never generated!)")
                    print(f"      Status: {attempt['status']}")
                    if attempt['error']:
                        # Handle array format errors like ['error message']
                        error_display = attempt['error']
                        if error_display.startswith('[') and error_display.endswith(']'):
                            print(f"      Error: {error_display}")
                        else:
                            print(f"      Error: {error_display[:200]}...")
                    print(f"      Processed: {attempt['processed_at']}")
                    if attempt['file_name']:
                        print(f"      File: {attempt['file_name']}")

                if len(failed_attempts) > 3:
                    print(f"\n   ... and {len(failed_attempts) - 3} more failed attempt(s)")
            else:
                logger.info("  ✅ All attempts successful")
                print(f"✅ All {len(validation_attempts)} validation attempt(s) succeeded")

            # Show date range
            if validation_attempts:
                dates = [a['processed_at'] for a in validation_attempts if a['processed_at']]
                if dates:
                    earliest = min(dates)
                    latest_date = max(dates)
                    logger.info(f"  Date range: {earliest} to {latest_date}")
                    print(f"\n📅 Validation activity: {earliest.strftime('%Y-%m-%d %H:%M')} to {latest_date.strftime('%Y-%m-%d %H:%M')}")

            logger.info("=" * 80)

            return {
                "validation_attempts": validation_attempts,
                "total_attempts": len(validation_attempts),
                "failed_attempts": len(failed_attempts),
                "latest_error": latest_error,
                "latest_file": latest_file,
                "latest_status": latest_status,
                "failure_breakdown": failure_breakdown  # NEW: Categorized failures
            }

        except Exception as e:
            logger.error(f"REDSHIFT ERROR: {e}")
            logger.info("=" * 80)
            print(f"❌ Error querying load validation: {e}")
            return {
                "error": str(e),
                "validation_attempts": [],
                "total_attempts": 0,
                "failed_attempts": 0,
                "latest_error": None,
                "failure_breakdown": {}
            }

    def validate_company_permalink(self, company_name: str, guessed_permalink: str) -> Optional[List[str]]:
        """
        Validate and get the correct company permalink(s) from Redshift.

        This is CRITICAL because our permalink normalization is a best-guess.
        The actual permalink in the database might be different (e.g., "& " → "and").

        Args:
            company_name: Original company name (e.g., "Church & Dwight")
            guessed_permalink: Our normalized guess (e.g., "church-dwight")

        Returns:
            List of correct permalinks if found (may be 1 or more), None if not found

        Example:
            Input: "Church & Dwight", "church-dwight"
            Query finds: name="church and dwight", permalink="church-and-dwight"
            Returns: ["church-and-dwight"]
        """
        if not company_name and not guessed_permalink:
            return None

        print(f"\n🔍 Validating company permalink in Redshift...")
        print(f"   Company name: {company_name}")
        print(f"   Guessed permalink: {guessed_permalink}")

        # Extract key words from company name for matching
        # e.g., "Church & Dwight" → ["church", "dwight"]
        import re
        words = re.findall(r'\w+', company_name.lower()) if company_name else []
        # Use most significant words (skip common words)
        significant_words = [w for w in words if len(w) > 2 and w not in ['inc', 'llc', 'ltd', 'corp', 'company']]

        if not significant_words:
            return None

        # Build conditions: BOTH name and permalink must match ALL words
        name_conditions = []
        permalink_conditions = []
        params = []

        for word in significant_words:
            name_conditions.append("lower(name) LIKE %s")
            params.append(f"%{word}%")

            permalink_conditions.append("permalink LIKE %s")
            params.append(f"%{word}%")

        # Combine conditions with AND (more precise matching)
        where_clause = f"({' AND '.join(name_conditions)}) AND ({' AND '.join(permalink_conditions)})"

        query = f"""
        SELECT name, permalink
        FROM platform_shared_db.pgs_company.companies
        WHERE {where_clause}
          AND status = 'approved'
          AND active = true
          AND is_test_company = false
        LIMIT 5
        """

        try:
            # Ensure connection is open
            self._ensure_connection()
            
            logger.info("=" * 80)
            logger.info("REDSHIFT QUERY - Company permalink validation")
            logger.info("=" * 80)
            logger.info(f"SQL:\n{query}")
            logger.info(f"Parameters: {params}")
            logger.info("=" * 80)

            print(f"\n{'='*80}")
            print(f"REDSHIFT SQL - Company Validation:")
            print(f"{'='*80}")
            print(query)
            print(f"\nParameters: {params}")
            print(f"{'='*80}\n")

            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            if not results:
                logger.info("RESULT: No matching company found")
                logger.info("=" * 80)
                print(f"⚠️  No matching company found in Redshift")
                print(f"   This means the shipper_id filter will be SKIPPED to avoid false negatives\n")
                return None

            # Show all matches
            logger.info(f"RESULT: Found {len(results)} potential matches:")
            print(f"✅ Found {len(results)} potential company match(es):")

            permalinks = []
            for i, row in enumerate(results, 1):
                db_name = row[0]
                db_permalink = row[1]
                permalinks.append(db_permalink)
                logger.info(f"  Match {i}: name='{db_name}', permalink='{db_permalink}'")
                print(f"   {i}. Name: {db_name}")
                print(f"      Permalink: {db_permalink}")

            # Return ALL matching permalinks (will be used in IN clause)
            if len(permalinks) == 1:
                logger.info(f"Using single validated permalink: {permalinks[0]}")
                print(f"\n✅ Using validated permalink: {permalinks[0]}\n")
            else:
                logger.info(f"Using {len(permalinks)} validated permalinks: {permalinks}")
                print(f"\n✅ Using {len(permalinks)} validated permalinks:")
                for p in permalinks:
                    print(f"   - {p}")
                print()

            logger.info("=" * 80)
            return permalinks

        except Exception as e:
            logger.error(f"REDSHIFT ERROR: {e}")
            logger.info("=" * 80)
            print(f"❌ Error validating company permalink: {e}")
            return None

    def get_load_states(self, tracking_ids: List[str]) -> List[Dict]:
        """
        Get load states for multiple tracking IDs for cross-referencing with errors.

        This is used to explain errors by comparing error timestamps with load states:
        - Was the load terminated before the update attempt?
        - Was the load already delivered?
        - What was the status when the error occurred?

        Args:
            tracking_ids: List of tracking IDs (load_id in Redshift)

        Returns:
            List of dictionaries with load state information:
            - tracking_id, load_number, shipper_id, carrier_id
            - status, created_at, terminated_at, delivered_at
            - first_ping_time, latest_check_call_time
        """
        if not tracking_ids:
            print("⚠️  No tracking IDs provided to get_load_states")
            return []

        # Convert to integers
        try:
            tracking_id_ints = [int(tid) for tid in tracking_ids if str(tid).isdigit()]
            if not tracking_id_ints:
                print("⚠️  No valid tracking IDs to query")
                return []
        except ValueError:
            print("⚠️  Invalid tracking IDs format")
            return []

        print(f"\n🔍 Querying load states for {len(tracking_id_ints)} tracking IDs...")

        # Build query with IN clause
        placeholders = ','.join(['%s'] * len(tracking_id_ints))
        query = f"""
        SELECT
            load_id,
            load_number,
            shipper_id,
            carrier_id,
            status,
            created_at,
            terminated_at,
            delivered_at,
            first_ping_time,
            latest_check_call_time
        FROM platform_shared_db.platform.fact_loads
        WHERE load_id IN ({placeholders})
          AND is_deleted = false
        ORDER BY created_at DESC
        """

        try:
            # Ensure connection is open
            self._ensure_connection()
            
            # Log the query for debugging
            logger.info("=" * 80)
            logger.info("REDSHIFT QUERY - get_load_states")
            logger.info("=" * 80)
            logger.info(f"SQL:\n{query}")
            logger.info(f"Parameters: {tracking_id_ints}")
            logger.info("=" * 80)

            # Print SQL for debugging
            print(f"\n{'='*80}")
            print(f"REDSHIFT SQL - get_load_states:")
            print(f"{'='*80}")
            print(query)
            print(f"\nParameters: {tracking_id_ints}")
            print(f"{'='*80}\n")

            cursor = self.connection.cursor()
            cursor.execute(query, tracking_id_ints)
            results = cursor.fetchall()
            cursor.close()

            if not results:
                logger.info("RESULT: No loads found")
                logger.info("=" * 80)
                print(f"⚠️  No loads found for provided tracking IDs")
                return []

            # Parse results into dictionaries with timezone-aware datetimes
            from datetime import timezone as dt_timezone

            def make_tz_aware(dt):
                """Make datetime timezone-aware (UTC) if it's naive."""
                if dt and dt.tzinfo is None:
                    return dt.replace(tzinfo=dt_timezone.utc)
                return dt

            load_states = []
            for row in results:
                state = {
                    'tracking_id': row[0],
                    'load_number': row[1],
                    'shipper_id': row[2],
                    'carrier_id': row[3],
                    'status': row[4],
                    'created_at': make_tz_aware(row[5]),
                    'terminated_at': make_tz_aware(row[6]),
                    'delivered_at': make_tz_aware(row[7]),
                    'first_ping_time': make_tz_aware(row[8]),
                    'latest_check_call_time': make_tz_aware(row[9])
                }
                load_states.append(state)

            logger.info(f"RESULT: Found {len(load_states)} load states")
            print(f"✅ Found states for {len(load_states)} loads:")

            # Print summary
            for state in load_states:
                print(f"\n   Load {state['tracking_id']} ({state['load_number']}):")
                print(f"      Status: {state['status']}")
                print(f"      Created: {state['created_at']}")
                if state['terminated_at']:
                    print(f"      Terminated: {state['terminated_at']}")
                if state['delivered_at']:
                    print(f"      Delivered: {state['delivered_at']}")

            logger.info("=" * 80)
            return load_states

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.error(f"REDSHIFT CONNECTION ERROR: {e}")
            logger.info("Attempting to reconnect and retry...")
            try:
                self._connect()
                cursor = self.connection.cursor()
                cursor.execute(query, tracking_id_ints)
                results = cursor.fetchall()
                cursor.close()
                
                if results:
                    # Reprocess results
                    from datetime import timezone as dt_timezone
                    def make_tz_aware(dt):
                        if dt and dt.tzinfo is None:
                            return dt.replace(tzinfo=dt_timezone.utc)
                        return dt
                    
                    load_states = []
                    for row in results:
                        state = {
                            'tracking_id': row[0],
                            'load_number': row[1],
                            'shipper_id': row[2],
                            'carrier_id': row[3],
                            'status': row[4],
                            'created_at': make_tz_aware(row[5]),
                            'terminated_at': make_tz_aware(row[6]),
                            'delivered_at': make_tz_aware(row[7]),
                            'first_ping_time': make_tz_aware(row[8]),
                            'latest_check_call_time': make_tz_aware(row[9])
                        }
                        load_states.append(state)
                    logger.info("✅ Retry successful")
                    return load_states
            except Exception as retry_error:
                logger.error(f"REDSHIFT RETRY FAILED: {retry_error}")
            logger.info("=" * 80)
            print(f"❌ Error getting load states: {e}")
            return []
        except Exception as e:
            logger.error(f"REDSHIFT ERROR: {e}")
            logger.info("=" * 80)
            print(f"❌ Error getting load states: {e}")
            return []

    def execute(self, query: str, params: Dict = None, verbose: bool = True, query_name: str = None) -> List[Dict]:
        """
        Execute a generic SQL query and return results as list of dicts.

        Args:
            query: SQL query string (can use %(param)s placeholders)
            params: Dictionary of parameters for the query
            verbose: Whether to print the query for debugging
            query_name: Optional name/description of the query for debugging

        Returns:
            List of dictionaries with column names as keys
        """
        # Check if Redshift is available
        if not self.is_available:
            if verbose:
                print(f"⚠️  Skipping Redshift query: {query_name or 'Unnamed query'} (not connected)")
            return []

        self._ensure_connection()

        if verbose:
            print("\n" + "=" * 80)
            if query_name:
                print(f"📊 REDSHIFT QUERY: {query_name}")
            else:
                print("📊 REDSHIFT QUERY:")
            print("-" * 80)

            # Display query with parameters substituted for easy copy-paste
            display_query = query
            if params:
                # Create a copy to display with substituted values
                from datetime import datetime, date
                for key, value in params.items():
                    placeholder = f"%({key})s"
                    # Format value based on type
                    if isinstance(value, str):
                        formatted_value = f"'{value}'"
                    elif value is None:
                        formatted_value = "NULL"
                    elif isinstance(value, (datetime, date)):
                        formatted_value = f"'{value}'"
                    else:
                        formatted_value = str(value)
                    display_query = display_query.replace(placeholder, formatted_value)

            print(display_query)
            print("=" * 80 + "\n")

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or {})

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows and convert to list of dicts
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]

            if verbose:
                if query_name:
                    print(f"✅ {query_name}: Returned {len(results)} rows\n")
                else:
                    print(f"✅ Query returned {len(results)} rows\n")

            cursor.close()
            return results

        except Exception as e:
            # Note: With autocommit=True, no rollback needed (each query is isolated)
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

            if query_name:
                print(f"❌ QUERY FAILED ({query_name}): {e}\n")
            else:
                print(f"❌ Query failed: {e}\n")

            # Log the full query for debugging
            if verbose and params:
                print(f"   Parameters: {params}\n")

            raise

    def find_similar_stuck_loads(self, carrier_id: str, limit: int = 20) -> Dict[str, Any]:
        """Find similar loads stuck in same state for the same carrier."""
        if not self.is_available:
            return {"affected_loads": 0}

        query = """
        SELECT COUNT(DISTINCT load_id) as affected_loads
        FROM load_states
        WHERE carrier_id = %(carrier_id)s
          AND current_state IN ('Awaiting Tracking Info', 'awaiting_tracking_info')
          AND updated_at >= CURRENT_DATE - INTERVAL '7 days'
        """

        try:
            results = self.execute(query, {"carrier_id": carrier_id}, verbose=False, query_name="find_similar_stuck_loads")
            if results and len(results) > 0:
                return {"affected_loads": results[0].get("affected_loads", 0)}
            return {"affected_loads": 0}
        except Exception as e:
            logger.error(f"Error finding similar loads: {e}")
            return {"affected_loads": 0}

    def query_network_relationships(self, shipper_id: str, carrier_id: str) -> Dict[str, Any]:
        """Query network relationships from Redshift."""
        if not self.is_available:
            return {"exists": False}

        query = """
        SELECT relationship_id, status, active, allow_tracking, created_at, updated_at
        FROM network_relationships
        WHERE shipper_id = %(shipper_id)s
          AND carrier_id = %(carrier_id)s
        LIMIT 1
        """

        try:
            results = self.execute(query, {"shipper_id": shipper_id, "carrier_id": carrier_id}, verbose=False, query_name="query_network_relationships")
            if results and len(results) > 0:
                rel = results[0]
                return {
                    "exists": True,
                    "status": rel.get("status"),
                    "active": rel.get("active"),
                    "allow_tracking": rel.get("allow_tracking"),
                }
            return {"exists": False}
        except Exception as e:
            logger.error(f"Error querying network relationships: {e}")
            return {"exists": False}

    def close(self):
        """Close Redshift connection."""
        if self.connection:
            self.connection.close()
            print("🔌 Closed Redshift connection")

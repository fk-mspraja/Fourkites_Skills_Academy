"""ClickHouse client for querying logs and integration data."""

import logging
import threading
from typing import Dict, List, Optional, Any
from clickhouse_driver import Client

from core.utils.config import config

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """Client for querying logs from SigNoz ClickHouse with thread-safe connection management."""

    def __init__(self):
        """Initialize SigNoz ClickHouse client with connection parameters."""
        self.host = config.SIGNOZ_CLICKHOUSE_HOST
        self.port = config.SIGNOZ_CLICKHOUSE_PORT
        self.user = config.SIGNOZ_CLICKHOUSE_USER
        self.password = config.SIGNOZ_CLICKHOUSE_PASSWORD
        self.database = 'signoz_logs'
        self.settings = {'max_execution_time': 300}  # 5 minute timeout

        # Thread-local storage for connections
        # Each thread gets its own connection to avoid "Simultaneous queries" error
        self._thread_local = threading.local()

        # Validate configuration
        if not self.host or self.host == 'localhost':
            logger.warning("SigNoz ClickHouse host not configured or set to localhost")
            raise ValueError("SigNoz ClickHouse host not properly configured")

    def _get_connection(self):
        """Get or create a ClickHouse connection for the current thread."""
        if not hasattr(self._thread_local, 'client') or self._thread_local.client is None:
            self._thread_local.client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                settings=self.settings
            )
        return self._thread_local.client

    def execute(
        self,
        query: str,
        params: Optional[dict] = None,
        *,
        query_name: Optional[str] = None,
        verbose: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute raw SQL against SigNoz ClickHouse with optional logging.

        Args:
            query: SQL query to execute
            params: Optional query parameters
            query_name: Optional name for logging
            verbose: If True, log the query

        Returns:
            List of dictionaries with query results
        """
        params = params or {}

        if verbose:
            logger.info("=" * 80)
            if query_name:
                logger.info("SIGNOZ CLICKHOUSE QUERY: %s", query_name)
            else:
                logger.info("SIGNOZ CLICKHOUSE QUERY")
            logger.info("=" * 80)
            # Use %s formatting to avoid issues with % characters in SQL LIKE clauses
            logger.info("%s", query)
            logger.info("=" * 80)

        try:
            # Get thread-local connection to avoid "Simultaneous queries" error
            client = self._get_connection()

            # Only pass params if they're not empty
            # ClickHouse driver uses Python % formatting which conflicts with SQL LIKE '%...'
            # Add query timeout settings (120 seconds max for large result sets)
            exec_settings = {'max_execution_time': 120}

            if params:
                rows, column_meta = client.execute(query, params, with_column_types=True, settings=exec_settings)
            else:
                rows, column_meta = client.execute(query, with_column_types=True, settings=exec_settings)
        except Exception as exc:
            logger.error("SigNoz ClickHouse query failed: %s", exc)
            raise

        # Convert rows to list of dicts
        column_names = [col[0] for col in column_meta]
        return [dict(zip(column_names, row)) for row in rows]

    def build_log_search_query(
        self,
        service_names: List[str],
        start_date: str,
        end_date: str,
        search_string: Optional[str] = None,
        tracking_id: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        limit: int = 200
    ) -> tuple:
        """
        Build the SQL query and parameters for log search.
        Returns (query, params, query_display) so caller can send to UI before execution.
        """
        from datetime import datetime, timedelta

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        now = datetime.now()
        retention_limit = now - timedelta(days=30)

        # Track if dates were adjusted
        date_adjusted = False

        # Adjust dates if outside 30-day retention window
        if start_dt < retention_limit:
            logger.warning("Start date %s adjusted to %s (30-day retention)", start_date, retention_limit.date())
            start_dt = retention_limit
            date_adjusted = True

        if end_dt > now:
            logger.warning("End date %s adjusted to %s (cannot search future)", end_date, now.date())
            end_dt = now
            date_adjusted = True

        start_date_adj = start_dt.strftime("%Y-%m-%d")
        end_date_adj = end_dt.strftime("%Y-%m-%d")

        # Build base params
        params = {
            'start_date': start_date_adj,
            'end_date': end_date_adj,
            'limit': limit
        }

        # Build service names clause (IN)
        if len(service_names) == 1:
            service_clause = "resource_string_service$$name = %(service_0)s"
            params['service_0'] = service_names[0]
        else:
            service_placeholders = []
            for i, service in enumerate(service_names):
                param_name = f'service_{i}'
                service_placeholders.append(f"%(service_{i})s")
                params[param_name] = service
            service_clause = f"resource_string_service$$name IN ({','.join(service_placeholders)})"

        # Build search conditions (either simple or advanced mode)
        search_conditions_str = "1=1"  # Default to no filtering

        # Simple mode: single search_string
        if search_string:
            search_conditions_str = "body LIKE %(search_string)s"
            params['search_string'] = f'%{search_string}%'

        # Advanced mode: multiple conditions with hasToken and contains
        elif conditions:
            condition_parts = []  # Store individual condition clauses with connectors

            for i, condition in enumerate(conditions):
                # Handle both dict and Pydantic objects
                if hasattr(condition, 'operator'):
                    # Pydantic object
                    operator = condition.operator
                    value = condition.value
                    connector = condition.connector if i < len(conditions) - 1 else None
                else:
                    # Dictionary
                    operator = condition.get('operator')
                    value = condition.get('value')
                    connector = condition.get('connector') if i < len(conditions) - 1 else None

                condition_clause = None

                if operator == 'hasToken':
                    # Split value into words and add hasToken for each
                    # NOTE: hasToken() doesn't support words with underscores or special chars
                    # If value contains problematic chars, fall back to LIKE only
                    words = value.split()
                    has_problematic_chars = any('_' in word or '-' in word for word in words)

                    if has_problematic_chars or len(words) == 1 and ('_' in value or '-' in value):
                        # Fall back to LIKE only for values with underscores/hyphens
                        param_name = f'like_{i}'
                        condition_clause = f"body LIKE %({param_name})s"
                        params[param_name] = f'%{value}%'
                    else:
                        # Use hasToken for normal words
                        token_clauses = []
                        for j, word in enumerate(words):
                            param_name = f'token_{i}_{j}'
                            token_clauses.append(f"hasToken(body, %({param_name})s)")
                            params[param_name] = word
                        # Add final LIKE for exact phrase
                        param_name = f'phrase_{i}'
                        token_clauses.append(f"body LIKE %({param_name})s")
                        params[param_name] = f'%{value}%'
                        # Group all token checks with AND
                        condition_clause = "(" + " AND ".join(token_clauses) + ")"
                elif operator == 'contains':
                    param_name = f'contains_{i}'
                    condition_clause = f"body LIKE %({param_name})s"
                    params[param_name] = f'%{value}%'

                if condition_clause:
                    condition_parts.append({
                        'clause': condition_clause,
                        'connector': connector
                    })

            # Build final condition string with proper OR/AND handling
            if condition_parts:
                final_sql_parts = []
                has_or = False
                for i, part in enumerate(condition_parts):
                    final_sql_parts.append(part['clause'])
                    # Add connector (AND/OR) if not last
                    if i < len(condition_parts) - 1 and part['connector']:
                        final_sql_parts.append(part['connector'])
                        if part['connector'] == 'OR':
                            has_or = True

                # If OR exists, wrap entire condition in parentheses for proper precedence
                if has_or:
                    search_conditions_str = "(" + " ".join(final_sql_parts) + ")"
                else:
                    search_conditions_str = " ".join(final_sql_parts)
            else:
                search_conditions_str = "1=1"

        # Build tracking_id filter
        tracking_id_clause = ""
        if tracking_id:
            tracking_id_clause = "AND attribute_string_tracking_id = %(tracking_id)s"
            params['tracking_id'] = tracking_id

        query = f"""
        SELECT
            toDateTime64(timestamp / 1000000000, 3) as ts,
            resource_string_service$$name as service_name,
            body
        FROM signoz_logs.distributed_logs
        WHERE toDate(timestamp / 1000000000) BETWEEN %(start_date)s AND %(end_date)s
          AND {service_clause}
          AND {search_conditions_str}
          {tracking_id_clause}
        LIMIT %(limit)s
        """

        # Create display query with parameters substituted
        query_display = query
        for param_name, param_value in params.items():
            placeholder = f"%({param_name})s"
            if isinstance(param_value, str):
                safe_value = param_value.replace("'", "\\'")
                query_display = query_display.replace(placeholder, f"'{safe_value}'")
            else:
                query_display = query_display.replace(placeholder, str(param_value))

        return query, params, query_display.strip(), date_adjusted

    def search_logs_manual(
        self,
        service_names: List[str],
        start_date: str,
        end_date: str,
        search_string: Optional[str] = None,
        tracking_id: Optional[str] = None,
        conditions: Optional[List[Dict[str, Any]]] = None,
        limit: int = 200
    ) -> Dict[str, Any]:
        """
        Manual log search for tech users.

        Searches SigNoz ClickHouse distributed_logs table for application logs.

        Args:
            service_names: List of service names (e.g., ['integrations-worker', 'ocean-worker'])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            search_string: Text to search in body column (simple mode)
            tracking_id: Optional tracking ID filter
            conditions: List of search conditions for advanced mode
            limit: Max records (default 200)

        Returns:
            {
                "logs": [{"ts": "...", "body": "..."}],
                "total": int,
                "truncated": bool,
                "searched_with_tracking_id": bool,
                "fallback_used": bool,
                "date_adjusted": bool,
                "query": str (executable SQL)
            }
        """
        # Log search parameters
        services_str = ", ".join(service_names)
        logger.info("Searching logs in services: %s from %s to %s", services_str, start_date, end_date)
        if search_string:
            logger.info("Search string: %s", search_string)
        if conditions:
            logger.info("Conditions: %s", conditions)
        if tracking_id:
            logger.info("Tracking ID filter: %s", tracking_id)

        # Build the query using the shared method
        query, params, query_display, date_adjusted = self.build_log_search_query(
            service_names=service_names,
            start_date=start_date,
            end_date=end_date,
            search_string=search_string,
            tracking_id=tracking_id,
            conditions=conditions,
            limit=limit
        )

        try:
            # Log the query being executed (use %s to avoid $ interpretation issues)
            logger.info("Executing query:\n%s", query)
            logger.info("Parameters: %s", params)
            logger.info("Executable query (copy-paste ready):\n%s", query_display)

            logger.info("⏳ Executing query against ClickHouse (max 120s timeout)...")

            # Execute query
            results = self.execute(query, params)

            logger.info("✅ Query completed successfully, processing %d results", len(results))

            # If no results and tracking_id was used, retry without it
            if len(results) == 0 and tracking_id:
                logger.info("No results with tracking_id, retrying without it...")

                # Build fallback query without tracking_id
                query_no_tid, params_no_tid, query_display_fallback, _ = self.build_log_search_query(
                    service_names=service_names,
                    start_date=start_date,
                    end_date=end_date,
                    search_string=search_string,
                    tracking_id=None,  # Remove tracking_id
                    conditions=conditions,
                    limit=limit
                )

                logger.info("Fallback query:\n%s", query_no_tid)
                logger.info("Fallback parameters: %s", params_no_tid)
                logger.info("Executable fallback query (copy-paste ready):\n%s", query_display_fallback)
                logger.info("⏳ Executing fallback query against ClickHouse (max 120s timeout)...")

                results = self.execute(query_no_tid, params_no_tid)

                logger.info("✅ Fallback query completed successfully, processing %d results", len(results))

                return {
                    "logs": results,
                    "total": len(results),
                    "truncated": len(results) == limit,
                    "searched_with_tracking_id": False,
                    "fallback_used": True,
                    "date_adjusted": date_adjusted,
                    "query": query_display_fallback
                }

            return {
                "logs": results,
                "total": len(results),
                "truncated": len(results) == limit,
                "searched_with_tracking_id": bool(tracking_id),
                "fallback_used": False,
                "date_adjusted": date_adjusted,
                "query": query_display
            }

        except Exception as e:
            logger.error(f"SigNoz log search failed: {e}", exc_info=True)
            raise

    def get_ocean_processing_logs(
        self,
        container_number: Optional[str] = None,
        booking_number: Optional[str] = None,
        days_back: int = 7,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get ocean processing logs for a container or booking number.

        Args:
            container_number: Container number to search for
            booking_number: Booking number to search for
            days_back: Number of days to look back (default 7)
            limit: Max log entries to return (default 50)

        Returns:
            {"count": int, "logs": [...], "has_errors": bool}
        """
        if not self.is_configured:
            return {"count": 0, "logs": [], "has_errors": False}

        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        search_string = container_number or booking_number
        if not search_string:
            return {"count": 0, "logs": [], "has_errors": False}

        try:
            result = self.search_logs_manual(
                service_names=["ocean-worker", "integrations-worker"],
                start_date=start_date,
                end_date=end_date,
                search_string=search_string,
                limit=limit
            )

            logs = result.get("logs", [])
            has_errors = any("error" in log.get("body", "").lower() for log in logs)

            return {
                "count": len(logs),
                "logs": logs[:10],  # Return first 10 for evidence
                "has_errors": has_errors
            }
        except Exception as e:
            logger.error(f"Error getting ocean processing logs: {e}")
            return {"count": 0, "logs": [], "has_errors": False}

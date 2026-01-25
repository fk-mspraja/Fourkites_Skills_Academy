"""ClickHouse client for querying rewind_db (fact_load_file_* tables)."""

import logging
import threading
from typing import Dict, List, Optional, Any
from clickhouse_driver import Client

from core.utils.config import config

logger = logging.getLogger(__name__)


class RewindClickHouseClient:
    """Client for querying fact_load_file_* tables from rewind_db ClickHouse."""

    def __init__(self):
        """Initialize Rewind ClickHouse client with connection parameters."""
        self.host = config.REWIND_CLICKHOUSE_HOST
        self.port = config.REWIND_CLICKHOUSE_PORT
        self.user = config.REWIND_CLICKHOUSE_USER
        self.password = config.REWIND_CLICKHOUSE_PASSWORD
        self.database = config.REWIND_CLICKHOUSE_DATABASE
        self.secure = config.REWIND_CLICKHOUSE_SECURE
        self.verify = config.REWIND_CLICKHOUSE_VERIFY
        self.settings = {'max_execution_time': 300}  # 5 minute timeout

        # Thread-local storage for connections
        # Each thread gets its own connection to avoid "Simultaneous queries" error
        self._thread_local = threading.local()

        # Validate configuration
        if not self.host or self.host == 'localhost':
            logger.warning("Rewind ClickHouse host not configured or set to localhost")
            raise ValueError("Rewind ClickHouse host not properly configured")

        logger.info(f"Rewind ClickHouse config: host={self.host}, port={self.port}, "
                   f"database={self.database}, secure={self.secure}, verify={self.verify}")

    def _get_connection(self):
        """Get or create a ClickHouse connection for the current thread."""
        if not hasattr(self._thread_local, 'client') or self._thread_local.client is None:
            connection_params = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'settings': self.settings,
                'connect_timeout': 30,  # 30 second connect timeout
                'send_receive_timeout': 300,  # 5 minute query timeout
            }

            # Add SSL/TLS parameters if secure connection is enabled
            if self.secure:
                connection_params['secure'] = True
                connection_params['verify'] = self.verify
                logger.info(f"Connecting to Rewind ClickHouse with SSL on port {self.port}: verify={self.verify}")

            logger.info(f"Creating ClickHouse client with params: host={self.host}, port={self.port}, secure={self.secure}")

            try:
                self._thread_local.client = Client(**connection_params)
                # Test the connection immediately
                self._thread_local.client.execute("SELECT 1")
                logger.info("Rewind ClickHouse connection established and verified")
            except Exception as e:
                logger.error(f"Failed to establish Rewind ClickHouse connection: {e}")
                self._thread_local.client = None
                raise

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
        Execute raw SQL against Rewind ClickHouse with optional logging.

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
                logger.info("REWIND CLICKHOUSE QUERY: %s", query_name)
            else:
                logger.info("REWIND CLICKHOUSE QUERY")
            logger.info("=" * 80)
            # Use %s formatting to avoid issues with % characters in SQL LIKE clauses
            logger.info("%s", query)
            logger.info("=" * 80)

        try:
            # Get thread-local connection to avoid "Simultaneous queries" error
            client = self._get_connection()

            if not client:
                raise Exception("Failed to get ClickHouse client connection")

            # Only pass params if they're not empty
            # ClickHouse driver uses Python % formatting which conflicts with SQL LIKE '%...'
            if params:
                rows, column_meta = client.execute(query, params, with_column_types=True)
            else:
                rows, column_meta = client.execute(query, with_column_types=True)
        except Exception as exc:
            logger.error("Rewind ClickHouse query failed: %s", exc)
            # Clear the connection on error so it will reconnect next time
            if hasattr(self._thread_local, 'client'):
                self._thread_local.client = None
            raise

        # Convert rows to list of dicts
        column_names = [col[0] for col in column_meta]
        return [dict(zip(column_names, row)) for row in rows]

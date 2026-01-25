"""AWS Athena client for querying historical logs and API calls."""

import boto3
import asyncio
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from utils.config import config

logger = logging.getLogger(__name__)

# Thread pool for running blocking boto3 calls
_executor = ThreadPoolExecutor(max_workers=10)


class AthenaClient:
    """Client for querying AWS Athena (raw_data_db)."""

    def __init__(self):
        """Initialize Athena client using boto3 with credentials from config."""
        # Build boto3 client kwargs
        client_kwargs = {'region_name': config.ATHENA_REGION}

        # Use explicit credentials from .env if provided
        if config.ATHENA_AWS_ACCESS_KEY_ID and config.ATHENA_AWS_SECRET_ACCESS_KEY:
            client_kwargs['aws_access_key_id'] = config.ATHENA_AWS_ACCESS_KEY_ID
            client_kwargs['aws_secret_access_key'] = config.ATHENA_AWS_SECRET_ACCESS_KEY

            # Add session token ONLY if provided and not a placeholder
            if (config.ATHENA_AWS_SESSION_TOKEN and
                config.ATHENA_AWS_SESSION_TOKEN not in ['your_token', '', 'None', 'none']):
                client_kwargs['aws_session_token'] = config.ATHENA_AWS_SESSION_TOKEN
                logger.info("Athena client initialized with explicit credentials + session token")
            else:
                logger.info("Athena client initialized with explicit credentials (no session token)")
        else:
            # Fall back to default boto3 credential chain
            logger.info("Athena client initialized using default AWS credential chain")

        # Validate configuration
        if not config.ATHENA_DATABASE:
            raise ValueError("ATHENA_DATABASE is required")
        if not config.ATHENA_OUTPUT_LOCATION:
            raise ValueError("ATHENA_OUTPUT_LOCATION is required")

        self.client = boto3.client('athena', **client_kwargs)
        self.database = config.ATHENA_DATABASE
        self.output_location = config.ATHENA_OUTPUT_LOCATION
        logger.info(f"Athena configured - Region: {config.ATHENA_REGION}, Database: {self.database}")

    def _execute_sync(
        self,
        query: str,
        verbose: bool = False,
        query_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Synchronous execution method (for use with run_in_executor).

        Args:
            query: SQL query to execute
            verbose: Whether to print verbose logs
            query_name: Name for logging

        Returns:
            List of result rows as dictionaries
        """
        import time

        try:
            if verbose:
                logger.info("=" * 80)
                if query_name:
                    logger.info(f"ATHENA QUERY: {query_name}")
                else:
                    logger.info("ATHENA QUERY")
                logger.info("=" * 80)
                logger.info(query)
                logger.info("=" * 80)

            # Start query execution
            response = self.client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={'OutputLocation': self.output_location}
            )

            query_execution_id = response['QueryExecutionId']

            # Wait for query to complete
            max_attempts = 60  # 60 attempts * 1 second = 60 seconds timeout
            attempt = 0

            while attempt < max_attempts:
                query_status = self.client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                status = query_status['QueryExecution']['Status']['State']

                if status == 'SUCCEEDED':
                    break
                elif status in ['FAILED', 'CANCELLED']:
                    error_msg = query_status['QueryExecution']['Status'].get(
                        'StateChangeReason', 'Unknown error'
                    )
                    logger.error(f"Athena query failed: {error_msg}")
                    return []

                time.sleep(1)  # Poll every 1 second (blocking, but in thread pool)
                attempt += 1

            if attempt >= max_attempts:
                logger.error("Athena query timeout: Query took too long (>60 seconds)")
                return []

            # Get query results
            results = []
            next_token = None
            column_names = None

            while True:
                if next_token:
                    result_response = self.client.get_query_results(
                        QueryExecutionId=query_execution_id,
                        NextToken=next_token
                    )
                else:
                    result_response = self.client.get_query_results(
                        QueryExecutionId=query_execution_id
                    )

                # Extract column names from first page
                if column_names is None and 'ResultSet' in result_response:
                    column_info = result_response['ResultSet']['ResultSetMetadata']['ColumnInfo']
                    column_names = [col['Name'] for col in column_info]

                    # Process rows (skip header row on first page)
                    rows = result_response['ResultSet']['Rows']
                    for row in rows[1:]:  # Skip header
                        values = [field.get('VarCharValue') for field in row['Data']]
                        results.append(dict(zip(column_names, values)))
                else:
                    # Subsequent pages don't have header
                    rows = result_response['ResultSet']['Rows']
                    for row in rows:
                        values = [field.get('VarCharValue') for field in row['Data']]
                        results.append(dict(zip(column_names, values)))

                # Check if more results exist
                next_token = result_response.get('NextToken')
                if not next_token:
                    break

            if verbose:
                logger.info(f"RESULT: Found {len(results)} rows")
                logger.info("=" * 80)

            return results

        except Exception as e:
            logger.error(f"Athena query error: {e}", exc_info=True)
            if verbose:
                logger.info("=" * 80)
            return []

    def execute(
        self,
        query: str,
        verbose: bool = False,
        query_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Execute a generic Athena query synchronously (blocking) and return results as list of dicts.

        For async contexts, use execute_async() instead to avoid blocking the event loop.

        Args:
            query: SQL query to execute
            verbose: Whether to print verbose logs
            query_name: Name for logging

        Returns:
            List of result rows as dictionaries
        """
        return self._execute_sync(query, verbose, query_name)

    async def execute_async(
        self,
        query: str,
        verbose: bool = False,
        query_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Execute a generic Athena query asynchronously (non-blocking) and return results as list of dicts.

        Runs the blocking boto3 calls in a thread pool to avoid blocking the event loop.

        Args:
            query: SQL query to execute
            verbose: Whether to print verbose logs
            query_name: Name for logging

        Returns:
            List of result rows as dictionaries
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self._execute_sync,
            query,
            verbose,
            query_name
        )

"""Base client with thread-local connections and retry logic"""

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, TypeVar

from utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ClientError(Exception):
    """Base exception for client errors"""
    pass


class ConnectionError(ClientError):
    """Failed to establish connection"""
    pass


class QueryError(ClientError):
    """Query execution failed"""
    pass


class TimeoutError(ClientError):
    """Operation timed out"""
    pass


class BaseClient(ABC):
    """
    Base client with thread-local connection pattern and retry logic.

    Provides:
    - Thread-local connections to prevent "simultaneous queries" errors
    - Exponential backoff retry logic
    - Connection lifecycle management
    - Async execution support
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0
    ):
        self._thread_local = threading.local()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._is_closed = False

    @property
    def name(self) -> str:
        """Client name for logging"""
        return self.__class__.__name__

    @abstractmethod
    def _create_connection(self) -> Any:
        """Create a new connection. Override in subclass."""
        pass

    def _get_connection(self) -> Any:
        """Get thread-local connection, creating if needed"""
        if self._is_closed:
            raise ClientError(f"{self.name} is closed")

        if not hasattr(self._thread_local, "conn") or self._thread_local.conn is None:
            logger.debug(f"Creating new connection for {self.name}")
            self._thread_local.conn = self._create_connection()

        return self._thread_local.conn

    def _close_connection(self) -> None:
        """Close the thread-local connection"""
        if hasattr(self._thread_local, "conn") and self._thread_local.conn is not None:
            try:
                conn = self._thread_local.conn
                if hasattr(conn, "close"):
                    conn.close()
            except Exception as e:
                logger.warning(f"Error closing {self.name} connection: {e}")
            finally:
                self._thread_local.conn = None

    def close(self) -> None:
        """Close the client"""
        self._is_closed = True
        self._close_connection()

    async def execute_with_retry(
        self,
        operation: Callable[..., T],
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation: The function to execute
            *args: Arguments to pass to the operation
            operation_name: Name for logging
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Result of the operation

        Raises:
            ClientError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                # Execute with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(operation, *args, **kwargs),
                    timeout=self.timeout
                )

                elapsed = time.time() - start_time
                logger.debug(
                    f"{self.name}.{operation_name} completed",
                    extra={"elapsed_ms": elapsed * 1000, "attempt": attempt + 1}
                )

                return result

            except asyncio.TimeoutError:
                last_error = TimeoutError(
                    f"{self.name}.{operation_name} timed out after {self.timeout}s"
                )
                logger.warning(f"{last_error} (attempt {attempt + 1}/{self.max_retries})")

            except Exception as e:
                last_error = e
                logger.warning(
                    f"{self.name}.{operation_name} failed: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)
                logger.debug(f"Retrying in {delay:.1f}s")
                await asyncio.sleep(delay)

                # Reset connection on retry
                self._close_connection()

        raise ClientError(
            f"{self.name}.{operation_name} failed after {self.max_retries} attempts: {last_error}"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

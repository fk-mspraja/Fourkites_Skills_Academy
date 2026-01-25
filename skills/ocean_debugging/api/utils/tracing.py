"""
Distributed tracing utilities for request tracking.

Provides trace_id and span_id generation for tracking requests across services.
"""

import uuid
import time
import logging
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Context variables for storing trace information
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_span_stack: ContextVar[list] = ContextVar('span_stack', default=[])


def generate_trace_id() -> str:
    """Generate a unique trace ID for the request."""
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """Generate a unique span ID."""
    return str(uuid.uuid4())[:8]  # Shorter for readability


def get_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    return _trace_id.get()


def set_trace_id(trace_id: str):
    """Set the trace ID for the current context."""
    _trace_id.set(trace_id)


def get_current_span() -> Optional[Dict[str, Any]]:
    """Get the current span from the stack."""
    stack = _span_stack.get()
    return stack[-1] if stack else None


@contextmanager
def trace_request():
    """
    Context manager for tracing an entire request.

    Creates a root span for the entire request, so all logs have a span_id.
    This makes logs fully searchable in ClickHouse/Trino by trace_id + span_id.

    Usage:
        with trace_request():
            # Your request handling code
            with trace_span("database_query"):
                # Database query code (nested span)
    """
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    # Create root span for the entire request
    root_span_id = generate_span_id()
    root_span = {
        'span_id': root_span_id,
        'span_name': 'request',
        'parent_span_id': None,
        'start_time': time.time()
    }
    _span_stack.set([root_span])  # Initialize with root span

    start_time = time.time()
    logger.info(f"🔵 TRACE START | trace_id={trace_id} | span_id={root_span_id}")

    try:
        yield trace_id
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"🔵 TRACE END | trace_id={trace_id} | span_id={root_span_id} | duration={duration_ms:.2f}ms")
        _trace_id.set(None)
        _span_stack.set([])


@contextmanager
def trace_span(span_name: str, **attributes):
    """
    Context manager for tracing a span within a request.

    Args:
        span_name: Name of the span (e.g., "fetch_load_metadata", "query_athena")
        **attributes: Additional attributes to log with the span

    Usage:
        with trace_span("fetch_load_metadata", tracking_id="123"):
            result = fetch_metadata(tracking_id)
    """
    trace_id = get_trace_id()
    if not trace_id:
        # No active trace, skip tracing
        yield
        return

    span_id = generate_span_id()
    stack = _span_stack.get()
    parent_span = stack[-1] if stack else None
    parent_span_id = parent_span['span_id'] if parent_span else None

    span = {
        'span_id': span_id,
        'span_name': span_name,
        'parent_span_id': parent_span_id,
        'start_time': time.time()
    }

    # Add span to stack (create new list for contextvars immutability)
    _span_stack.set([*stack, span])

    # Format attributes
    attr_str = " | ".join([f"{k}={v}" for k, v in attributes.items()])
    parent_info = f" | parent_span_id={parent_span_id}" if parent_span_id else ""

    logger.info(f"  ▶ SPAN START | trace_id={trace_id} | span_id={span_id} | span={span_name}{parent_info} | {attr_str}")

    try:
        yield span_id
    except Exception as e:
        duration_ms = (time.time() - span['start_time']) * 1000
        logger.error(f"  ✗ SPAN ERROR | trace_id={trace_id} | span_id={span_id} | span={span_name} | duration={duration_ms:.2f}ms | error={str(e)}")
        raise
    finally:
        duration_ms = (time.time() - span['start_time']) * 1000
        logger.info(f"  ◀ SPAN END | trace_id={trace_id} | span_id={span_id} | span={span_name} | duration={duration_ms:.2f}ms")

        # Remove span from stack (create new list for contextvars immutability)
        stack = _span_stack.get()
        if stack and stack[-1]['span_id'] == span_id:
            _span_stack.set(stack[:-1])


def log_with_trace(message: str, level: str = "info", **extra):
    """
    Log a message with trace context.

    Args:
        message: Log message
        level: Log level (info, warning, error)
        **extra: Additional fields to log
    """
    trace_id = get_trace_id()
    current_span = get_current_span()

    if trace_id:
        span_info = f" | span_id={current_span['span_id']} | span={current_span['span_name']}" if current_span else ""
        extra_str = " | ".join([f"{k}={v}" for k, v in extra.items()])
        full_message = f"trace_id={trace_id}{span_info} | {message}"
        if extra_str:
            full_message += f" | {extra_str}"

        log_func = getattr(logger, level, logger.info)
        log_func(full_message)
    else:
        # No trace context, log normally
        log_func = getattr(logger, level, logger.info)
        log_func(message)


def log_span_start(span_name: str, **attributes):
    """
    Log span start without context manager (for simpler integration).

    Args:
        span_name: Name of the span
        **attributes: Additional attributes

    Returns:
        Tuple of (trace_id, span_id, start_time) for manual span end logging
    """
    trace_id = get_trace_id()
    if not trace_id:
        return None, None, None

    span_id = generate_span_id()
    start_time = time.time()

    attr_str = " | ".join([f"{k}={v}" for k, v in attributes.items()])
    logger.info(f"  ▶ SPAN START | trace_id={trace_id} | span_id={span_id} | span={span_name} | {attr_str}")

    return trace_id, span_id, start_time


def log_span_end(span_name: str, trace_id: str, span_id: str, start_time: float, **attributes):
    """
    Log span end.

    Args:
        span_name: Name of the span
        trace_id: Trace ID
        span_id: Span ID
        start_time: Start time from log_span_start
        **attributes: Additional attributes
    """
    if not trace_id or not span_id or not start_time:
        return

    duration_ms = (time.time() - start_time) * 1000
    attr_str = " | ".join([f"{k}={v}" for k, v in attributes.items()])
    log_msg = f"  ◀ SPAN END | trace_id={trace_id} | span_id={span_id} | span={span_name} | duration={duration_ms:.2f}ms"
    if attr_str:
        log_msg += f" | {attr_str}"
    logger.info(log_msg)

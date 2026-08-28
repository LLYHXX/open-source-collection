"""
Custom structlog processors for context injection.

Following internal structured logging conventions with
OpenTelemetry log-trace correlation best practices.

References:
    - OTel Logs Data Model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
"""

import logging
import os
import threading
from typing import Any, Dict, Optional

from opentelemetry import trace

# Cache service name to avoid repeated env lookups
_cached_service_name: Optional[str] = None


def _get_service_name() -> str:
    """Get cached service name for log entries."""
    global _cached_service_name
    if _cached_service_name is None:
        _cached_service_name = os.getenv("OTEL_SERVICE_NAME", "futureagi-backend")
    return _cached_service_name


def add_pid_and_tid(logger, method_name: str, event_dict: dict) -> dict:
    """
    Add process ID and thread ID to log entries.

    Useful for debugging multi-process and multi-threaded issues
    (e.g., Celery workers, gunicorn).
    """
    event_dict["pid"] = os.getpid()
    event_dict["tid"] = threading.get_ident()
    return event_dict


_cached_region: Optional[str] = None


def add_region_context(logger, method_name: str, event_dict: dict) -> dict:
    """Add deployment region to log entries for multi-region filtering."""
    global _cached_region
    if _cached_region is None:
        _cached_region = os.getenv("REGION", "us")
    event_dict["region"] = _cached_region
    return event_dict


def add_otel_context(logger, method_name: str, event_dict: dict) -> dict:
    """
    Inject OpenTelemetry trace context into log entries for log-trace correlation.

    This enables correlation between logs and distributed traces in observability
    tools supporting OpenTelemetry trace context.

    Adds the following fields (compatible with most backends):
        - trace_id: 32-character hex string (W3C format)
        - span_id: 16-character hex string
        - trace_flags: Trace flags (01 = sampled)
        - service.name: Service name for filtering
        - otel.trace_id: Duplicate for backends expecting this format
        - otel.span_id: Duplicate for backends expecting this format

    The LoggingInstrumentor also injects otelTraceID/otelSpanID into stdlib
    log records - this processor reads those for stdlib logs routed through structlog.
    """
    try:
        span = trace.get_current_span()
        span_context = span.get_span_context() if span else None

        if span_context and span_context.is_valid:
            # W3C trace context format (32-char hex trace ID, 16-char hex span ID)
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            trace_flags = format(span_context.trace_flags, "02x")

            # Standard field names (used by most backends)
            event_dict["trace_id"] = trace_id
            event_dict["span_id"] = span_id
            event_dict["trace_flags"] = trace_flags

            # OpenTelemetry-prefixed fields (alternate casing for backend compatibility)
            event_dict["traceID"] = trace_id
            event_dict["spanID"] = span_id

            # Service context (critical for multi-service correlation)
            event_dict["service.name"] = _get_service_name()

            # Check if trace is sampled (useful for debugging sampling issues)
            is_sampled = span_context.trace_flags & trace.TraceFlags.SAMPLED
            event_dict["trace_sampled"] = bool(is_sampled)

    except Exception:
        pass  # Don't break logging if OTEL fails

    return event_dict


def add_otel_context_from_record(logger, method_name: str, event_dict: dict) -> dict:
    """
    Extract OpenTelemetry context from stdlib LogRecord attributes.

    The OpenTelemetry LoggingInstrumentor injects trace context into LogRecords
    as otelTraceID, otelSpanID, otelServiceName. This processor reads those
    for stdlib logs that go through structlog's ProcessorFormatter.

    Use this in foreign_pre_chain for stdlib logger integration.
    """
    try:
        # Get the LogRecord if available (from stdlib logging integration)
        record: Optional[logging.LogRecord] = event_dict.get("_record")

        if record:
            # Read OTel-injected attributes from LogRecord
            otel_trace_id = getattr(record, "otelTraceID", None)
            otel_span_id = getattr(record, "otelSpanID", None)
            otel_service = getattr(record, "otelServiceName", None)

            # Only add if not already present (avoid overwriting)
            if otel_trace_id and otel_trace_id != "0" and "trace_id" not in event_dict:
                event_dict["trace_id"] = otel_trace_id
                event_dict["traceID"] = otel_trace_id

            if otel_span_id and otel_span_id != "0" and "span_id" not in event_dict:
                event_dict["span_id"] = otel_span_id
                event_dict["spanID"] = otel_span_id

            if otel_service and "service.name" not in event_dict:
                event_dict["service.name"] = otel_service

    except Exception:
        pass  # Don't break logging if extraction fails

    # Always call the main otel context function to get current span context
    # This handles structlog loggers that don't have a LogRecord
    return add_otel_context(logger, method_name, event_dict)

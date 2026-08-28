"""Temporal OpenTelemetry integration."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

__all__ = [
    "init_otel_for_temporal",
    "reset_tracing_interceptor",
    "get_temporal_tracing_interceptor",
    "get_interceptors_for_client",
    "get_interceptors_for_worker",
    "connect_with_tracing",
]

# Singleton interceptor instance
_tracing_interceptor = None


def init_otel_for_temporal(queue_name: str = "worker") -> object | None:
    """
    Initialize OpenTelemetry for a Temporal worker.

    This should be called FIRST before any other imports to ensure
    all activities, DB queries, Redis, and HTTP calls are traced.

    Args:
        queue_name: Task queue name for component identification

    Returns:
        TracerProvider if initialized, None if disabled or failed
    """
    try:
        from tfc.telemetry import init_telemetry, instrument_for_temporal

        provider = init_telemetry(component=f"temporal-{queue_name}")
        if provider:
            instrument_for_temporal()
            logger.info("temporal_worker_otel_initialized", task_queue=queue_name)
            return provider
        else:
            logger.info("temporal_worker_otel_disabled", task_queue=queue_name)
            return None
    except ImportError as e:
        logger.warning("temporal_worker_otel_import_error", error=str(e))
        return None
    except Exception as e:
        logger.warning("temporal_worker_otel_init_failed", error=str(e))
        return None


def reset_tracing_interceptor() -> None:
    """
    Reset the cached TracingInterceptor.

    Call this after init_telemetry() to ensure the interceptor
    uses the newly configured tracer provider.

    This is automatically called by init_telemetry().
    """
    global _tracing_interceptor
    _tracing_interceptor = None
    logger.debug("temporal_tracing_interceptor_reset")


def get_temporal_tracing_interceptor():
    """
    Get or create the Temporal TracingInterceptor.

    The interceptor should be passed to Client.connect() to enable
    automatic tracing of all client calls, workflows, and activities.

    IMPORTANT: Call init_telemetry() BEFORE calling this function to ensure
    the TracingInterceptor uses the properly configured tracer provider.

    Usage:
        from tfc.telemetry import init_telemetry
        from tfc.telemetry.temporal import get_temporal_tracing_interceptor
        from temporalio.client import Client

        # Initialize OTel FIRST
        init_telemetry(component="temporal-worker")

        # Then get interceptor
        interceptor = get_temporal_tracing_interceptor()
        client = await Client.connect(
            "localhost:7233",
            interceptors=[interceptor] if interceptor else [],
        )

    Returns:
        TracingInterceptor instance or None if not available
    """
    global _tracing_interceptor

    if _tracing_interceptor is not None:
        return _tracing_interceptor

    try:
        from opentelemetry import trace
        from temporalio.contrib.opentelemetry import TracingInterceptor

        # Get the current tracer provider (should be configured by init_telemetry)
        tracer_provider = trace.get_tracer_provider()
        provider_name = type(tracer_provider).__name__

        # Check if OTel is properly initialized
        if provider_name == "ProxyTracerProvider":
            # ProxyTracerProvider means no SDK is configured yet
            logger.warning(
                "temporal_tracing_no_provider",
                provider=provider_name,
                hint="Call init_telemetry() before get_temporal_tracing_interceptor()",
            )

        # Create interceptor - let it use the global tracer provider
        # TracingInterceptor will create its own tracer with proper instrumentation scope
        _tracing_interceptor = TracingInterceptor()

        logger.info(
            "temporal_tracing_interceptor_created",
            tracer_provider=provider_name,
            interceptor_type=type(_tracing_interceptor).__name__,
        )
        return _tracing_interceptor

    except ImportError as e:
        logger.warning(
            "temporal_otel_unavailable",
            error=str(e),
            hint="Install temporalio[opentelemetry] extra",
        )
        return None
    except Exception as e:
        logger.error("temporal_interceptor_failed", error=str(e), exc_info=True)
        return None


def get_interceptors_for_client() -> list:
    """
    Get list of interceptors to pass to Temporal Client.connect().

    This returns a list that includes the TracingInterceptor if available,
    or an empty list if not.

    Usage:
        from tfc.telemetry.temporal import get_interceptors_for_client
        from temporalio.client import Client

        client = await Client.connect(
            "localhost:7233",
            interceptors=get_interceptors_for_client(),
        )

    Returns:
        List of interceptors
    """
    interceptor = get_temporal_tracing_interceptor()
    return [interceptor] if interceptor else []


def get_interceptors_for_worker() -> list:
    """
    Get list of interceptors to pass to Temporal Worker.

    The TracingInterceptor from Client.connect() will automatically apply
    to workers using that client. However, if you want to apply interceptors
    only to workers (not client calls), use this function.

    Note: Per Temporal docs, it's recommended to set interceptors on the
    client rather than the worker, so the interceptor applies to all calls.

    Returns:
        List of interceptors (currently same as client interceptors)
    """
    return get_interceptors_for_client()


async def connect_with_tracing(
    host: str,
    namespace: str = "default",
    **kwargs,
):
    """
    Connect to Temporal with tracing enabled.

    Convenience function that creates a Temporal client with
    OpenTelemetry tracing interceptor automatically configured.

    Args:
        host: Temporal server host (e.g., "localhost:7233")
        namespace: Temporal namespace
        **kwargs: Additional arguments to pass to Client.connect()

    Returns:
        Connected Temporal Client with tracing enabled
    """
    from temporalio.client import Client

    # Merge interceptors
    interceptors = kwargs.pop("interceptors", [])
    tracing_interceptor = get_temporal_tracing_interceptor()
    if tracing_interceptor:
        interceptors = [tracing_interceptor] + list(interceptors)

    return await Client.connect(
        host,
        namespace=namespace,
        interceptors=interceptors,
        **kwargs,
    )

"""
FutureAGI OpenTelemetry Integration

A production-grade OpenTelemetry setup for distributed tracing across:
- Django HTTP/gRPC requests
- Celery background tasks
- Temporal workflows and activities
- LLM inference calls

Usage:
    # In manage.py, celery.py, or temporal worker startup:
    from tfc.telemetry import init_telemetry
    init_telemetry(service_name="django")  # or "celery", "temporal-worker"

    # Manual span creation for LLM calls:
    from tfc.telemetry import create_llm_span, get_tracer

    tracer = get_tracer(__name__)
    with create_llm_span(tracer, "gpt-4-inference", model="gpt-4", provider="openai") as span:
        response = call_llm()
        span.set_attribute("output.value", response[:100])
        span.set_attribute("llm.token_count.total", 150)

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4317)
    OTEL_EXPORTER_OTLP_PROTOCOL: Protocol (grpc or http/protobuf, default: grpc)
    OTEL_SERVICE_NAME: Override service name
    OTEL_ENABLED: Set to "false" to disable tracing (default: true)
    OTEL_TRACES_SAMPLER: Sampler type (default: parentbased_traceidratio)
    OTEL_TRACES_SAMPLER_ARG: Sampler arg, e.g., 0.1 for 10% (default: 1.0)
    OTEL_LOGS_ENABLED: Set to "true" to enable OTLP log export (default: false)

References:
    - OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
    - Django instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/django/django.html
    - Celery instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/celery/celery.html
    - Temporal tracing: https://python.temporal.io/temporalio.contrib.opentelemetry.html
    - structlog integration: https://www.structlog.org/en/stable/frameworks.html
"""

from .config import (
    OTEL_ENABLED,
    get_otlp_endpoint,
    get_service_name,
    get_tracer,
    get_tracer_provider,
    init_telemetry,
    verify_telemetry,
)
from .context import sync_to_async_with_context  # Alias for otel_sync_to_async
from .context import (  # Thread context propagation (use otel_sync_to_async for new code)
    attach_otel_context,
    detach_otel_context,
    extract_trace_context_from_headers,
    get_current_otel_context,
    get_current_trace_context,
    log_trace_context,
    otel_sync_to_async,
    run_sync_with_context,
    set_attribute,
    set_attributes,
    set_business_context,
    set_error_context,
    set_request_context,
    set_user_context,
    wrap_for_async,
    wrap_for_thread,
)
from .enrichment import (
    add_span_context,
    add_span_event,
    capture_args,
    capture_args_async,
    capture_db_query,
    capture_http_request,
)
from .instrumentation import (  # Core framework instrumentation; HTTP clients; Databases; LLM providers (via traceAI - https://github.com/future-agi/traceAI); Agent frameworks (via traceAI); All LLM instrumentation; Cloud services; Vector databases; ClickHouse custom instrumentation; Django Channels/WebSocket custom instrumentation; MinIO custom instrumentation; Messaging; Async and threading; Other
    instrument_aiohttp,
    instrument_all_llm_providers,
    instrument_all_vector_dbs,
    instrument_anthropic,
    instrument_asyncio,
    instrument_bedrock,
    instrument_botocore,
    instrument_celery,
    instrument_chromadb,
    instrument_clickhouse_client,
    instrument_crewai,
    instrument_django,
    instrument_for_celery,
    instrument_for_django,
    instrument_for_temporal,
    instrument_google_genai,
    instrument_groq,
    instrument_grpc,
    instrument_httpx,
    instrument_jinja2,
    instrument_litellm,
    instrument_logging,
    instrument_mcp,
    instrument_milvus,
    instrument_minio_client,
    instrument_mistralai,
    instrument_openai,
    instrument_pika,
    instrument_pinecone,
    instrument_psycopg,
    instrument_qdrant,
    instrument_redis,
    instrument_requests,
    instrument_threading,
    instrument_urllib3,
    instrument_vertexai,
    instrument_weaviate,
    trace_channel_layer_send,
    trace_clickhouse_query,
    trace_clickhouse_query_async,
    trace_minio_operation,
    trace_websocket_consumer,
)
from .llm_spans import create_llm_span, set_llm_attributes
from .logs import (
    OTEL_LOGS_ENABLED,
    get_logger_provider,
    get_logs_endpoint,
    init_otel_logging,
)
from .naming import (
    django_request_hook,
    django_response_hook,
    get_activity_span_name,
    get_db_span_name,
    get_http_client_span_name,
    get_workflow_span_name,
    sanitize_span_name,
)
from .temporal import (
    get_interceptors_for_client,
    get_temporal_tracing_interceptor,
    init_otel_for_temporal,
)

__all__ = [
    # Core configuration
    "init_telemetry",
    "get_tracer",
    "get_tracer_provider",
    "get_service_name",
    "get_otlp_endpoint",
    "OTEL_ENABLED",
    "verify_telemetry",
    # Context helpers
    "set_user_context",
    "set_request_context",
    "set_business_context",
    "set_error_context",
    "set_attribute",
    "set_attributes",
    # Debug helpers
    "get_current_trace_context",
    "log_trace_context",
    "extract_trace_context_from_headers",
    # Thread context propagation (for sync_to_async)
    "otel_sync_to_async",
    "sync_to_async_with_context",  # Alias for otel_sync_to_async
    "run_sync_with_context",
    "wrap_for_async",
    "wrap_for_thread",
    "wrap_for_async",
    "get_current_otel_context",
    "attach_otel_context",
    "detach_otel_context",
    # Instrumentation - core frameworks
    "instrument_django",
    "instrument_celery",
    # Instrumentation - HTTP clients
    "instrument_requests",
    "instrument_httpx",
    "instrument_urllib3",
    "instrument_aiohttp",
    # Instrumentation - databases
    "instrument_psycopg",
    "instrument_redis",
    # Instrumentation - LLM providers (via traceAI)
    "instrument_openai",
    "instrument_anthropic",
    "instrument_bedrock",
    "instrument_google_genai",
    "instrument_vertexai",
    "instrument_groq",
    "instrument_mistralai",
    "instrument_litellm",
    # Instrumentation - Agent frameworks (via traceAI)
    "instrument_crewai",
    "instrument_mcp",
    "instrument_all_llm_providers",
    # Instrumentation - cloud services
    "instrument_botocore",
    # Instrumentation - vector databases
    "instrument_chromadb",
    "instrument_qdrant",
    "instrument_pinecone",
    "instrument_weaviate",
    "instrument_milvus",
    "instrument_all_vector_dbs",
    # Instrumentation - ClickHouse (custom)
    "trace_clickhouse_query",
    "trace_clickhouse_query_async",
    "instrument_clickhouse_client",
    # Instrumentation - Django Channels/WebSocket (custom)
    "trace_websocket_consumer",
    "trace_channel_layer_send",
    # Instrumentation - MinIO (custom)
    "trace_minio_operation",
    "instrument_minio_client",
    # Instrumentation - messaging
    "instrument_pika",
    # Instrumentation - async and threading
    "instrument_asyncio",
    "instrument_threading",
    # Instrumentation - other
    "instrument_grpc",
    "instrument_logging",
    "instrument_jinja2",
    # Instrumentation - convenience (all-in-one)
    "instrument_for_django",
    "instrument_for_celery",
    "instrument_for_temporal",
    # Temporal
    "get_temporal_tracing_interceptor",
    "get_interceptors_for_client",
    "init_otel_for_temporal",
    # LLM spans (manual)
    "create_llm_span",
    "set_llm_attributes",
    # Enrichment utilities (rich context capture)
    "capture_args",
    "capture_args_async",
    "add_span_context",
    "add_span_event",
    "capture_db_query",
    "capture_http_request",
    # Span naming utilities
    "django_request_hook",
    "django_response_hook",
    "get_db_span_name",
    "get_workflow_span_name",
    "get_activity_span_name",
    "get_http_client_span_name",
    "sanitize_span_name",
    # Log-trace correlation
    "init_otel_logging",
    "get_logger_provider",
    "get_logs_endpoint",
    "OTEL_LOGS_ENABLED",
]

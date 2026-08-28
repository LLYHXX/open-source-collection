"""Business context helpers for OpenTelemetry spans.

Note: OTel imports are lazy to avoid slow startup when OTEL_ENABLED=false.
"""

import functools
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)

# User context
ATTR_USER_ID = "enduser.id"
ATTR_USER_EMAIL = "enduser.email"
ATTR_ORGANIZATION_ID = "organization.id"
ATTR_ORGANIZATION_NAME = "organization.name"

# Request context
ATTR_REQUEST_ID = "request.id"
ATTR_CORRELATION_ID = "correlation.id"

# FutureAGI business context (fi.* namespace)
ATTR_FI_PROJECT_ID = "fi.project.id"
ATTR_FI_PROJECT_NAME = "fi.project.name"
ATTR_FI_EXPERIMENT_ID = "fi.experiment.id"
ATTR_FI_EXPERIMENT_NAME = "fi.experiment.name"
ATTR_FI_TRACE_ID = "fi.trace.id"  # Your internal trace ID, not OTel
ATTR_FI_SPAN_ID = "fi.span.id"  # Your internal span ID, not OTel
ATTR_FI_DATASET_ID = "fi.dataset.id"
ATTR_FI_EVAL_ID = "fi.eval.id"
ATTR_FI_WORKFLOW_ID = "fi.workflow.id"

# Error context
ATTR_ERROR_TYPE = "error.type"
ATTR_ERROR_MESSAGE = "error.message"


def get_current_span():
    """Get the current active span."""
    from opentelemetry import trace

    return trace.get_current_span()


def set_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span."""
    span = get_current_span()
    if span.is_recording():
        span.set_attribute(key, value)


def set_attributes(attributes: dict[str, Any]) -> None:
    """Set multiple attributes on the current span."""
    span = get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def set_user_context(
    user_id: Optional[str | int] = None,
    user_email: Optional[str] = None,
    organization_id: Optional[str | int] = None,
    organization_name: Optional[str] = None,
) -> None:
    """
    Set user context on the current span.

    Call this in middleware after authentication.

    Example:
        from accounts.utils import get_request_organization
        _org = get_request_organization(request)
        set_user_context(
            user_id=request.user.id,
            organization_id=_org.id if _org else None,
        )
    """
    attrs = {}
    if user_id is not None:
        attrs[ATTR_USER_ID] = str(user_id)
    if user_email is not None:
        attrs[ATTR_USER_EMAIL] = user_email
    if organization_id is not None:
        attrs[ATTR_ORGANIZATION_ID] = str(organization_id)
    if organization_name is not None:
        attrs[ATTR_ORGANIZATION_NAME] = organization_name

    set_attributes(attrs)


def set_request_context(
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set request context on the current span.

    Example:
        set_request_context(request_id=request.META.get("X-Request-ID"))
    """
    attrs = {}
    if request_id is not None:
        attrs[ATTR_REQUEST_ID] = request_id
    if correlation_id is not None:
        attrs[ATTR_CORRELATION_ID] = correlation_id

    set_attributes(attrs)


def set_business_context(
    project_id: Optional[str | int] = None,
    project_name: Optional[str] = None,
    experiment_id: Optional[str | int] = None,
    experiment_name: Optional[str] = None,
    trace_id: Optional[str | int] = None,
    span_id: Optional[str | int] = None,
    dataset_id: Optional[str | int] = None,
    eval_id: Optional[str | int] = None,
    workflow_id: Optional[str] = None,
) -> None:
    """
    Set FutureAGI business context on the current span.

    Call this when processing experiments, traces, evals, etc.

    Example:
        set_business_context(
            project_id=project.id,
            experiment_id=experiment.id,
            trace_id=trace.id,
        )
    """
    attrs = {}
    if project_id is not None:
        attrs[ATTR_FI_PROJECT_ID] = str(project_id)
    if project_name is not None:
        attrs[ATTR_FI_PROJECT_NAME] = project_name
    if experiment_id is not None:
        attrs[ATTR_FI_EXPERIMENT_ID] = str(experiment_id)
    if experiment_name is not None:
        attrs[ATTR_FI_EXPERIMENT_NAME] = experiment_name
    if trace_id is not None:
        attrs[ATTR_FI_TRACE_ID] = str(trace_id)
    if span_id is not None:
        attrs[ATTR_FI_SPAN_ID] = str(span_id)
    if dataset_id is not None:
        attrs[ATTR_FI_DATASET_ID] = str(dataset_id)
    if eval_id is not None:
        attrs[ATTR_FI_EVAL_ID] = str(eval_id)
    if workflow_id is not None:
        attrs[ATTR_FI_WORKFLOW_ID] = workflow_id

    set_attributes(attrs)


def set_error_context(
    error: Exception,
    error_type: Optional[str] = None,
) -> None:
    """
    Set error context on the current span.

    Example:
        try:
            do_something()
        except Exception as e:
            set_error_context(e)
            raise
    """
    from opentelemetry import trace

    span = get_current_span()
    if span.is_recording():
        span.set_attribute(ATTR_ERROR_TYPE, error_type or type(error).__name__)
        span.set_attribute(ATTR_ERROR_MESSAGE, str(error))
        span.record_exception(error)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))


def with_business_context(**context_kwargs):
    """
    Decorator to add business context to a function's span.

    Example:
        @with_business_context(project_id=123)
        def process_experiment(experiment_id):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            set_business_context(**context_kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_current_trace_context() -> dict[str, str]:
    """
    Get the current trace context as a dictionary of headers.

    Useful for debugging trace propagation issues.

    Returns:
        Dictionary with trace context headers (e.g., traceparent, tracestate)
    """
    from opentelemetry.propagate import inject

    headers: dict[str, str] = {}
    inject(headers)
    return headers


def log_trace_context(prefix: str = "") -> None:
    """Log the current trace context for debugging."""
    span = get_current_span()
    ctx = span.get_span_context()
    headers = get_current_trace_context()

    logger.info(
        "otel_trace_context",
        prefix=prefix,
        trace_id=format(ctx.trace_id, "032x"),
        span_id=format(ctx.span_id, "016x"),
        is_valid=ctx.is_valid,
        headers=headers,
    )


def extract_trace_context_from_headers(headers: dict[str, str]) -> None:
    """Extract and log trace context from incoming headers for debugging."""
    normalized = {k.lower(): v for k, v in headers.items()}

    logger.info(
        "otel_incoming_headers",
        traceparent=normalized.get("traceparent", "NOT_FOUND"),
        tracestate=normalized.get("tracestate", "NOT_FOUND"),
        baggage=normalized.get("baggage", "NOT_FOUND"),
    )


# =============================================================================
# Thread Context Propagation
# =============================================================================
# OpenTelemetry context is stored in contextvars, which are NOT automatically
# propagated when using Django's sync_to_async or ThreadPoolExecutor.
#
# IMPORTANT: We use OTel's context.attach()/detach() instead of Python's
# copy_context()/ctx.run(). The copy_context() approach causes:
#   "ValueError: Token was created in a different Context"
# because it copies the entire contextvars storage including OTel span tokens,
# and when spans end in the thread, they try to detach tokens that belong to
# the original context.
#
# The attach/detach approach:
# 1. Captures only the OTel Context object (not the Python contextvars Context)
# 2. Creates a NEW token when attaching in the thread
# 3. Detaches using the token created in the same thread - works correctly


def otel_sync_to_async(
    func: Optional[Callable] = None,
    *,
    thread_sensitive: bool = True,
) -> Callable:
    """
    Drop-in replacement for Django's sync_to_async that propagates OTel context.

    This is the CORRECT way to propagate OpenTelemetry context across threads.
    It uses OTel's attach/detach API which creates fresh tokens in the worker
    thread, avoiding the "Token was created in a different Context" error.

    When OTEL_ENABLED=false, this is a simple pass-through to Django's sync_to_async
    with no context operations (zero overhead).

    Why this works:
    - context.get_current() captures the OTel Context object (not Python's contextvars)
    - context.attach(ctx) creates a NEW token in the worker thread's Python context
    - context.detach(token) uses the token created in the same thread - no error

    Why copy_context() DOESN'T work:
    - copy_context() copies ALL contextvars including OTel span tokens
    - ctx.run() executes in the copied context
    - When spans end, they try to detach tokens from the original context
    - Python raises ValueError because token belongs to a different Context

    Usage:
        # As decorator
        @otel_sync_to_async(thread_sensitive=False)
        def my_sync_function():
            # LLM calls here will be children of the parent span
            ...

        # Inline
        result = await otel_sync_to_async(my_sync_func, thread_sensitive=False)(args)

    Args:
        func: Sync function to wrap (optional, for decorator use)
        thread_sensitive: Whether to run in the main thread (default True)

    Returns:
        Async wrapper function that propagates OTel context
    """
    from asgiref.sync import sync_to_async as django_sync_to_async

    from .config import OTEL_ENABLED

    def decorator(sync_func: Callable) -> Callable:
        # Fast path: if OTel is disabled, just use Django's sync_to_async directly
        if not OTEL_ENABLED:
            return django_sync_to_async(sync_func, thread_sensitive=thread_sensitive)

        @functools.wraps(sync_func)
        async def async_wrapper(*args, **kwargs):
            # Import here to avoid loading OTel when disabled
            from opentelemetry import context as otel_context

            # Capture OTel context BEFORE crossing thread boundary
            # This is the OTel Context object, NOT Python's contextvars.Context
            parent_ctx = otel_context.get_current()

            def run_with_otel_context():
                # Attach the parent OTel context in this thread
                # This creates a NEW token in this thread's Python context
                token = otel_context.attach(parent_ctx)
                try:
                    return sync_func(*args, **kwargs)
                finally:
                    # Detach using the token created in THIS thread - works correctly
                    otel_context.detach(token)

            return await django_sync_to_async(
                run_with_otel_context, thread_sensitive=thread_sensitive
            )()

        return async_wrapper

    if func is not None:
        return decorator(func)
    return decorator


# Alias for backward compatibility
sync_to_async_with_context = otel_sync_to_async


async def run_sync_with_context(func: Callable, *args, **kwargs) -> Any:
    """
    Run a synchronous function in a thread pool while preserving OTel context.

    This is useful for one-off sync calls that need to preserve trace context.
    When OTEL_ENABLED=false, this is a simple pass-through with no context operations.

    Args:
        func: Synchronous function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function

    Example:
        result = await run_sync_with_context(my_sync_llm_call, prompt="Hello")
    """
    from asgiref.sync import sync_to_async

    from .config import OTEL_ENABLED

    # Fast path: if OTel is disabled, just run directly
    if not OTEL_ENABLED:
        return await sync_to_async(func, thread_sensitive=False)(*args, **kwargs)

    from opentelemetry import context as otel_context

    # Capture OTel context before thread switch
    parent_ctx = otel_context.get_current()

    def run_with_otel_context():
        token = otel_context.attach(parent_ctx)
        try:
            return func(*args, **kwargs)
        finally:
            otel_context.detach(token)

    return await sync_to_async(run_with_otel_context, thread_sensitive=False)()


def wrap_for_thread(func: Callable) -> Callable:
    """
    Wrap a function to run with the current OTel context in any thread.

    Use this when you need to pass a callback to a ThreadPoolExecutor or
    other thread-based execution.

    When OTEL_ENABLED=false, returns the original function unchanged (zero overhead).

    Args:
        func: Function to wrap

    Returns:
        Wrapped function that will run with the captured context

    Example:
        with ThreadPoolExecutor() as executor:
            # Without wrapping, LLM calls in my_func would lose trace context
            future = executor.submit(wrap_for_thread(my_func), arg1, arg2)
    """
    from .config import OTEL_ENABLED

    # Fast path: if OTel is disabled, return the function unchanged
    if not OTEL_ENABLED:
        return func

    from opentelemetry import context as otel_context

    # Capture OTel context at wrap time
    parent_ctx = otel_context.get_current()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        token = otel_context.attach(parent_ctx)
        try:
            return func(*args, **kwargs)
        finally:
            otel_context.detach(token)

    return wrapper


def wrap_for_async(func: Callable) -> Callable:
    """
    Wrap an async function to run with the current OTel context.

    Use this when you need to ensure async functions maintain trace context
    across await boundaries.

    When OTEL_ENABLED=false, returns the original function unchanged (zero overhead).

    Args:
        func: Async function to wrap

    Returns:
        Wrapped async function that will run with the captured context

    Example:
        @wrap_for_async
        async def my_async_func():
            await some_llm_call()  # Will maintain trace context
    """
    from .config import OTEL_ENABLED

    # Fast path: if OTel is disabled, return the function unchanged
    if not OTEL_ENABLED:
        return func

    from opentelemetry import context as otel_context

    # Capture OTel context at wrap time
    parent_ctx = otel_context.get_current()

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        token = otel_context.attach(parent_ctx)
        try:
            return await func(*args, **kwargs)
        finally:
            otel_context.detach(token)

    return wrapper


def get_current_otel_context():
    """
    Get the current OpenTelemetry context object.

    Useful for manual context propagation scenarios.

    Returns:
        Current OTel Context object
    """
    from opentelemetry import context

    return context.get_current()


def attach_otel_context(ctx):
    """
    Attach an OpenTelemetry context to the current thread.

    Args:
        ctx: OTel Context object to attach

    Returns:
        Token to use with detach_otel_context

    Example:
        # In async code, capture context:
        ctx = get_current_otel_context()

        # In sync code (different thread):
        token = attach_otel_context(ctx)
        try:
            # OTel context is now active
            make_llm_call()
        finally:
            detach_otel_context(token)
    """
    from opentelemetry import context

    return context.attach(ctx)


def detach_otel_context(token):
    """
    Detach a previously attached OpenTelemetry context.

    Args:
        token: Token returned from attach_otel_context
    """
    from opentelemetry import context

    context.detach(token)


__all__ = [
    # Attribute names
    "ATTR_USER_ID",
    "ATTR_USER_EMAIL",
    "ATTR_ORGANIZATION_ID",
    "ATTR_ORGANIZATION_NAME",
    "ATTR_REQUEST_ID",
    "ATTR_CORRELATION_ID",
    "ATTR_FI_PROJECT_ID",
    "ATTR_FI_PROJECT_NAME",
    "ATTR_FI_EXPERIMENT_ID",
    "ATTR_FI_EXPERIMENT_NAME",
    "ATTR_FI_TRACE_ID",
    "ATTR_FI_SPAN_ID",
    "ATTR_FI_DATASET_ID",
    "ATTR_FI_EVAL_ID",
    "ATTR_FI_WORKFLOW_ID",
    # Functions
    "get_current_span",
    "set_attribute",
    "set_attributes",
    "set_user_context",
    "set_request_context",
    "set_business_context",
    "set_error_context",
    "with_business_context",
    # Debug helpers
    "get_current_trace_context",
    "log_trace_context",
    "extract_trace_context_from_headers",
    # Thread context propagation
    "otel_sync_to_async",
    "sync_to_async_with_context",  # Alias for otel_sync_to_async
    "run_sync_with_context",
    "wrap_for_thread",
    "get_current_otel_context",
    "attach_otel_context",
    "detach_otel_context",
]

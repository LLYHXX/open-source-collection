"""
Trace enrichment utilities for capturing rich context.

Provides decorators and utilities to capture:
- Function arguments and return values
- Database query parameters
- HTTP request/response bodies
- Custom business context
"""

import functools
import json
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

import structlog

if TYPE_CHECKING:
    from opentelemetry.trace import Span

logger = structlog.get_logger(__name__)

# Type for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# Maximum size for captured values (prevent huge payloads)
MAX_VALUE_SIZE = 4096
MAX_DICT_ITEMS = 50
MAX_LIST_ITEMS = 20


def _truncate_value(value: Any, max_size: int = MAX_VALUE_SIZE) -> str:
    """Safely convert and truncate a value for span attributes."""
    try:
        if value is None:
            return "null"
        if isinstance(value, (str, int, float, bool)):
            s = str(value)
            if len(s) > max_size:
                return s[:max_size] + "...[truncated]"
            return s
        if isinstance(value, bytes):
            s = value.decode("utf-8", errors="replace")
            if len(s) > max_size:
                return s[:max_size] + "...[truncated]"
            return s
        if isinstance(value, dict):
            # Limit dict items
            truncated = dict(list(value.items())[:MAX_DICT_ITEMS])
            if len(value) > MAX_DICT_ITEMS:
                truncated["__truncated__"] = f"{len(value) - MAX_DICT_ITEMS} more items"
            s = json.dumps(truncated, default=str, ensure_ascii=False)
            if len(s) > max_size:
                return s[:max_size] + "...[truncated]"
            return s
        if isinstance(value, (list, tuple)):
            truncated = list(value[:MAX_LIST_ITEMS])
            if len(value) > MAX_LIST_ITEMS:
                truncated.append(f"...[{len(value) - MAX_LIST_ITEMS} more items]")
            s = json.dumps(truncated, default=str, ensure_ascii=False)
            if len(s) > max_size:
                return s[:max_size] + "...[truncated]"
            return s
        # For objects, try to get useful repr
        s = repr(value)
        if len(s) > max_size:
            return s[:max_size] + "...[truncated]"
        return s
    except Exception:
        return f"<{type(value).__name__}>"


def _safe_set_attribute(span: "Span", key: str, value: Any) -> None:
    """Safely set a span attribute, handling any type."""
    try:
        if span.is_recording():
            str_value = _truncate_value(value)
            span.set_attribute(key, str_value)
    except Exception:
        pass


# Sensitive argument patterns to always exclude
_SENSITIVE_PATTERNS = ["password", "token", "secret", "key", "auth", "credential"]


def _get_safe_exclude_args(exclude_args: Optional[list[str]]) -> list[str]:
    """Get list of argument names to exclude, including sensitive patterns."""
    result = list(exclude_args) if exclude_args else []
    result.extend(_SENSITIVE_PATTERNS)
    return result


def _capture_function_args(
    span: "Span",
    func: Callable,
    args: tuple,
    kwargs: dict,
    arg_names: Optional[list[str]],
    exclude_args: list[str],
    prefix: str,
) -> None:
    """Capture function arguments on the span."""
    import inspect

    if not span.is_recording():
        return

    # Capture function name
    _safe_set_attribute(span, f"{prefix}.name", func.__qualname__)

    # Get argument names from function signature
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    # Capture positional args
    for param_name, arg_value in zip(param_names, args):
        if arg_names and param_name not in arg_names:
            continue
        if any(excl in param_name.lower() for excl in exclude_args):
            continue
        _safe_set_attribute(span, f"{prefix}.args.{param_name}", arg_value)

    # Capture keyword args
    for key, value in kwargs.items():
        if arg_names and key not in arg_names:
            continue
        if any(excl in key.lower() for excl in exclude_args):
            continue
        _safe_set_attribute(span, f"{prefix}.args.{key}", value)


def _capture_return_value(
    span: "Span",
    result: Any,
    prefix: str,
) -> None:
    """Capture function return value on the span."""
    if span.is_recording():
        _safe_set_attribute(span, f"{prefix}.return", result)


def _capture_exception(
    span: "Span",
    exc: Exception,
    prefix: str,
) -> None:
    """Capture exception details on the span."""
    if span.is_recording():
        _safe_set_attribute(span, f"{prefix}.exception.type", type(exc).__name__)
        _safe_set_attribute(span, f"{prefix}.exception.message", str(exc))


def capture_args(
    *,
    capture_return: bool = True,
    capture_exception: bool = True,
    arg_names: Optional[list[str]] = None,
    exclude_args: Optional[list[str]] = None,
    prefix: str = "function",
) -> Callable[[F], F]:
    """
    Decorator to capture function arguments and return value in the current span.

    Usage:
        @capture_args()
        def process_order(order_id: int, user_id: int, items: list):
            ...

        # Captures in span:
        # - function.args.order_id = "123"
        # - function.args.user_id = "456"
        # - function.args.items = "[...]"
        # - function.return = "..."

    Args:
        capture_return: Whether to capture return value
        capture_exception: Whether to capture exception details
        arg_names: Only capture these argument names (None = all)
        exclude_args: Exclude these argument names (e.g., ["password", "token"])
        prefix: Attribute prefix (default: "function")
    """
    safe_exclude_args = _get_safe_exclude_args(exclude_args)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from opentelemetry import trace

            span = trace.get_current_span()
            _capture_function_args(
                span, func, args, kwargs, arg_names, safe_exclude_args, prefix
            )

            try:
                result = func(*args, **kwargs)
                if capture_return:
                    _capture_return_value(span, result, prefix)
                return result
            except Exception as e:
                if capture_exception:
                    _capture_exception(span, e, prefix)
                raise

        return wrapper  # type: ignore

    return decorator


def capture_args_async(
    *,
    capture_return: bool = True,
    capture_exception: bool = True,
    arg_names: Optional[list[str]] = None,
    exclude_args: Optional[list[str]] = None,
    prefix: str = "function",
) -> Callable[[F], F]:
    """Async version of capture_args decorator."""
    safe_exclude_args = _get_safe_exclude_args(exclude_args)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from opentelemetry import trace

            span = trace.get_current_span()
            _capture_function_args(
                span, func, args, kwargs, arg_names, safe_exclude_args, prefix
            )

            try:
                result = await func(*args, **kwargs)
                if capture_return:
                    _capture_return_value(span, result, prefix)
                return result
            except Exception as e:
                if capture_exception:
                    _capture_exception(span, e, prefix)
                raise

        return wrapper  # type: ignore

    return decorator


def add_span_context(**attributes: Any) -> None:
    """
    Add custom context to the current span.

    Usage:
        add_span_context(
            user_id=request.user.id,
            order_id=order.id,
            filters={"status": "active", "limit": 10},
        )
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            _safe_set_attribute(span, key, value)


def add_span_event(
    name: str,
    **attributes: Any,
) -> None:
    """
    Add an event to the current span (like a log within the trace).

    Usage:
        add_span_event("cache_miss", key="user:123")
        add_span_event("validation_failed", field="email", reason="invalid format")
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        safe_attrs = {}
        for key, value in attributes.items():
            safe_attrs[key] = _truncate_value(value)
        span.add_event(name, attributes=safe_attrs)


def capture_db_query(
    query: str,
    params: Any = None,
    rows_affected: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Capture database query details in the current span.

    Usage:
        capture_db_query(
            query="SELECT * FROM users WHERE status = %s AND created_at > %s",
            params=["active", "2024-01-01"],
            rows_affected=42,
            duration_ms=15.3,
        )
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        _safe_set_attribute(span, "db.statement", query)
        if params:
            _safe_set_attribute(span, "db.params", params)
        if rows_affected is not None:
            span.set_attribute("db.rows_affected", rows_affected)
        if duration_ms is not None:
            span.set_attribute("db.duration_ms", duration_ms)


def capture_http_request(
    method: str,
    url: str,
    headers: Optional[dict] = None,
    body: Optional[Any] = None,
    status_code: Optional[int] = None,
    response_body: Optional[Any] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Capture HTTP request/response details in the current span.

    Usage:
        capture_http_request(
            method="POST",
            url="https://api.openai.com/v1/chat/completions",
            body={"model": "gpt-4", "messages": [...]},
            status_code=200,
            response_body={"choices": [...]},
            duration_ms=1234.5,
        )
    """
    from opentelemetry import trace

    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)
        if headers:
            # Filter out sensitive headers
            safe_headers = {
                k: v
                for k, v in headers.items()
                if k.lower()
                not in ("authorization", "x-api-key", "cookie", "set-cookie")
            }
            _safe_set_attribute(span, "http.request.headers", safe_headers)
        if body:
            _safe_set_attribute(span, "http.request.body", body)
        if status_code is not None:
            span.set_attribute("http.status_code", status_code)
        if response_body:
            _safe_set_attribute(span, "http.response.body", response_body)
        if duration_ms is not None:
            span.set_attribute("http.duration_ms", duration_ms)


__all__ = [
    "capture_args",
    "capture_args_async",
    "add_span_context",
    "add_span_event",
    "capture_db_query",
    "capture_http_request",
]

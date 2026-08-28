"""
LLM-specific span creation utilities.

Provides helpers for creating spans with LLM/AI-specific attributes
following OpenTelemetry semantic conventions for generative AI.

Note: OTel imports are lazy to avoid slow startup when OTEL_ENABLED=false.

Reference:
- OpenTelemetry Semantic Conventions for GenAI: https://opentelemetry.io/docs/specs/semconv/gen-ai/
- FutureAGI unified tracing convention

Usage:
    from tfc.telemetry import get_tracer, create_llm_span

    tracer = get_tracer(__name__)

    with create_llm_span(tracer, "gpt-4-inference", model="gpt-4", provider="openai") as span:
        response = call_openai()
        span.set_attribute("gen_ai.usage.total_tokens", response.usage.total_tokens)
"""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

# Type hints only - no runtime import cost
if TYPE_CHECKING:
    from opentelemetry import trace
    from opentelemetry.trace import Span

# ---------------------------------------------------------------------------
# Span kind attribute
# ---------------------------------------------------------------------------
GEN_AI_SPAN_KIND = "gen_ai.span.kind"
FI_SPAN_KIND = GEN_AI_SPAN_KIND  # Backward compatibility alias

# Span kind values (unified convention)
FI_SPAN_KIND_LLM = "LLM"
FI_SPAN_KIND_EMBEDDING = "EMBEDDING"
FI_SPAN_KIND_RETRIEVER = "RETRIEVER"
FI_SPAN_KIND_CHAIN = "CHAIN"
FI_SPAN_KIND_TOOL = "TOOL"
FI_SPAN_KIND_AGENT = "AGENT"
FI_SPAN_KIND_RERANKER = "RERANKER"
FI_SPAN_KIND_GUARDRAIL = "GUARDRAIL"
FI_SPAN_KIND_EVALUATOR = "EVALUATOR"
FI_SPAN_KIND_CONVERSATION = "CONVERSATION"
FI_SPAN_KIND_UNKNOWN = "UNKNOWN"
# Deprecated: use FI_SPAN_KIND_RETRIEVER
FI_SPAN_KIND_RETRIEVAL = FI_SPAN_KIND_RETRIEVER

# Operation name
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"

# ---------------------------------------------------------------------------
# Model attributes (gen_ai.* primary, llm.* legacy dual-write)
# ---------------------------------------------------------------------------
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_PROVIDER_NAME = "gen_ai.provider.name"
GEN_AI_SYSTEM = "gen_ai.system"
# Legacy aliases (kept for backward compat, used internally for dual-writes)
LLM_MODEL_NAME = "llm.model_name"
LLM_PROVIDER = "llm.provider"
LLM_REQUEST_MODEL = GEN_AI_REQUEST_MODEL  # Alias
LLM_SYSTEM = GEN_AI_SYSTEM  # Alias

# ---------------------------------------------------------------------------
# Input/Output
# ---------------------------------------------------------------------------
INPUT_VALUE = "input.value"
OUTPUT_VALUE = "output.value"
INPUT_MIME_TYPE = "input.mime_type"
OUTPUT_MIME_TYPE = "output.mime_type"

# ---------------------------------------------------------------------------
# Token counts (gen_ai.* primary, llm.* legacy dual-write)
# ---------------------------------------------------------------------------
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_USAGE_TOTAL_TOKENS = "gen_ai.usage.total_tokens"
# Legacy aliases
LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"
LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"

# ---------------------------------------------------------------------------
# Model parameters (gen_ai.request.* primary, llm.* legacy dual-write)
# ---------------------------------------------------------------------------
GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
GEN_AI_REQUEST_TOP_P = "gen_ai.request.top_p"
GEN_AI_REQUEST_FREQUENCY_PENALTY = "gen_ai.request.frequency_penalty"
GEN_AI_REQUEST_PRESENCE_PENALTY = "gen_ai.request.presence_penalty"
# Legacy aliases
LLM_TEMPERATURE = "llm.temperature"
LLM_MAX_TOKENS = "llm.max_tokens"
LLM_TOP_P = "llm.top_p"
LLM_FREQUENCY_PENALTY = "llm.frequency_penalty"
LLM_PRESENCE_PENALTY = "llm.presence_penalty"

# ---------------------------------------------------------------------------
# Response metadata (gen_ai.* primary, llm.* legacy dual-write)
# ---------------------------------------------------------------------------
GEN_AI_RESPONSE_ID = "gen_ai.response.id"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_CLIENT_OPERATION_DURATION = "gen_ai.client.operation.duration"
# Legacy aliases
LLM_RESPONSE_ID = "llm.response.id"
LLM_RESPONSE_FINISH_REASON = "llm.response.finish_reason"
LLM_RESPONSE_LATENCY_MS = "llm.response.latency_ms"

# ---------------------------------------------------------------------------
# Error tracking (OTEL standard: error.*, not llm.error.*)
# ---------------------------------------------------------------------------
ERROR_TYPE = "error.type"
ERROR_MESSAGE = "error.message"
# Legacy aliases
LLM_ERROR_TYPE = "llm.error.type"
LLM_ERROR_MESSAGE = "llm.error.message"

# ---------------------------------------------------------------------------
# Domain-specific attributes used by helper functions
# ---------------------------------------------------------------------------
GEN_AI_RETRIEVAL_QUERY = "gen_ai.retrieval.query"
GEN_AI_RETRIEVAL_TOP_K = "gen_ai.retrieval.top_k"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"
GEN_AI_AGENT_NAME = "gen_ai.agent.name"
GEN_AI_AGENT_DESCRIPTION = "gen_ai.agent.description"


def set_llm_attributes(
    span: "Span",
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    span_kind: str = FI_SPAN_KIND_LLM,
    operation_name: Optional[str] = None,
    input_value: Optional[str] = None,
    output_value: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    presence_penalty: Optional[float] = None,
    response_id: Optional[str] = None,
    finish_reason: Optional[str] = None,
    latency_ms: Optional[float] = None,
    extra_attributes: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Set LLM-specific attributes on a span.

    Dual-writes both gen_ai.* (OTEL standard) and llm.* (legacy) attributes
    for backward compatibility with existing consumers.

    Args:
        span: The span to add attributes to
        model: Model name (e.g., "gpt-4", "claude-3-opus")
        provider: Provider name (e.g., "openai", "anthropic")
        span_kind: Span kind (LLM, EMBEDDING, RETRIEVER, etc.)
        operation_name: Operation type (e.g., "chat", "image_generation")
        input_value: Input text/prompt (truncate sensitive data)
        output_value: Output text/response (truncate sensitive data)
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        total_tokens: Total tokens (prompt + completion)
        temperature: Model temperature parameter
        max_tokens: Max tokens parameter
        top_p: Top-p (nucleus sampling) parameter
        frequency_penalty: Frequency penalty parameter
        presence_penalty: Presence penalty parameter
        response_id: Provider's response ID
        finish_reason: Why the model stopped (e.g., "stop", "length")
        latency_ms: Response latency in milliseconds
        extra_attributes: Additional custom attributes
    """
    # Span kind
    span.set_attribute(GEN_AI_SPAN_KIND, span_kind)

    # Operation name
    if operation_name:
        span.set_attribute(GEN_AI_OPERATION_NAME, operation_name)

    # Model info (dual-write gen_ai.* + legacy llm.*)
    if model:
        span.set_attribute(GEN_AI_REQUEST_MODEL, model)
        span.set_attribute(LLM_MODEL_NAME, model)

    if provider:
        span.set_attribute(GEN_AI_PROVIDER_NAME, provider)
        span.set_attribute(GEN_AI_SYSTEM, provider)
        span.set_attribute(LLM_PROVIDER, provider)

    # Input/Output
    if input_value is not None:
        span.set_attribute(INPUT_VALUE, input_value)

    if output_value is not None:
        span.set_attribute(OUTPUT_VALUE, output_value)

    # Token counts (dual-write gen_ai.* + legacy llm.*)
    if prompt_tokens is not None:
        span.set_attribute(GEN_AI_USAGE_INPUT_TOKENS, prompt_tokens)
        span.set_attribute(LLM_TOKEN_COUNT_PROMPT, prompt_tokens)

    if completion_tokens is not None:
        span.set_attribute(GEN_AI_USAGE_OUTPUT_TOKENS, completion_tokens)
        span.set_attribute(LLM_TOKEN_COUNT_COMPLETION, completion_tokens)

    if total_tokens is not None:
        span.set_attribute(GEN_AI_USAGE_TOTAL_TOKENS, total_tokens)
        span.set_attribute(LLM_TOKEN_COUNT_TOTAL, total_tokens)
    elif prompt_tokens is not None and completion_tokens is not None:
        total = prompt_tokens + completion_tokens
        span.set_attribute(GEN_AI_USAGE_TOTAL_TOKENS, total)
        span.set_attribute(LLM_TOKEN_COUNT_TOTAL, total)

    # Model parameters (dual-write gen_ai.request.* + legacy llm.*)
    if temperature is not None:
        span.set_attribute(GEN_AI_REQUEST_TEMPERATURE, temperature)
        span.set_attribute(LLM_TEMPERATURE, temperature)

    if max_tokens is not None:
        span.set_attribute(GEN_AI_REQUEST_MAX_TOKENS, max_tokens)
        span.set_attribute(LLM_MAX_TOKENS, max_tokens)

    if top_p is not None:
        span.set_attribute(GEN_AI_REQUEST_TOP_P, top_p)
        span.set_attribute(LLM_TOP_P, top_p)

    if frequency_penalty is not None:
        span.set_attribute(GEN_AI_REQUEST_FREQUENCY_PENALTY, frequency_penalty)
        span.set_attribute(LLM_FREQUENCY_PENALTY, frequency_penalty)

    if presence_penalty is not None:
        span.set_attribute(GEN_AI_REQUEST_PRESENCE_PENALTY, presence_penalty)
        span.set_attribute(LLM_PRESENCE_PENALTY, presence_penalty)

    # Response metadata (dual-write gen_ai.* + legacy llm.*)
    if response_id:
        span.set_attribute(GEN_AI_RESPONSE_ID, response_id)
        span.set_attribute(LLM_RESPONSE_ID, response_id)

    if finish_reason:
        span.set_attribute(GEN_AI_RESPONSE_FINISH_REASONS, [finish_reason])
        span.set_attribute(LLM_RESPONSE_FINISH_REASON, finish_reason)

    if latency_ms is not None:
        span.set_attribute(GEN_AI_CLIENT_OPERATION_DURATION, latency_ms)
        span.set_attribute(LLM_RESPONSE_LATENCY_MS, latency_ms)

    # Extra attributes
    if extra_attributes:
        for key, value in extra_attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def set_llm_error(
    span: "Span",
    error: Exception,
    error_type: Optional[str] = None,
) -> None:
    """
    Record an LLM error on a span.

    Sets both OTEL standard error.* and legacy llm.error.* attributes.

    Args:
        span: The span to record the error on
        error: The exception that occurred
        error_type: Optional error type classification
    """
    from opentelemetry.trace import Status, StatusCode

    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)

    if error_type:
        span.set_attribute(ERROR_TYPE, error_type)
        span.set_attribute(LLM_ERROR_TYPE, error_type)

    error_msg = str(error)
    span.set_attribute(ERROR_MESSAGE, error_msg)
    span.set_attribute(LLM_ERROR_MESSAGE, error_msg)


@contextmanager
def create_llm_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    span_kind: str = FI_SPAN_KIND_LLM,
    operation_name: Optional[str] = None,
    input_value: Optional[str] = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating LLM inference spans.

    Creates a span with LLM-specific attributes pre-configured.
    The span is automatically ended when the context exits.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name (e.g., "gpt-4-inference", "claude-embedding")
        model: Model name
        provider: Provider name
        span_kind: Span kind (LLM, EMBEDDING, RETRIEVER, etc.)
        operation_name: Operation type (e.g., "chat", "image_generation")
        input_value: Input prompt (will be truncated if too long)
        record_exception: Whether to record exceptions
        set_status_on_exception: Whether to set error status on exception
        **extra_attributes: Additional attributes to set

    Yields:
        The created span

    Example:
        tracer = get_tracer(__name__)

        with create_llm_span(
            tracer,
            "openai-completion",
            model="gpt-4",
            provider="openai",
            operation_name="chat",
            input_value=prompt[:1000],
        ) as span:
            start_time = time.time()
            response = openai.chat.completions.create(...)
            latency_ms = (time.time() - start_time) * 1000

            span.set_attribute("gen_ai.usage.total_tokens", response.usage.total_tokens)
            span.set_attribute("gen_ai.client.operation.duration", latency_ms)
    """
    from opentelemetry.trace import SpanKind

    with tracer.start_as_current_span(
        name,
        kind=SpanKind.CLIENT,
        record_exception=record_exception,
        set_status_on_exception=set_status_on_exception,
    ) as span:
        # Set initial attributes
        set_llm_attributes(
            span,
            model=model,
            provider=provider,
            span_kind=span_kind,
            operation_name=operation_name,
            input_value=input_value,
            extra_attributes=extra_attributes if extra_attributes else None,
        )

        yield span


@contextmanager
def create_embedding_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    input_text: Optional[str] = None,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating embedding generation spans.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name (e.g., "openai-embedding")
        model: Model name (e.g., "text-embedding-3-small")
        provider: Provider name
        input_text: Text being embedded
        **extra_attributes: Additional attributes

    Yields:
        The created span
    """
    with create_llm_span(
        tracer,
        name,
        model=model,
        provider=provider,
        span_kind=FI_SPAN_KIND_EMBEDDING,
        operation_name="embeddings",
        input_value=input_text,
        **extra_attributes,
    ) as span:
        yield span


@contextmanager
def create_retrieval_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    query: Optional[str] = None,
    index_name: Optional[str] = None,
    top_k: Optional[int] = None,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating retrieval/search spans.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name (e.g., "pinecone-search")
        query: Search query
        index_name: Name of the search index
        top_k: Number of results requested
        **extra_attributes: Additional attributes

    Yields:
        The created span
    """
    extra = dict(extra_attributes)
    if query:
        extra[GEN_AI_RETRIEVAL_QUERY] = query
    if index_name:
        extra["retrieval.index_name"] = index_name
    if top_k:
        extra[GEN_AI_RETRIEVAL_TOP_K] = top_k

    with create_llm_span(
        tracer,
        name,
        span_kind=FI_SPAN_KIND_RETRIEVER,
        input_value=query,
        **extra,
    ) as span:
        yield span


@contextmanager
def create_chain_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    chain_type: Optional[str] = None,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating chain/pipeline spans.

    Use this for LangChain chains or custom multi-step pipelines.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name (e.g., "rag-chain")
        chain_type: Type of chain (e.g., "retrieval_qa", "conversational")
        **extra_attributes: Additional attributes

    Yields:
        The created span
    """
    extra = dict(extra_attributes)
    if chain_type:
        extra["chain.type"] = chain_type

    with create_llm_span(
        tracer,
        name,
        span_kind=FI_SPAN_KIND_CHAIN,
        **extra,
    ) as span:
        yield span


@contextmanager
def create_tool_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    tool_name: Optional[str] = None,
    tool_input: Optional[str] = None,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating tool execution spans.

    Use this for function/tool calls in agent systems.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name
        tool_name: Name of the tool being executed
        tool_input: Input to the tool (JSON string or description)
        **extra_attributes: Additional attributes

    Yields:
        The created span
    """
    extra = dict(extra_attributes)
    if tool_name:
        extra[GEN_AI_TOOL_NAME] = tool_name

    with create_llm_span(
        tracer,
        name,
        span_kind=FI_SPAN_KIND_TOOL,
        operation_name="execute_tool",
        input_value=tool_input,
        **extra,
    ) as span:
        yield span


@contextmanager
def create_agent_span(
    tracer,  # trace.Tracer
    name: str,
    *,
    agent_name: Optional[str] = None,
    agent_description: Optional[str] = None,
    # Deprecated parameter name kept for backward compat
    agent_type: Optional[str] = None,
    **extra_attributes,
) -> Iterator["Span"]:
    """
    Context manager for creating agent execution spans.

    Use this as the parent span for agent loops.

    Args:
        tracer: OpenTelemetry tracer instance
        name: Span name
        agent_name: Name of the agent
        agent_description: Description of the agent
        agent_type: Deprecated, use agent_description instead
        **extra_attributes: Additional attributes

    Yields:
        The created span
    """
    extra = dict(extra_attributes)
    if agent_name:
        extra[GEN_AI_AGENT_NAME] = agent_name
    description = agent_description or agent_type
    if description:
        extra[GEN_AI_AGENT_DESCRIPTION] = description

    with create_llm_span(
        tracer,
        name,
        span_kind=FI_SPAN_KIND_AGENT,
        **extra,
    ) as span:
        yield span


__all__ = [
    # Span kind attribute
    "GEN_AI_SPAN_KIND",
    "FI_SPAN_KIND",
    # Span kind values
    "FI_SPAN_KIND_LLM",
    "FI_SPAN_KIND_EMBEDDING",
    "FI_SPAN_KIND_RETRIEVER",
    "FI_SPAN_KIND_RETRIEVAL",  # Deprecated alias for RETRIEVER
    "FI_SPAN_KIND_CHAIN",
    "FI_SPAN_KIND_TOOL",
    "FI_SPAN_KIND_AGENT",
    "FI_SPAN_KIND_RERANKER",
    "FI_SPAN_KIND_GUARDRAIL",
    "FI_SPAN_KIND_EVALUATOR",
    "FI_SPAN_KIND_CONVERSATION",
    "FI_SPAN_KIND_UNKNOWN",
    # Operation name
    "GEN_AI_OPERATION_NAME",
    # Model attribute constants (gen_ai.* primary)
    "GEN_AI_REQUEST_MODEL",
    "GEN_AI_PROVIDER_NAME",
    "GEN_AI_SYSTEM",
    "LLM_MODEL_NAME",
    "LLM_PROVIDER",
    "LLM_REQUEST_MODEL",
    "LLM_SYSTEM",
    # Input/Output
    "INPUT_VALUE",
    "OUTPUT_VALUE",
    "INPUT_MIME_TYPE",
    "OUTPUT_MIME_TYPE",
    # Token counts (gen_ai.* primary)
    "GEN_AI_USAGE_INPUT_TOKENS",
    "GEN_AI_USAGE_OUTPUT_TOKENS",
    "GEN_AI_USAGE_TOTAL_TOKENS",
    "LLM_TOKEN_COUNT_TOTAL",
    "LLM_TOKEN_COUNT_PROMPT",
    "LLM_TOKEN_COUNT_COMPLETION",
    # Model parameters (gen_ai.request.* primary)
    "GEN_AI_REQUEST_TEMPERATURE",
    "GEN_AI_REQUEST_MAX_TOKENS",
    "GEN_AI_REQUEST_TOP_P",
    "GEN_AI_REQUEST_FREQUENCY_PENALTY",
    "GEN_AI_REQUEST_PRESENCE_PENALTY",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "LLM_TOP_P",
    "LLM_FREQUENCY_PENALTY",
    "LLM_PRESENCE_PENALTY",
    # Response metadata (gen_ai.* primary)
    "GEN_AI_RESPONSE_ID",
    "GEN_AI_RESPONSE_FINISH_REASONS",
    "GEN_AI_CLIENT_OPERATION_DURATION",
    "LLM_RESPONSE_ID",
    "LLM_RESPONSE_FINISH_REASON",
    "LLM_RESPONSE_LATENCY_MS",
    # Error tracking (OTEL standard)
    "ERROR_TYPE",
    "ERROR_MESSAGE",
    "LLM_ERROR_TYPE",
    "LLM_ERROR_MESSAGE",
    # Domain-specific attributes
    "GEN_AI_RETRIEVAL_QUERY",
    "GEN_AI_RETRIEVAL_TOP_K",
    "GEN_AI_TOOL_NAME",
    "GEN_AI_AGENT_NAME",
    "GEN_AI_AGENT_DESCRIPTION",
    # Functions
    "set_llm_attributes",
    "set_llm_error",
    # Context managers
    "create_llm_span",
    "create_embedding_span",
    "create_retrieval_span",
    "create_chain_span",
    "create_tool_span",
    "create_agent_span",
]

"""
OpenLLMetry adapter — handles traces from Traceloop's OpenLLMetry SDK via OTLP.

OpenLLMetry uses two attribute layers:

1. OTel GenAI semantic conventions: ``gen_ai.*`` (model, tokens, prompts, completions)
2. Traceloop proprietary: ``traceloop.*`` (span kind, entity, prompt management)

It also sends some legacy ``llm.*`` attributes that differ from the fi.* convention.

Detection: any ``gen_ai.*`` or ``traceloop.*`` attribute present.

Key attribute shapes (legacy mode, the default):
  - gen_ai.system: "openai" | "Anthropic" | ...
  - gen_ai.request.model / gen_ai.response.model: model name string
  - gen_ai.usage.input_tokens / gen_ai.usage.prompt_tokens: int
  - gen_ai.usage.output_tokens / gen_ai.usage.completion_tokens: int
  - gen_ai.prompt.{i}.role / gen_ai.prompt.{i}.content: indexed message attrs
  - gen_ai.completion.{i}.role / gen_ai.completion.{i}.content: indexed completion attrs
  - gen_ai.request.temperature / gen_ai.request.max_tokens / ...: individual params
  - traceloop.span.kind: "workflow" | "task" | "agent" | "tool"
  - traceloop.entity.input / traceloop.entity.output: JSON strings

Source: github.com/traceloop/openllmetry
"""

import json
import re
from typing import Any

from tracer.utils.adapters.base import (
    BaseTraceAdapter,
    extract_query,
    first_not_none,
    flatten_input_messages,
    flatten_output_messages,
    parse_json_attr,
    register_adapter,
    set_io_value,
    strip_keys,
)
from tracer.utils.otel import SpanAttributes

# traceloop.span.kind → fi.span.kind
_TRACELOOP_KIND_MAP = {
    "workflow": "CHAIN",
    "task": "CHAIN",
    "agent": "AGENT",
    "tool": "TOOL",
    "unknown": "UNKNOWN",
}

# gen_ai.operation.name / llm.request.type → fi.span.kind
_OPERATION_KIND_MAP = {
    "chat": "LLM",
    "completion": "LLM",
    "embedding": "EMBEDDING",
    "embeddings": "EMBEDDING",
    "rerank": "RERANKER",
    "execute_tool": "TOOL",
}

# gen_ai.system values → normalized provider name
_SYSTEM_PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "cohere": "cohere",
    "mistralai": "mistralai",
    "google": "google",
    "ollama": "ollama",
    "groq": "groq",
    "deepseek": "deepseek",
    "meta": "meta",
    "bedrock": "aws_bedrock",
    "azure": "azure_openai",
}

# gen_ai.request.* keys that map to invocation parameters
_REQUEST_PARAM_KEYS = {
    "gen_ai.request.temperature": "temperature",
    "gen_ai.request.max_tokens": "max_tokens",
    "gen_ai.request.top_p": "top_p",
    "gen_ai.request.top_k": "top_k",
    "gen_ai.request.frequency_penalty": "frequency_penalty",
    "gen_ai.request.presence_penalty": "presence_penalty",
    "gen_ai.request.seed": "seed",
    "gen_ai.request.stop_sequences": "stop_sequences",
    "gen_ai.request.reasoning_effort": "reasoning_effort",
}

# Traceloop-specific llm.* keys to strip (NOT part of fi-native convention)
_TRACELOOP_LLM_KEYS = frozenset(
    {
        "llm.request.type",
        "llm.frequency_penalty",
        "llm.presence_penalty",
        "llm.top_k",
        "llm.chat.stop_sequences",
        "llm.is_streaming",
        "llm.user",
        "llm.headers",
        "llm.request.functions",
        "llm.request.repetition_penalty",
        "llm.request.structured_output_schema",
        "llm.request.reasoning_effort",
        "llm.response.finish_reason",
        "llm.response.stop_reason",
        "llm.usage.total_tokens",
        "llm.content.completion.chunk",
    }
)

# Regex for indexed prompt/completion attributes
_PROMPT_RE = re.compile(r"^gen_ai\.prompt\.(\d+)\.(.+)$")
_COMPLETION_RE = re.compile(r"^gen_ai\.completion\.(\d+)\.(.+)$")


def _extract_indexed_messages(
    attributes: dict[str, Any], prefix_re: re.Pattern
) -> list[dict[str, Any]]:
    """
    Extract indexed message attributes into a list of message dicts.

    Handles ``gen_ai.prompt.{i}.role``, ``gen_ai.prompt.{i}.content``,
    ``gen_ai.prompt.{i}.tool_calls.{j}.*``, etc.
    """
    messages: dict[int, dict[str, Any]] = {}
    for key, val in attributes.items():
        m = prefix_re.match(key)
        if not m:
            continue
        idx = int(m.group(1))
        field = m.group(2)
        if idx not in messages:
            messages[idx] = {}
        # Parse JSON-encoded content (e.g. multi-part content blocks)
        if field == "content" and isinstance(val, str):
            parsed = parse_json_attr(val)
            messages[idx][field] = parsed
        else:
            messages[idx][field] = val

    if not messages:
        return []

    result = []
    for idx in sorted(messages.keys()):
        msg = messages[idx]
        result.append(
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                **{k: v for k, v in msg.items() if k not in ("role", "content")},
            }
        )
    return result


class OpenLLMetryAdapter(BaseTraceAdapter):
    @property
    def source_name(self) -> str:
        return "openllmetry"

    def detect(self, attributes: dict[str, Any]) -> bool:
        # Only match actual OpenLLMetry SDK spans (traceloop.* marker present).
        # Plain gen_ai.* spans (e.g. from traceai SDK) use standard OTEL GenAI
        # conventions and are handled by the OtelGenAIAdapter instead.
        return any(k.startswith("traceloop.") for k in attributes)

    def normalize(self, attributes: dict[str, Any]) -> dict[str, Any]:
        # --- Extract values before stripping ---

        # Span kind
        traceloop_kind = attributes.get("traceloop.span.kind", "").lower()
        operation_name = attributes.get("gen_ai.operation.name", "").lower()
        request_type = attributes.get("llm.request.type", "").lower()

        # Model (response model takes priority — it's the actual model used)
        model = first_not_none(
            attributes.get("gen_ai.response.model"),
            attributes.get("gen_ai.request.model"),
        )

        # Provider
        system = first_not_none(
            attributes.get("gen_ai.system"),
            attributes.get("gen_ai.provider.name"),
        )
        if system:
            system = system.lower()

        # Token counts (both old and new OTel formats)
        prompt_tokens = first_not_none(
            attributes.get("gen_ai.usage.input_tokens"),
            attributes.get("gen_ai.usage.prompt_tokens"),
        )
        completion_tokens = first_not_none(
            attributes.get("gen_ai.usage.output_tokens"),
            attributes.get("gen_ai.usage.completion_tokens"),
        )
        total_tokens = first_not_none(
            attributes.get("gen_ai.usage.total_tokens"),
            attributes.get("llm.usage.total_tokens"),
        )

        # Model parameters from individual gen_ai.request.* keys
        invocation_params = {}
        for gen_ai_key, param_name in _REQUEST_PARAM_KEYS.items():
            val = attributes.get(gen_ai_key)
            if val is not None:
                invocation_params[param_name] = val

        # Extract input/output messages (legacy indexed format)
        input_messages = _extract_indexed_messages(attributes, _PROMPT_RE)
        output_messages = _extract_indexed_messages(attributes, _COMPLETION_RE)

        # Traceloop entity input/output (fallback for non-LLM spans)
        entity_input = attributes.get("traceloop.entity.input")
        entity_output = attributes.get("traceloop.entity.output")

        # Traceloop prompt management
        prompt_key = attributes.get("traceloop.prompt.key")
        prompt_version = attributes.get("traceloop.prompt.version")
        prompt_template = attributes.get("traceloop.prompt.template")
        prompt_variables = attributes.get("traceloop.prompt.template_variables")

        # Association properties → metadata
        assoc_props = attributes.get("traceloop.association.properties")

        # --- Strip foreign keys ---
        strip_keys(attributes, "gen_ai.", "traceloop.")
        to_remove = [k for k in attributes if k in _TRACELOOP_LLM_KEYS]
        for k in to_remove:
            del attributes[k]

        # --- Determine span kind ---
        span_kind = ""
        if traceloop_kind in _TRACELOOP_KIND_MAP:
            span_kind = _TRACELOOP_KIND_MAP[traceloop_kind]
        elif operation_name in _OPERATION_KIND_MAP:
            span_kind = _OPERATION_KIND_MAP[operation_name]
        elif request_type in _OPERATION_KIND_MAP:
            span_kind = _OPERATION_KIND_MAP[request_type]
        elif model:
            span_kind = "LLM"

        if span_kind:
            attributes[SpanAttributes.FI_SPAN_KIND] = span_kind
        is_llm = span_kind == "LLM"

        # --- input.value / output.value ---
        if is_llm and input_messages:
            set_io_value(attributes, "input", input_messages)
        elif entity_input is not None:
            set_io_value(attributes, "input", parse_json_attr(entity_input))

        if is_llm and output_messages:
            obs_output = (
                output_messages[0] if len(output_messages) == 1 else output_messages
            )
            set_io_value(attributes, "output", obs_output)
        elif entity_output is not None:
            set_io_value(attributes, "output", parse_json_attr(entity_output))

        # --- LLM-specific ---
        if is_llm:
            if model:
                attributes[SpanAttributes.LLM_MODEL_NAME] = model
            provider = _SYSTEM_PROVIDER_MAP.get(system, system or "")
            if provider:
                attributes[SpanAttributes.LLM_PROVIDER] = provider
                attributes[SpanAttributes.LLM_SYSTEM] = provider

            if prompt_tokens is not None:
                attributes[SpanAttributes.LLM_TOKEN_COUNT_PROMPT] = int(prompt_tokens)
            if completion_tokens is not None:
                attributes[SpanAttributes.LLM_TOKEN_COUNT_COMPLETION] = int(
                    completion_tokens
                )
            if total_tokens is not None:
                attributes[SpanAttributes.LLM_TOKEN_COUNT_TOTAL] = int(total_tokens)
            elif prompt_tokens is not None and completion_tokens is not None:
                attributes[SpanAttributes.LLM_TOKEN_COUNT_TOTAL] = int(
                    prompt_tokens
                ) + int(completion_tokens)

            if invocation_params:
                attributes[SpanAttributes.LLM_INVOCATION_PARAMETERS] = invocation_params

            # Flatten messages
            if input_messages:
                flatten_input_messages(input_messages, attributes)
                extract_query(input_messages, attributes)
                attributes[SpanAttributes.RAW_INPUT] = input_messages

            if output_messages:
                flatten_output_messages(output_messages, attributes)
                raw = (
                    output_messages[0] if len(output_messages) == 1 else output_messages
                )
                attributes[SpanAttributes.RAW_OUTPUT] = raw

        # --- Prompt template ---
        if prompt_key is not None:
            attributes[SpanAttributes.FI_PROMPT_TEMPLATE_NAME] = prompt_key
        if prompt_version is not None:
            attributes[SpanAttributes.LLM_PROMPT_TEMPLATE_VERSION] = prompt_version
        if prompt_template is not None:
            attributes[SpanAttributes.LLM_PROMPT_TEMPLATE] = prompt_template
        if prompt_variables is not None:
            attributes[SpanAttributes.LLM_PROMPT_TEMPLATE_VARIABLES] = parse_json_attr(
                prompt_variables
            )

        # --- Metadata ---
        if assoc_props is not None:
            parsed = parse_json_attr(assoc_props)
            if parsed and SpanAttributes.METADATA not in attributes:
                attributes[SpanAttributes.METADATA] = parsed

        attributes["gen_ai.trace.source"] = self.source_name
        return attributes


register_adapter("openllmetry", OpenLLMetryAdapter(), priority=8)

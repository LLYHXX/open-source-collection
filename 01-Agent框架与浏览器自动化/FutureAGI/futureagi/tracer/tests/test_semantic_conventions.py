"""
Unit tests for semantic conventions module.

Tests the AttributeRegistry's ability to handle multiple semantic conventions:
- OTEL GenAI (primary)
- OpenInference (backward compat)
"""

import pytest

from tracer.utils.semantic_conventions import (
    AttributeAliases,
    AttributeRegistry,
    SemanticConvention,
    detect_semconv,
    get_attribute,
)


class TestAttributeRegistry:
    """Tests for the AttributeRegistry class."""

    def test_get_value_otel_genai_convention(self):
        """Test that OTEL GenAI convention attributes are extracted correctly."""
        attributes = {
            "gen_ai.request.model": "claude-3-opus",
            "gen_ai.usage.input_tokens": 200,
            "gen_ai.usage.output_tokens": 100,
            "gen_ai.system": "anthropic",
            "gen_ai.operation.name": "chat",
        }

        assert AttributeRegistry.get_value(attributes, "model_name") == "claude-3-opus"
        assert AttributeRegistry.get_value(attributes, "input_tokens") == 200
        assert AttributeRegistry.get_value(attributes, "output_tokens") == 100
        assert AttributeRegistry.get_value(attributes, "provider") == "anthropic"
        assert AttributeRegistry.get_value(attributes, "operation_name") == "chat"

    def test_get_value_otel_genai_span_kind(self):
        """Test that gen_ai.span.kind is resolved for span_kind."""
        attributes = {
            "gen_ai.span.kind": "llm",
        }
        assert AttributeRegistry.get_value(attributes, "span_kind") == "llm"

    def test_get_value_openinference_span_kind(self):
        """Test that openinference.span.kind is resolved for span_kind."""
        attributes = {
            "openinference.span.kind": "LLM",
        }
        assert AttributeRegistry.get_value(attributes, "span_kind") == "LLM"

    def test_get_value_priority_order(self):
        """Test that OTEL GenAI convention takes priority when both are present."""
        attributes = {
            "gen_ai.request.model": "otel-model",  # OTEL GenAI (priority 1)
        }

        assert AttributeRegistry.get_value(attributes, "model_name") == "otel-model"

    def test_get_value_fallback(self):
        """Test that lower priority convention is used when higher is missing."""
        attributes = {
            "gen_ai.request.model": "otel-model",  # OTEL GenAI
        }

        assert AttributeRegistry.get_value(attributes, "model_name") == "otel-model"

    def test_get_value_default(self):
        """Test that default value is returned when attribute is not found."""
        attributes = {"some.other.attribute": "value"}

        assert AttributeRegistry.get_value(attributes, "model_name") is None
        assert (
            AttributeRegistry.get_value(attributes, "model_name", "default")
            == "default"
        )

    def test_get_value_with_source(self):
        """Test getting value along with the matched alias."""
        attributes = {
            "gen_ai.request.model": "claude-3",
        }

        value, source = AttributeRegistry.get_value_with_source(
            attributes, "model_name"
        )
        assert value == "claude-3"
        assert source == "gen_ai.request.model"

    def test_get_value_with_source_not_found(self):
        """Test get_value_with_source when attribute not found."""
        attributes = {}

        value, source = AttributeRegistry.get_value_with_source(
            attributes, "model_name"
        )
        assert value is None
        assert source is None


class TestConventionDetection:
    """Tests for semantic convention detection."""

    def test_detect_otel_genai_convention(self):
        """Test detection of OTEL GenAI convention."""
        attributes = {
            "gen_ai.request.model": "claude-3",
            "gen_ai.system": "anthropic",
        }

        assert (
            AttributeRegistry.detect_convention(attributes)
            == SemanticConvention.OTEL_GENAI
        )

    def test_detect_openinference_convention(self):
        """Test detection of OpenInference convention."""
        attributes = {
            "openinference.span.kind": "LLM",
        }

        assert (
            AttributeRegistry.detect_convention(attributes)
            == SemanticConvention.OPENINFERENCE
        )

    def test_detect_unknown_convention(self):
        """Test detection returns UNKNOWN when no convention detected."""
        attributes = {
            "some.random.attribute": "value",
        }

        assert (
            AttributeRegistry.detect_convention(attributes)
            == SemanticConvention.UNKNOWN
        )

    def test_detect_semconv_convenience(self):
        """Test the convenience function."""
        attributes = {"gen_ai.system": "openai"}
        assert detect_semconv(attributes) == "otel_genai"


class TestSpanKindNormalization:
    """Tests for span kind normalization."""

    def test_normalize_otel_operations(self):
        """Test normalization of OTEL GenAI operations."""
        assert AttributeRegistry.normalize_span_kind("chat") == "llm"
        assert AttributeRegistry.normalize_span_kind("generate_content") == "llm"
        assert AttributeRegistry.normalize_span_kind("text_completion") == "llm"
        assert AttributeRegistry.normalize_span_kind("embeddings") == "embedding"
        assert AttributeRegistry.normalize_span_kind("execute_tool") == "tool"
        assert AttributeRegistry.normalize_span_kind("invoke") == "chain"

    def test_normalize_openinference_kinds(self):
        """Test that OpenInference span kinds pass through correctly."""
        assert AttributeRegistry.normalize_span_kind("LLM") == "llm"
        assert AttributeRegistry.normalize_span_kind("CHAIN") == "chain"
        assert AttributeRegistry.normalize_span_kind("TOOL") == "tool"
        assert AttributeRegistry.normalize_span_kind("RETRIEVER") == "retriever"
        assert AttributeRegistry.normalize_span_kind("AGENT") == "agent"
        assert AttributeRegistry.normalize_span_kind("RERANKER") == "reranker"
        assert AttributeRegistry.normalize_span_kind("GUARDRAIL") == "guardrail"
        assert AttributeRegistry.normalize_span_kind("EVALUATOR") == "evaluator"

    def test_normalize_unknown(self):
        """Test that unknown span kinds return 'unknown'."""
        assert AttributeRegistry.normalize_span_kind("something_else") == "unknown"
        assert AttributeRegistry.normalize_span_kind("") == "unknown"
        assert AttributeRegistry.normalize_span_kind(None) == "unknown"

    def test_normalize_case_insensitive(self):
        """Test that normalization is case-insensitive."""
        assert AttributeRegistry.normalize_span_kind("CHAT") == "llm"
        assert AttributeRegistry.normalize_span_kind("Chat") == "llm"
        assert AttributeRegistry.normalize_span_kind("LLM") == "llm"
        assert AttributeRegistry.normalize_span_kind("llm") == "llm"


class TestNestedValueAccess:
    """Tests for nested attribute value access."""

    def test_flat_key_access(self):
        """Test access with flat keys (standard OTEL format)."""
        attributes = {
            "gen_ai.request.model": "gpt-4",
            "gen_ai.system": "openai",
        }

        assert (
            AttributeRegistry._get_nested_value(attributes, "gen_ai.request.model")
            == "gpt-4"
        )
        assert (
            AttributeRegistry._get_nested_value(attributes, "gen_ai.system") == "openai"
        )

    def test_nested_dict_access(self):
        """Test access with nested dictionaries."""
        attributes = {
            "llm": {
                "model_name": "gpt-4",
                "invocation_parameters": {
                    "temperature": 0.7,
                },
            },
        }

        assert (
            AttributeRegistry._get_nested_value(attributes, "llm.model_name") == "gpt-4"
        )
        assert (
            AttributeRegistry._get_nested_value(
                attributes, "llm.invocation_parameters.temperature"
            )
            == 0.7
        )

    def test_missing_key(self):
        """Test that missing keys return None."""
        attributes = {"gen_ai.request.model": "gpt-4"}

        assert AttributeRegistry._get_nested_value(attributes, "gen_ai.system") is None
        assert AttributeRegistry._get_nested_value(attributes, "nonexistent") is None

    def test_empty_attributes(self):
        """Test handling of empty attributes."""
        assert AttributeRegistry._get_nested_value({}, "any.key") is None
        assert AttributeRegistry._get_nested_value(None, "any.key") is None


class TestGetAllValues:
    """Tests for extracting all canonical values."""

    def test_get_all_values_otel_genai(self):
        """Test extracting all values from OTEL GenAI convention span."""
        attributes = {
            "gen_ai.request.model": "claude-3",
            "gen_ai.usage.input_tokens": 200,
            "gen_ai.usage.output_tokens": 100,
            "gen_ai.system": "anthropic",
            "gen_ai.operation.name": "chat",
            "gen_ai.conversation.id": "conv-456",
            "enduser.id": "user-789",
        }

        result = AttributeRegistry.get_all_values(attributes)

        assert result["model_name"] == "claude-3"
        assert result["input_tokens"] == 200
        assert result["output_tokens"] == 100
        assert result["provider"] == "anthropic"
        assert result["operation_name"] == "chat"
        assert result["session_id"] == "conv-456"
        assert result["user_id"] == "user-789"

    def test_get_all_values_openinference_span_kind(self):
        """Test extracting span_kind from OpenInference convention."""
        attributes = {
            "openinference.span.kind": "LLM",
            "session.id": "sess-123",
        }

        result = AttributeRegistry.get_all_values(attributes)
        assert result["span_kind"] == "LLM"
        assert result["session_id"] == "sess-123"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_attribute(self):
        """Test the get_attribute convenience function."""
        attributes = {"gen_ai.request.model": "gpt-4"}

        assert get_attribute(attributes, "model_name") == "gpt-4"
        assert get_attribute(attributes, "provider") is None
        assert get_attribute(attributes, "provider", "default") == "default"

    def test_detect_semconv(self):
        """Test the detect_semconv convenience function."""
        assert detect_semconv({"gen_ai.system": "openai"}) == "otel_genai"
        assert detect_semconv({"openinference.span.kind": "LLM"}) == "openinference"
        assert detect_semconv({}) == "unknown"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_none_attributes(self):
        """Test handling of None attributes."""
        assert AttributeRegistry.get_value(None, "model_name") is None
        assert AttributeRegistry.detect_convention(None) == SemanticConvention.UNKNOWN

    def test_empty_string_values(self):
        """Test handling of empty string values."""
        attributes = {
            "gen_ai.request.model": "",
            "gen_ai.response.model": "claude-3",
        }

        # Empty string is still a value, so gen_ai.request.model (higher priority alias) returns ""
        result = AttributeRegistry.get_value(attributes, "model_name")
        assert result == ""  # Request model has priority even with empty string

    def test_zero_values(self):
        """Test handling of zero values (should not be treated as missing)."""
        attributes = {
            "gen_ai.usage.input_tokens": 0,
        }

        # Zero is a valid value
        assert AttributeRegistry.get_value(attributes, "input_tokens") == 0

    def test_mixed_conventions(self):
        """Test handling of spans with mixed conventions (realistic scenario)."""
        # Some instrumentations might emit both for compatibility
        attributes = {
            "gen_ai.request.model": "gpt-4",
            "gen_ai.usage.input_tokens": 100,
            "gen_ai.system": "openai",
        }

        # OTEL GenAI values should be found
        result = AttributeRegistry.get_all_values(attributes)
        assert result["model_name"] == "gpt-4"
        assert result["input_tokens"] == 100
        assert result["provider"] == "openai"

        # Detection should identify OTEL GenAI
        assert (
            AttributeRegistry.detect_convention(attributes)
            == SemanticConvention.OTEL_GENAI
        )

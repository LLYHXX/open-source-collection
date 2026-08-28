"""Unit tests for adapter registry and detection dispatch."""

import pytest

from tracer.utils.adapters.base import _ADAPTER_REGISTRY, _detect_adapter


@pytest.mark.unit
class TestAdapterRegistry:
    def test_all_five_adapters_registered(self):
        names = {name for _, name, _ in _ADAPTER_REGISTRY}
        assert names == {
            "langfuse",
            "openllmetry",
            "openinference",
            "otel_genai",
            "fi_native",
        }

    def test_priority_ordering(self):
        priorities = [(name, priority) for priority, name, _ in _ADAPTER_REGISTRY]
        names_in_order = [name for name, _ in priorities]
        assert names_in_order.index("langfuse") < names_in_order.index("openllmetry")
        assert names_in_order.index("openllmetry") < names_in_order.index(
            "openinference"
        )
        assert names_in_order.index("openinference") < names_in_order.index("fi_native")
        assert names_in_order.index("openllmetry") < names_in_order.index("otel_genai")
        assert names_in_order.index("otel_genai") < names_in_order.index(
            "openinference"
        )

    def test_langfuse_priority_is_5(self):
        for priority, name, _ in _ADAPTER_REGISTRY:
            if name == "langfuse":
                assert priority == 5

    def test_fi_native_priority_is_100(self):
        for priority, name, _ in _ADAPTER_REGISTRY:
            if name == "fi_native":
                assert priority == 100


@pytest.mark.unit
class TestDetectAdapter:
    def test_detect_langfuse(self):
        adapter = _detect_adapter({"langfuse.observation.type": "generation"})
        assert adapter is not None
        assert adapter.source_name == "langfuse"

    def test_detect_openinference(self):
        adapter = _detect_adapter({"openinference.span.kind": "LLM"})
        assert adapter is not None
        assert adapter.source_name == "openinference"

    def test_detect_otel_genai(self):
        adapter = _detect_adapter({"gen_ai.system": "openai"})
        assert adapter is not None
        assert adapter.source_name == "traceai"

    def test_detect_openllmetry_traceloop(self):
        adapter = _detect_adapter({"traceloop.span.kind": "workflow"})
        assert adapter is not None
        assert adapter.source_name == "openllmetry"

    def test_detect_fi_native(self):
        adapter = _detect_adapter({"fi.span.kind": "LLM"})
        assert adapter is not None
        assert adapter.source_name == "traceai"

    def test_detect_empty_attrs_returns_none(self):
        assert _detect_adapter({}) is None

    def test_detect_unknown_attrs_returns_none(self):
        assert _detect_adapter({"random.key": "val", "another": 42}) is None

    def test_langfuse_wins_over_fi_native(self):
        """When both langfuse and fi markers present, lower priority (langfuse=5) wins."""
        adapter = _detect_adapter(
            {
                "langfuse.observation.type": "generation",
                "fi.span.kind": "LLM",
            }
        )
        assert adapter.source_name == "langfuse"

    def test_otel_genai_wins_over_openinference(self):
        """When both gen_ai and openinference markers present, otel_genai (9) wins over openinference (10)."""
        adapter = _detect_adapter(
            {
                "gen_ai.system": "openai",
                "openinference.span.kind": "LLM",
            }
        )
        assert adapter.source_name == "traceai"

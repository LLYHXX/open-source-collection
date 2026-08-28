"""
OpenInference adapter — handles Arize Phoenix and other OpenInference-based traces.

OpenInference convention shares almost all attribute names with fi.* convention.
The only remapping needed is: openinference.span.kind → fi.span.kind
All llm.*, input.*, output.* attributes are already identical.

After normalization, openinference.* keys are stripped from attributes.
"""

from typing import Any

from tracer.utils.adapters.base import BaseTraceAdapter, register_adapter, strip_keys


class OpenInferenceAdapter(BaseTraceAdapter):
    @property
    def source_name(self) -> str:
        return "openinference"

    def detect(self, attributes: dict[str, Any]) -> bool:
        return "openinference.span.kind" in attributes

    def normalize(self, attributes: dict[str, Any]) -> dict[str, Any]:
        # Map openinference.span.kind → fi.span.kind (only if not already set)
        if "fi.span.kind" not in attributes:
            attributes["fi.span.kind"] = attributes["openinference.span.kind"]

        strip_keys(attributes, "openinference.")

        attributes["gen_ai.trace.source"] = self.source_name
        return attributes


register_adapter("openinference", OpenInferenceAdapter(), priority=10)

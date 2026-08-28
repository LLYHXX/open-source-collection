"""
FI Native adapter — passthrough for spans already using fi.* convention.

Registered at lowest priority so foreign-format adapters get checked first.
"""

from typing import Any

from tracer.utils.adapters.base import BaseTraceAdapter, register_adapter


class FiNativeAdapter(BaseTraceAdapter):
    @property
    def source_name(self) -> str:
        return "traceai"

    def detect(self, attributes: dict[str, Any]) -> bool:
        return "fi.span.kind" in attributes

    def normalize(self, attributes: dict[str, Any]) -> dict[str, Any]:
        attributes["gen_ai.trace.source"] = self.source_name
        return attributes


register_adapter("fi_native", FiNativeAdapter(), priority=100)

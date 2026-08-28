"""
Trace format adapters — normalize foreign OTLP attribute schemas to fi.* convention.

Usage:
    from tracer.utils.adapters import normalize_span_attributes
    normalize_span_attributes(otel_data_list)
"""

# Import adapter modules to trigger self-registration.
# Add new adapters here as they are created.
import tracer.utils.adapters.fi_native  # noqa: F401
import tracer.utils.adapters.langfuse  # noqa: F401
import tracer.utils.adapters.openinference  # noqa: F401
import tracer.utils.adapters.openllmetry  # noqa: F401
import tracer.utils.adapters.otel_genai  # noqa: F401
from tracer.utils.adapters.base import normalize_span_attributes  # noqa: F401

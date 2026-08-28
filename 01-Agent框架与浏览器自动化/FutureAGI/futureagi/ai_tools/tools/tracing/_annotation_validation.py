"""Annotation value validation for MCP tracing tools.

Delegates to the shared validation utility in tracer/utils/annotation_validation.py.
"""

from tracer.utils.annotation_validation import (
    validate_annotation_value as _validate_core,
)


def validate_annotation_value(
    label,
    value: str | None = None,
    value_float: float | None = None,
    value_bool: bool | None = None,
    value_str_list: list[str] | None = None,
) -> str | None:
    """Validate annotation value against label type and settings.

    Thin wrapper that extracts label.type and label.settings, then
    delegates to the shared utility.

    Args:
        label: AnnotationsLabels instance with .type and .settings
        value: String value (for TEXT)
        value_float: Float value (for NUMERIC/STAR)
        value_bool: Boolean value (for THUMBS_UP_DOWN)
        value_str_list: List of strings (for CATEGORICAL)

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_core(
        label_type=label.type,
        label_settings=label.settings,
        value=value,
        value_float=value_float,
        value_bool=value_bool,
        value_str_list=value_str_list,
    )

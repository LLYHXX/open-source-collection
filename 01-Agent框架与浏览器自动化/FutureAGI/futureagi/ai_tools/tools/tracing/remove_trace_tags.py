from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class RemoveTraceTagsInput(PydanticBaseModel):
    trace_id: UUID = Field(description="The UUID of the trace to remove tags from")
    tags: list[str] = Field(description="List of tag strings to remove")


@register_tool
class RemoveTraceTagsTool(BaseTool):
    name = "remove_trace_tags"
    description = (
        "Removes specified tags from a trace. Tags that are not present "
        "on the trace are silently ignored."
    )
    category = "tracing"
    input_model = RemoveTraceTagsInput

    def execute(self, params: RemoveTraceTagsInput, context: ToolContext) -> ToolResult:

        from tracer.models.trace import Trace

        try:
            trace = Trace.objects.get(
                id=params.trace_id, project__organization=context.organization
            )
        except Trace.DoesNotExist:
            return ToolResult.not_found("Trace", str(params.trace_id))

        if not params.tags:
            return ToolResult.error(
                "Provide at least one tag to remove.",
                error_code="VALIDATION_ERROR",
            )

        existing_tags = set(trace.tags or [])
        to_remove = set(params.tags)
        removed = existing_tags & to_remove
        not_found = to_remove - existing_tags

        # Update tags
        trace.tags = sorted(existing_tags - to_remove)
        trace.save()

        info = key_value_block(
            [
                ("Trace ID", f"`{params.trace_id}`"),
                (
                    "Removed Tags",
                    (
                        ", ".join(f"`{t}`" for t in sorted(removed))
                        if removed
                        else "—(none found)"
                    ),
                ),
                (
                    "Not Found",
                    (
                        ", ".join(f"`{t}`" for t in sorted(not_found))
                        if not_found
                        else "—"
                    ),
                ),
                ("Remaining Tags", str(len(trace.tags))),
            ]
        )

        content = section("Tags Removed", info)

        return ToolResult(
            content=content,
            data={
                "trace_id": str(params.trace_id),
                "removed": sorted(removed),
                "not_found": sorted(not_found),
                "remaining_tags": trace.tags,
            },
        )

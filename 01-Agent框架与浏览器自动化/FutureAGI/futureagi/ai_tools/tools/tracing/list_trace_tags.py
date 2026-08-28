from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class ListTraceTagsInput(PydanticBaseModel):
    trace_id: UUID = Field(description="The UUID of the trace to list tags for")


@register_tool
class ListTraceTagsTool(BaseTool):
    name = "list_trace_tags"
    description = (
        "Lists all tags on a specific trace. Tags are string labels "
        "stored as a JSON array on the trace."
    )
    category = "tracing"
    input_model = ListTraceTagsInput

    def execute(self, params: ListTraceTagsInput, context: ToolContext) -> ToolResult:

        from tracer.models.trace import Trace

        try:
            trace = Trace.objects.get(
                id=params.trace_id, project__organization=context.organization
            )
        except Trace.DoesNotExist:
            return ToolResult.not_found("Trace", str(params.trace_id))

        tags = trace.tags or []

        if not tags:
            content = section(
                "Trace Tags",
                f"No tags found on trace `{params.trace_id}`.",
            )
        else:
            tag_list = "\n".join(f"- `{tag}`" for tag in tags)
            info = key_value_block(
                [
                    ("Trace ID", f"`{params.trace_id}`"),
                    ("Trace Name", trace.name or "—"),
                    ("Tag Count", str(len(tags))),
                ]
            )
            content = section(f"Trace Tags ({len(tags)})", f"{info}\n\n{tag_list}")

        return ToolResult(
            content=content,
            data={
                "trace_id": str(params.trace_id),
                "tags": tags,
                "count": len(tags),
            },
        )

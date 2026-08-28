from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteTraceAnnotationInput(PydanticBaseModel):
    annotation_id: UUID = Field(description="The UUID of the annotation to delete")


@register_tool
class DeleteTraceAnnotationTool(BaseTool):
    name = "delete_trace_annotation"
    description = (
        "Deletes a trace annotation by ID. This is a soft delete "
        "(marks as deleted, does not permanently remove)."
    )
    category = "tracing"
    input_model = DeleteTraceAnnotationInput

    def execute(
        self, params: DeleteTraceAnnotationInput, context: ToolContext
    ) -> ToolResult:

        from tracer.models.trace_annotation import TraceAnnotation

        try:
            annotation = TraceAnnotation.objects.select_related("annotation_label").get(
                id=params.annotation_id,
                trace__project__organization=context.organization,
            )
        except TraceAnnotation.DoesNotExist:
            return ToolResult.not_found("Trace Annotation", str(params.annotation_id))

        label_name = (
            annotation.annotation_label.name if annotation.annotation_label else "—"
        )
        trace_id = str(annotation.trace_id) if annotation.trace_id else "—"
        ann_id = str(annotation.id)

        # Also soft-delete the corresponding Score record to keep data consistent
        if annotation.annotation_label_id and annotation.observation_span_id:
            from model_hub.models.score import Score

            Score.no_workspace_objects.filter(
                observation_span_id=annotation.observation_span_id,
                label_id=annotation.annotation_label_id,
                annotator_id=annotation.user_id,
                deleted=False,
            ).update(deleted=True)

        # Soft delete
        annotation.delete()

        info = key_value_block(
            [
                ("Annotation ID", f"`{ann_id}`"),
                ("Label", label_name),
                ("Trace", f"`{trace_id}`"),
                ("Status", "Deleted"),
            ]
        )

        content = section("Annotation Deleted", info)

        return ToolResult(
            content=content,
            data={
                "annotation_id": ann_id,
                "label": label_name,
                "trace_id": trace_id,
                "deleted": True,
            },
        )

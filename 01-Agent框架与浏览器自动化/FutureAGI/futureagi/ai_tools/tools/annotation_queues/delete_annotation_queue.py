from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class DeleteAnnotationQueueInput(PydanticBaseModel):
    queue_id: UUID = Field(description="The UUID of the annotation queue to delete")


@register_tool
class DeleteAnnotationQueueTool(BaseTool):
    name = "delete_annotation_queue"
    description = (
        "Deletes an annotation queue (soft delete). "
        "All items and annotations within the queue are preserved but become inaccessible."
    )
    category = "annotations"
    input_model = DeleteAnnotationQueueInput

    def execute(
        self, params: DeleteAnnotationQueueInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.annotation_queues import AnnotationQueue

        try:
            queue = AnnotationQueue.objects.get(
                id=params.queue_id,
                organization=context.organization,
                deleted=False,
            )
        except AnnotationQueue.DoesNotExist:
            return ToolResult.not_found("Annotation Queue", str(params.queue_id))

        queue_name = queue.name
        queue.delete()

        info = key_value_block(
            [
                ("Queue ID", f"`{params.queue_id}`"),
                ("Name", queue_name),
                ("Status", "Deleted"),
            ]
        )

        content = section("Annotation Queue Deleted", info)

        return ToolResult(
            content=content,
            data={
                "queue_id": str(params.queue_id),
                "name": queue_name,
                "deleted": True,
            },
        )

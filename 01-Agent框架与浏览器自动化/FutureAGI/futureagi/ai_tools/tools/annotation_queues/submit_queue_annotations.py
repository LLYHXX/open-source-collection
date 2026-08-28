from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class QueueAnnotationValue(PydanticBaseModel):
    label_id: UUID = Field(description="The annotation label UUID")
    value: Any = Field(
        description=(
            "Annotation value. Format depends on label type: "
            "TEXT -> {text: 'string'}, NUMERIC -> {value: float}, "
            "STAR -> {rating: float}, CATEGORICAL -> {selected: ['option1']}, "
            "THUMBS_UP_DOWN -> {value: 'up' or 'down'}"
        )
    )


class SubmitQueueAnnotationsInput(PydanticBaseModel):
    queue_id: UUID = Field(description="The UUID of the annotation queue")
    item_id: UUID = Field(description="The UUID of the queue item to annotate")
    annotations: list[QueueAnnotationValue] = Field(
        description="List of annotation values to submit", min_length=1
    )
    notes: Optional[str] = Field(
        default=None, description="Optional notes for this annotation"
    )


@register_tool
class SubmitQueueAnnotationsTool(BaseTool):
    name = "submit_queue_annotations"
    description = (
        "Submits annotation values for a queue item. Provide the queue ID, item ID, "
        "and annotation values for each label. Automatically completes the item "
        "when the required number of annotations is reached."
    )
    category = "annotations"
    input_model = SubmitQueueAnnotationsInput

    def execute(
        self, params: SubmitQueueAnnotationsInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.annotation_queues import (
            AnnotationQueue,
            ItemAnnotation,
            QueueItem,
        )
        from model_hub.models.develop_annotations import AnnotationsLabels

        try:
            queue = AnnotationQueue.objects.get(
                id=params.queue_id,
                organization=context.organization,
                deleted=False,
            )
        except AnnotationQueue.DoesNotExist:
            return ToolResult.not_found("Annotation Queue", str(params.queue_id))

        try:
            item = QueueItem.objects.get(
                id=params.item_id,
                queue=queue,
                deleted=False,
            )
        except QueueItem.DoesNotExist:
            return ToolResult.not_found("Queue Item", str(params.item_id))

        if item.status == "completed":
            return ToolResult.error(
                "This item is already completed.", error_code="VALIDATION_ERROR"
            )

        # Pre-fetch labels
        label_ids = {a.label_id for a in params.annotations}
        labels_by_id = {
            l.id: l
            for l in AnnotationsLabels.objects.filter(
                id__in=label_ids, organization=context.organization
            )
        }

        created = 0
        updated = 0
        errors = []

        for ann in params.annotations:
            label = labels_by_id.get(ann.label_id)
            if not label:
                errors.append(f"Label `{ann.label_id}` not found")
                continue

            # Upsert — update if same (item, user, label) exists
            existing = ItemAnnotation.objects.filter(
                queue_item=item,
                annotator=context.user,
                label=label,
                deleted=False,
            ).first()

            if existing:
                existing.value = ann.value
                if params.notes:
                    existing.notes = params.notes
                existing.save()
                updated += 1
            else:
                ItemAnnotation.objects.create(
                    queue_item=item,
                    annotator=context.user,
                    label=label,
                    value=ann.value,
                    score_source="human",
                    notes=params.notes or "",
                    organization=context.organization,
                    workspace=context.workspace,
                )
                created += 1

        # Update item status
        if item.status == "pending":
            item.status = "in_progress"
            item.save(update_fields=["status", "updated_at"])

        # Auto-complete check: count distinct annotators who submitted
        annotator_count = (
            ItemAnnotation.objects.filter(queue_item=item, deleted=False)
            .values("annotator")
            .distinct()
            .count()
        )
        if annotator_count >= queue.annotations_required:
            item.status = "completed"
            item.save(update_fields=["status", "updated_at"])

        info = key_value_block(
            [
                ("Queue", queue.name),
                ("Item", f"`{item.id}`"),
                ("Created", str(created)),
                ("Updated", str(updated)),
                ("Item Status", item.status),
                ("Errors", str(len(errors)) if errors else "None"),
            ]
        )

        content = section("Queue Annotations Submitted", info)
        if errors:
            content += "\n\n### Errors\n\n" + "\n".join(f"- {e}" for e in errors)

        return ToolResult(
            content=content,
            data={
                "queue_id": str(queue.id),
                "item_id": str(item.id),
                "created": created,
                "updated": updated,
                "item_status": item.status,
                "errors": errors,
            },
            is_error=created == 0 and updated == 0 and len(errors) > 0,
        )

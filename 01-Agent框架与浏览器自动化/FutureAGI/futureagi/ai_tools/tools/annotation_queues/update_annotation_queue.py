from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class UpdateAnnotationQueueInput(PydanticBaseModel):
    queue_id: UUID = Field(description="The UUID of the annotation queue to update")
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    instructions: Optional[str] = Field(default=None)
    status: Optional[str] = Field(
        default=None,
        description="New status: draft, active, paused, completed",
    )
    annotations_required: Optional[int] = Field(default=None, ge=1, le=10)
    add_label_ids: Optional[list[UUID]] = Field(
        default=None, description="Label UUIDs to add to the queue"
    )
    remove_label_ids: Optional[list[UUID]] = Field(
        default=None, description="Label UUIDs to remove from the queue"
    )
    add_annotator_ids: Optional[list[UUID]] = Field(
        default=None, description="User UUIDs to add as annotators"
    )
    remove_annotator_ids: Optional[list[UUID]] = Field(
        default=None, description="User UUIDs to remove from annotators"
    )


@register_tool
class UpdateAnnotationQueueTool(BaseTool):
    name = "update_annotation_queue"
    description = (
        "Updates an annotation queue's settings, status, labels, or annotators. "
        "Use status transitions: draft->active, active->paused/completed, "
        "paused->active/completed, completed->active."
    )
    category = "annotations"
    input_model = UpdateAnnotationQueueInput

    def execute(
        self, params: UpdateAnnotationQueueInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.annotation_queues import (
            VALID_STATUS_TRANSITIONS,
            AnnotationQueue,
            AnnotationQueueAnnotator,
            AnnotationQueueLabel,
        )

        try:
            queue = AnnotationQueue.objects.get(
                id=params.queue_id,
                organization=context.organization,
                deleted=False,
            )
        except AnnotationQueue.DoesNotExist:
            return ToolResult.not_found("Annotation Queue", str(params.queue_id))

        changes = []

        # Status transition validation
        if params.status:
            valid_transitions = VALID_STATUS_TRANSITIONS.get(queue.status, set())
            if params.status not in valid_transitions:
                return ToolResult.error(
                    f"Cannot transition from '{queue.status}' to '{params.status}'. "
                    f"Valid transitions: {', '.join(sorted(valid_transitions)) if valid_transitions else 'none'}",
                    error_code="VALIDATION_ERROR",
                )
            queue.status = params.status
            changes.append(f"Status -> {params.status}")

        if params.name is not None:
            queue.name = params.name
            changes.append(f"Name -> '{params.name}'")
        if params.description is not None:
            queue.description = params.description
            changes.append("Description updated")
        if params.instructions is not None:
            queue.instructions = params.instructions
            changes.append("Instructions updated")
        if params.annotations_required is not None:
            queue.annotations_required = params.annotations_required
            changes.append(f"Annotations required -> {params.annotations_required}")

        if changes:
            queue.save()

        # Add labels
        if params.add_label_ids:
            from model_hub.models.develop_annotations import AnnotationsLabels

            labels = AnnotationsLabels.objects.filter(
                id__in=params.add_label_ids, organization=context.organization
            )
            existing_label_ids = set(
                AnnotationQueueLabel.objects.filter(
                    queue=queue, deleted=False
                ).values_list("label_id", flat=True)
            )
            max_order = (
                AnnotationQueueLabel.objects.filter(queue=queue, deleted=False)
                .order_by("-order")
                .values_list("order", flat=True)
                .first()
                or 0
            )
            added = 0
            for label in labels:
                if label.id not in existing_label_ids:
                    max_order += 1
                    AnnotationQueueLabel.objects.create(
                        queue=queue, label=label, order=max_order
                    )
                    added += 1
            if added:
                changes.append(f"Added {added} label(s)")

        # Remove labels
        if params.remove_label_ids:
            removed = AnnotationQueueLabel.objects.filter(
                queue=queue, label_id__in=params.remove_label_ids, deleted=False
            ).update(deleted=True)
            if removed:
                changes.append(f"Removed {removed} label(s)")

        # Add annotators
        if params.add_annotator_ids:
            from accounts.models.user import User

            users = User.objects.filter(
                id__in=params.add_annotator_ids,
                organization=context.organization,
            )
            existing_user_ids = set(
                AnnotationQueueAnnotator.objects.filter(
                    queue=queue, deleted=False
                ).values_list("user_id", flat=True)
            )
            added = 0
            for user in users:
                if user.id not in existing_user_ids:
                    AnnotationQueueAnnotator.objects.create(queue=queue, user=user)
                    added += 1
            if added:
                changes.append(f"Added {added} annotator(s)")

        # Remove annotators
        if params.remove_annotator_ids:
            removed = AnnotationQueueAnnotator.objects.filter(
                queue=queue, user_id__in=params.remove_annotator_ids, deleted=False
            ).update(deleted=True)
            if removed:
                changes.append(f"Removed {removed} annotator(s)")

        if not changes:
            return ToolResult.error(
                "No changes provided.", error_code="VALIDATION_ERROR"
            )

        info = key_value_block(
            [
                ("Queue ID", f"`{queue.id}`"),
                ("Name", queue.name),
                ("Changes", "; ".join(changes)),
            ]
        )

        content = section("Annotation Queue Updated", info)

        return ToolResult(
            content=content,
            data={
                "queue_id": str(queue.id),
                "changes": changes,
            },
        )

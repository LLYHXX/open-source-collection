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

VALID_STRATEGIES = {"manual", "round_robin", "load_balanced"}


class CreateAnnotationQueueInput(PydanticBaseModel):
    name: str = Field(
        description="Name for the annotation queue", min_length=1, max_length=255
    )
    description: Optional[str] = Field(
        default=None, description="Description of the queue"
    )
    instructions: Optional[str] = Field(
        default=None, description="Instructions for annotators"
    )
    assignment_strategy: str = Field(
        default="manual",
        description="Assignment strategy: manual, round_robin, or load_balanced",
    )
    annotations_required: int = Field(
        default=1, ge=1, le=10, description="Number of annotations required per item"
    )
    requires_review: bool = Field(
        default=False, description="Whether annotations require review"
    )
    project_id: Optional[UUID] = Field(
        default=None, description="Project UUID to scope the queue to"
    )
    dataset_id: Optional[UUID] = Field(
        default=None, description="Dataset UUID to scope the queue to"
    )
    agent_definition_id: Optional[UUID] = Field(
        default=None,
        description="Agent definition UUID to scope the queue to (for simulation annotation)",
    )
    label_ids: Optional[list[UUID]] = Field(
        default=None,
        description="List of annotation label UUIDs to attach to this queue",
    )
    annotator_ids: Optional[list[UUID]] = Field(
        default=None,
        description="List of user UUIDs to assign as annotators",
    )


@register_tool
class CreateAnnotationQueueTool(BaseTool):
    name = "create_annotation_queue"
    description = (
        "Creates an annotation queue for organizing annotation workflows. "
        "Queues can be scoped to a project, dataset, or agent definition (simulation). "
        "Items (traces, spans, dataset rows, call executions) can be added to the queue "
        "and assigned to annotators."
    )
    category = "annotations"
    input_model = CreateAnnotationQueueInput

    def execute(
        self, params: CreateAnnotationQueueInput, context: ToolContext
    ) -> ToolResult:
        from model_hub.models.annotation_queues import (
            AnnotationQueue,
            AnnotationQueueAnnotator,
            AnnotationQueueLabel,
        )
        from model_hub.models.develop_annotations import AnnotationsLabels

        if params.assignment_strategy not in VALID_STRATEGIES:
            return ToolResult.error(
                f"Invalid assignment_strategy '{params.assignment_strategy}'. "
                f"Valid: {', '.join(sorted(VALID_STRATEGIES))}",
                error_code="VALIDATION_ERROR",
            )

        # Validate project
        project = None
        if params.project_id:
            from tracer.models.project import Project

            try:
                project = Project.objects.get(
                    id=params.project_id, organization=context.organization
                )
            except Project.DoesNotExist:
                return ToolResult.not_found("Project", str(params.project_id))

        # Validate dataset
        dataset = None
        if params.dataset_id:
            from model_hub.models.develop_dataset import Dataset

            try:
                dataset = Dataset.objects.get(id=params.dataset_id)
            except Dataset.DoesNotExist:
                return ToolResult.not_found("Dataset", str(params.dataset_id))

        # Validate agent definition
        agent_definition = None
        if params.agent_definition_id:
            from simulate.models import AgentDefinition

            try:
                agent_definition = AgentDefinition.objects.get(
                    id=params.agent_definition_id,
                    organization=context.organization,
                )
            except AgentDefinition.DoesNotExist:
                return ToolResult.not_found(
                    "Agent Definition", str(params.agent_definition_id)
                )

        queue = AnnotationQueue(
            name=params.name,
            description=params.description or "",
            instructions=params.instructions or "",
            assignment_strategy=params.assignment_strategy,
            annotations_required=params.annotations_required,
            requires_review=params.requires_review,
            organization=context.organization,
            workspace=context.workspace,
            project=project,
            dataset=dataset,
            agent_definition=agent_definition,
            created_by=context.user,
        )
        queue.save()

        # Attach labels
        labels_added = 0
        if params.label_ids:
            labels = AnnotationsLabels.objects.filter(
                id__in=params.label_ids, organization=context.organization
            )
            for idx, label in enumerate(labels):
                AnnotationQueueLabel.objects.create(queue=queue, label=label, order=idx)
                labels_added += 1

        # Attach annotators
        annotators_added = 0
        if params.annotator_ids:
            from accounts.models.user import User

            users = User.objects.filter(
                id__in=params.annotator_ids,
                organization=context.organization,
            )
            for user in users:
                AnnotationQueueAnnotator.objects.create(queue=queue, user=user)
                annotators_added += 1

        scope = "—"
        if project:
            scope = f"Project: {project.name}"
        elif dataset:
            scope = f"Dataset: {dataset.name}"
        elif agent_definition:
            scope = f"Agent: {agent_definition.name}"

        info = key_value_block(
            [
                ("ID", f"`{queue.id}`"),
                ("Name", queue.name),
                ("Strategy", queue.assignment_strategy),
                ("Annotations Required", str(queue.annotations_required)),
                ("Scope", scope),
                ("Labels", str(labels_added)),
                ("Annotators", str(annotators_added)),
                ("Status", "draft"),
            ]
        )

        content = section("Annotation Queue Created", info)

        return ToolResult(
            content=content,
            data={
                "queue_id": str(queue.id),
                "name": queue.name,
                "status": queue.status,
                "labels_added": labels_added,
                "annotators_added": annotators_added,
            },
        )

from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class CreateAnnotationInput(PydanticBaseModel):
    name: str = Field(
        description="Name for the annotation task", min_length=1, max_length=255
    )
    dataset_id: UUID = Field(description="The UUID of the dataset to annotate")
    label_ids: list[UUID] = Field(
        description="List of annotation label UUIDs to use in this task",
        min_length=1,
    )
    responses: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of annotators required per row",
    )


@register_tool
class CreateAnnotationTool(BaseTool):
    name = "create_annotation"
    description = (
        "Creates a new annotation task for a dataset. "
        "Requires a dataset and at least one annotation label. "
        "Users can be assigned later via the dashboard."
    )
    category = "annotations"
    input_model = CreateAnnotationInput

    def execute(
        self, params: CreateAnnotationInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.develop_annotations import Annotations, AnnotationsLabels
        from model_hub.models.develop_dataset import Dataset
        from model_hub.services.annotation_service import process_annotation_columns

        # Validate dataset
        try:
            dataset = Dataset.objects.get(id=params.dataset_id)
        except Dataset.DoesNotExist:
            return ToolResult.not_found("Dataset", str(params.dataset_id))

        # Validate labels (scoped to organization)
        labels = list(
            AnnotationsLabels.objects.filter(
                id__in=params.label_ids,
                organization=context.organization,
            )
        )
        found_ids = set(str(l.id) for l in labels)
        missing = [str(lid) for lid in params.label_ids if str(lid) not in found_ids]
        if missing:
            return ToolResult.error(
                f"Label(s) not found: {', '.join(missing)}. "
                "Use list_annotation_labels to see available labels.",
                error_code="NOT_FOUND",
            )

        # Create annotation task
        annotation = Annotations(
            name=params.name,
            dataset=dataset,
            responses=params.responses,
            organization=context.organization,
            workspace=context.workspace,
        )
        annotation.save()

        # Add labels
        annotation.labels.set(labels)

        # Create columns via shared service (matches view's process_new_annotaion)
        columns_created = process_annotation_columns(annotation, labels)

        info = key_value_block(
            [
                ("ID", f"`{annotation.id}`"),
                ("Name", annotation.name),
                ("Dataset", dataset.name),
                ("Labels", str(len(labels))),
                ("Responses Required", str(params.responses)),
                ("Columns Created", str(columns_created)),
            ]
        )

        content = section("Annotation Task Created", info)
        content += "\n\n_Assign users via the dashboard to start annotation._"

        return ToolResult(
            content=content,
            data={
                "annotation_id": str(annotation.id),
                "name": annotation.name,
                "dataset_id": str(dataset.id),
                "label_count": len(labels),
                "columns_created": columns_created,
            },
        )

from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_number,
    key_value_block,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


class AnnotationSummaryInput(PydanticBaseModel):
    dataset_id: UUID = Field(
        description="The UUID of the dataset to get annotation summary for"
    )


@register_tool
class AnnotationSummaryTool(BaseTool):
    name = "annotation_summary"
    description = (
        "Returns annotation summary statistics for a dataset including "
        "per-label metrics (agreement scores, distributions), "
        "per-annotator stats (completion count, average time), "
        "and dataset-level coverage and progress."
    )
    category = "annotations"
    input_model = AnnotationSummaryInput

    def execute(
        self, params: AnnotationSummaryInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.develop_annotations import Annotations, AnnotationsLabels
        from model_hub.models.develop_dataset import Cell, Column, Dataset, Row

        try:
            dataset = Dataset.objects.get(
                id=params.dataset_id, deleted=False, organization=context.organization
            )
        except Dataset.DoesNotExist:
            return ToolResult.not_found("Dataset", str(params.dataset_id))

        total_rows = Row.objects.filter(dataset=dataset, deleted=False).count()

        # Get all annotations for this dataset
        annotations = Annotations.objects.filter(
            dataset=dataset,
        ).prefetch_related("labels", "assigned_users")

        if not annotations.exists():
            return ToolResult(
                content=section(
                    f"Annotation Summary: {dataset.name}",
                    "_No annotation tasks found for this dataset._",
                ),
                data={"annotations": [], "total_rows": total_rows},
            )

        # Build summary per annotation task
        ann_rows = []
        ann_data = []
        for ann in annotations:
            # Count completed rows
            ann_cols = Column.objects.filter(
                dataset=dataset,
                source="annotation_label",
                source_id__startswith=str(ann.id),
                deleted=False,
            )

            completed_cells = 0
            total_cells = 0
            for col in ann_cols:
                cells = Cell.objects.filter(column=col, dataset=dataset, deleted=False)
                total_cells += cells.count()
                completed_cells += (
                    cells.exclude(value="").exclude(value__isnull=True).count()
                )

            pct = (completed_cells / total_cells * 100) if total_cells > 0 else 0

            users = ann.assigned_users.all()
            label_names = [l.name for l in ann.labels.all()]

            ann_rows.append(
                [
                    ann.name,
                    str(users.count()),
                    ", ".join(label_names[:3])
                    + ("..." if len(label_names) > 3 else ""),
                    str(ann.responses),
                    f"{completed_cells}/{total_cells} ({pct:.0f}%)",
                    str(ann.lowest_unfinished_row or 0),
                ]
            )

            ann_data.append(
                {
                    "id": str(ann.id),
                    "name": ann.name,
                    "users": users.count(),
                    "labels": label_names,
                    "responses": ann.responses,
                    "completed_cells": completed_cells,
                    "total_cells": total_cells,
                    "completion_pct": round(pct, 1),
                }
            )

        table = markdown_table(
            [
                "Task",
                "Annotators",
                "Labels",
                "Responses/Row",
                "Progress",
                "Lowest Unfinished",
            ],
            ann_rows,
        )

        # Per-annotator stats
        annotator_rows = []
        all_users = set()
        for ann in annotations:
            for u in ann.assigned_users.all():
                all_users.add(u)

        for user in all_users:
            # Count cells annotated by this user
            user_count = 0
            for ann in annotations:
                ann_cols = Column.objects.filter(
                    dataset=dataset,
                    source="annotation_label",
                    source_id__startswith=str(ann.id),
                    deleted=False,
                )
                for col in ann_cols:
                    user_count += (
                        Cell.objects.filter(
                            column=col,
                            dataset=dataset,
                            deleted=False,
                            feedback_info__annotation__user_id=str(user.id),
                        )
                        .exclude(value="")
                        .count()
                    )

            if user_count > 0:
                annotator_rows.append(
                    [
                        user.email or user.name or str(user.id),
                        str(user_count),
                    ]
                )

        content = section(
            f"Annotation Summary: {dataset.name} ({total_rows} rows)",
            table,
        )

        if annotator_rows:
            annotator_table = markdown_table(
                ["Annotator", "Annotations"],
                annotator_rows,
            )
            content += f"\n\n### Per-Annotator Stats\n\n{annotator_table}"

        return ToolResult(
            content=content,
            data={"annotations": ann_data, "total_rows": total_rows},
        )

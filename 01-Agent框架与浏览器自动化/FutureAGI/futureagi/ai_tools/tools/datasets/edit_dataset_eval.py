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


class EditDatasetEvalInput(PydanticBaseModel):
    dataset_id: UUID = Field(description="The UUID of the dataset")
    eval_id: UUID = Field(description="The UUID of the UserEvalMetric to edit")
    mapping: Optional[dict[str, str]] = Field(
        default=None,
        description="Updated column mapping (template key → column ID/name)",
    )
    config: Optional[dict] = Field(
        default=None,
        description="Updated runtime config overrides",
    )
    model: Optional[str] = Field(
        default=None,
        description="Updated LLM model for evaluation",
    )
    run: bool = Field(
        default=False,
        description="If true, re-queue the eval to run after editing",
    )
    kb_id: Optional[str] = Field(
        default=None,
        description="Updated Knowledge Base ID",
    )
    error_localizer: Optional[bool] = Field(
        default=None,
        description="Updated error localizer",
    )


@register_tool
class EditDatasetEvalTool(BaseTool):
    name = "edit_dataset_eval"
    description = (
        "Modifies the configuration of an existing dataset evaluation, "
        "including column mapping, config parameters, and model. "
        "Optionally re-runs the eval after editing."
    )
    category = "datasets"
    input_model = EditDatasetEvalInput

    def execute(self, params: EditDatasetEvalInput, context: ToolContext) -> ToolResult:

        from model_hub.models.choices import DataTypeChoices
        from model_hub.models.develop_dataset import Dataset
        from model_hub.models.evals_metric import UserEvalMetric
        from model_hub.utils.function_eval_params import normalize_eval_runtime_config

        try:
            dataset = Dataset.objects.get(
                id=params.dataset_id, deleted=False, organization=context.organization
            )
        except Dataset.DoesNotExist:
            return ToolResult.not_found("Dataset", str(params.dataset_id))

        try:
            user_eval = UserEvalMetric.objects.get(
                id=params.eval_id, dataset=dataset, deleted=False
            )
        except UserEvalMetric.DoesNotExist:
            return ToolResult.not_found("DatasetEval", str(params.eval_id))

        # Check if column has been deleted (matches backend EditAndRunUserEvalView)
        if user_eval.column_deleted:
            return ToolResult.error(
                f"Column for eval '{user_eval.name}' has been deleted. "
                "Cannot edit this eval.",
                error_code="VALIDATION_ERROR",
            )

        changes = []
        update_fields = ["updated_at"]

        current_config = user_eval.config or {}
        new_config = params.config or {}

        if params.mapping is not None:
            current_config["mapping"] = params.mapping
            changes.append("Updated column mapping")

        if params.config is not None:
            new_config = normalize_eval_runtime_config(
                user_eval.template.config, params.config
            )
            current_config["config"] = new_config
            changes.append("Updated runtime config")

        if params.mapping is not None or params.config is not None:
            user_eval.config = current_config
            update_fields.append("config")

        if params.model:
            user_eval.model = params.model
            update_fields.append("model")
            changes.append(f"Model → `{params.model}`")

        if params.kb_id:
            # Check if kb_id is a valid UUID
            from uuid import UUID

            try:
                UUID(str(params.kb_id))
            except (ValueError, TypeError):
                return ToolResult.bad_param("kb_id", "Must be a valid UUID")
            user_eval.kb_id = params.kb_id
            update_fields.append("kb_id")
            changes.append(f"Knowledge Base → `{params.kb_id}`")

        if params.error_localizer:
            user_eval.error_localizer = params.error_localizer
            update_fields.append("error_localizer")
            changes.append("Updated error localizer")

        if new_config.get("reason_column"):
            from model_hub.models.choices import SourceChoices
            from model_hub.models.develop_dataset import Column

            column = Column.objects.filter(
                source_id=str(user_eval.id), deleted=False
            ).first()
            if column:
                reason_column, created = Column.objects.get_or_create(
                    name=f"{user_eval.name}-reason",
                    data_type=DataTypeChoices.TEXT.value,
                    source=SourceChoices.EVALUATION_REASON.value,
                    dataset=user_eval.dataset,
                    source_id=f"{column.id}-sourceid-{user_eval.id}",
                )
                if created:
                    column_order = user_eval.dataset.column_order or []
                    column_order.append(str(reason_column.id))
                    user_eval.dataset.column_order = column_order
                    user_eval.dataset.save()

        if params.run:
            from model_hub.models.choices import CellStatus, SourceChoices, StatusType
            from model_hub.models.develop_dataset import Cell, Column

            user_eval.status = StatusType.NOT_STARTED.value
            update_fields.append("status")

            # Find the result column and set replace_column_id
            corresponding_column = Column.objects.filter(
                source=SourceChoices.EVALUATION.value,
                source_id=str(user_eval.id),
                deleted=False,
            ).first()

            if corresponding_column:
                # Set result column cells to RUNNING
                Cell.objects.filter(
                    column__source_id=str(user_eval.id), deleted=False
                ).update(status=CellStatus.RUNNING.value)

                # Set reason column cells to RUNNING
                Cell.objects.filter(
                    column__source_id=f"{corresponding_column.id}-sourceid-{user_eval.id}",
                    deleted=False,
                ).update(status=CellStatus.RUNNING.value)

            changes.append("Queued for re-run")

        user_eval.save(update_fields=update_fields)

        info = key_value_block(
            [
                ("Eval", user_eval.name),
                ("Eval ID", f"`{user_eval.id}`"),
                (
                    "Changes",
                    "\n".join(f"- {c}" for c in changes) if changes else "No changes",
                ),
                ("Status", user_eval.status),
            ]
        )

        content = section("Dataset Eval Updated", info)
        if params.run:
            content += "\n\n_Evaluation re-queued for processing._"

        return ToolResult(
            content=content,
            data={
                "eval_id": str(user_eval.id),
                "changes": changes,
                "status": user_eval.status,
            },
        )

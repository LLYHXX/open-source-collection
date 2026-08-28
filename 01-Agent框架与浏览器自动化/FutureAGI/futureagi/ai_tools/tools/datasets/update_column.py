from typing import Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from ai_tools.tools.datasets.add_columns import DataTypeLiteral


class UpdateColumnInput(PydanticBaseModel):
    dataset_id: str = Field(
        description="Dataset name or UUID. Examples: 'my-qa-dataset' or '550e8400-e29b-41d4-a716-446655440000'"
    )
    column_id: str = Field(description="The UUID of the column to update")
    new_name: Optional[str] = Field(
        default=None,
        description="New name for the column",
        min_length=1,
        max_length=255,
    )
    new_data_type: Optional[DataTypeLiteral] = Field(
        default=None,
        description=(
            "New data type: text, integer, float, boolean, json, "
            "array, image, images, datetime, audio, document"
        ),
    )


@register_tool
class UpdateColumnTool(BaseTool):
    name = "update_column"
    description = (
        "Updates a column's name or data type in a dataset. "
        "Provide at least one of new_name or new_data_type."
    )
    category = "datasets"
    input_model = UpdateColumnInput

    def execute(self, params: UpdateColumnInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_dataset
        from model_hub.models.choices import SourceChoices
        from model_hub.models.develop_dataset import Column

        if not params.new_name and not params.new_data_type:
            return ToolResult.error(
                "Provide at least one of new_name or new_data_type.",
                error_code="VALIDATION_ERROR",
            )

        dataset, error = resolve_dataset(
            params.dataset_id, context.organization, context.workspace
        )
        if error:
            return ToolResult.error(error, error_code="NOT_FOUND")

        try:
            column = Column.objects.get(
                id=params.column_id, dataset=dataset, deleted=False
            )
        except Column.DoesNotExist:
            return ToolResult.not_found("Column", str(params.column_id))

        changes = []

        # --- Rename ---
        if params.new_name and params.new_name != column.name:
            exists = (
                Column.objects.filter(
                    dataset=dataset, name=params.new_name, deleted=False
                )
                .exclude(id=column.id)
                .exists()
            )
            if exists:
                return ToolResult.error(
                    f"Column '{params.new_name}' already exists in this dataset.",
                    error_code="VALIDATION_ERROR",
                )
            old_name = column.name
            column.name = params.new_name
            column.save(update_fields=["name", "updated_at"])
            changes.append(f"Name: `{old_name}` → `{params.new_name}`")

            # Update derived variable references for RUN_PROMPT columns
            if column.source == SourceChoices.RUN_PROMPT.value and column.source_id:
                self._update_derived_variables(column, old_name, params.new_name)

        # --- Type change ---
        if params.new_data_type:
            # Reject type change on derived columns (evaluation, run_prompt, etc.)
            if column.source_id:
                return ToolResult.error(
                    "Cannot change data type of a derived column "
                    f"(source: {column.source}). Only user-created columns "
                    "can have their type changed.",
                    error_code="VALIDATION_ERROR",
                )

            if params.new_data_type != column.data_type:
                import json

                from model_hub.models.choices import CellStatus, StatusType
                from model_hub.models.develop_dataset import Cell

                old_type = column.data_type

                # Set column to RUNNING while async conversion happens
                column.data_type = params.new_data_type
                column.status = StatusType.RUNNING.value
                column.save(update_fields=["data_type", "status", "updated_at"])

                # Mark cells as RUNNING
                Cell.objects.filter(
                    column=column, deleted=False, row__deleted=False
                ).update(
                    status=CellStatus.RUNNING.value,
                    value_infos=json.dumps({}),
                )

                # Trigger async conversion via Celery
                try:
                    from model_hub.views.develop_dataset import perform_conversion

                    perform_conversion.apply_async(
                        args=(str(column.id), params.new_data_type)
                    )
                    changes.append(
                        f"Type: `{old_type}` → `{params.new_data_type}` (conversion in progress)"
                    )
                except Exception:
                    # Fallback: just update the type without conversion
                    column.status = StatusType.COMPLETED.value
                    column.save(update_fields=["status"])
                    changes.append(f"Type: `{old_type}` → `{params.new_data_type}`")

        if not changes:
            return ToolResult(
                content=section("Column Update", "No changes were needed."),
                data={"column_id": str(column.id)},
            )

        info = key_value_block(
            [
                ("Dataset", dataset.name),
                ("Column ID", f"`{column.id}`"),
                ("Current Name", column.name),
                ("Current Type", column.data_type),
                ("Changes", "\n".join(changes)),
            ]
        )

        return ToolResult(
            content=section("Column Updated", info),
            data={
                "column_id": str(column.id),
                "name": column.name,
                "data_type": column.data_type,
            },
        )

    @staticmethod
    def _update_derived_variables(column, old_name: str, new_name: str):
        """Update derived variable references when a RUN_PROMPT column is renamed."""
        import structlog

        logger = structlog.get_logger(__name__)

        try:
            from model_hub.models.run_prompt import PromptVersion, RunPrompter
            from model_hub.services.derived_variable_service import (
                rename_derived_variables_for_column,
                rename_derived_variables_in_run_prompter,
            )

            run_prompter = RunPrompter.objects.filter(
                id=column.source_id, deleted=False
            ).first()

            if run_prompter:
                if rename_derived_variables_in_run_prompter(
                    run_prompter, old_name, new_name
                ):
                    run_prompter.save(update_fields=["run_prompt_config"])

                prompt_template = run_prompter.prompt
                if prompt_template:
                    prompt_versions = PromptVersion.objects.filter(
                        prompt=prompt_template, deleted=False
                    )
                    for version in prompt_versions:
                        if rename_derived_variables_for_column(
                            version, old_name, new_name
                        ):
                            version.save(update_fields=["metadata"])

        except Exception as e:
            logger.warning(
                "failed_to_update_derived_variables",
                old_name=old_name,
                new_name=new_name,
                error=str(e),
            )

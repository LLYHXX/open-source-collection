from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class ApplyEvalGroupToDatasetInput(PydanticBaseModel):
    eval_group_id: UUID = Field(description="The UUID of the eval group to apply")
    dataset_id: UUID = Field(
        description="The UUID of the dataset to apply the eval group to"
    )
    mapping: Optional[dict] = Field(
        default=None,
        description=(
            "Field mapping from eval template keys to dataset column IDs. "
            'Example: {"response": "<column_uuid>", "query": "<column_uuid>"}'
        ),
    )
    filters: Optional[dict] = Field(
        default=None,
        description=(
            "Additional filters: kb_id (knowledge base UUID), model (string), "
            "error_localizer (bool)"
        ),
    )
    params: Optional[dict] = Field(
        default=None,
        description="Additional parameters for the evaluation",
    )


@register_tool
class ApplyEvalGroupToDatasetTool(BaseTool):
    name = "apply_eval_group_to_dataset"
    description = (
        "Applies an evaluation group to a dataset. Creates UserEvalMetric "
        "entries for each eval template in the group, linking them to the dataset. "
        "Use list_eval_groups to find groups and list_datasets for dataset IDs."
    )
    category = "evaluations"
    input_model = ApplyEvalGroupToDatasetInput

    def execute(
        self, params: ApplyEvalGroupToDatasetInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.develop_dataset import Dataset
        from model_hub.models.eval_groups import EvalGroup
        from model_hub.services.eval_group import apply_eval_group

        # Validate eval group
        try:
            eval_group = EvalGroup.objects.get(
                id=params.eval_group_id,
                organization=context.organization,
                deleted=False,
            )
        except EvalGroup.DoesNotExist:
            return ToolResult.not_found("Eval Group", str(params.eval_group_id))

        # Validate dataset
        try:
            dataset = Dataset.objects.get(
                id=params.dataset_id, organization=context.organization
            )
        except Dataset.DoesNotExist:
            return ToolResult.not_found("Dataset", str(params.dataset_id))

        # Build filters dict (apply_eval_group expects dataset_id in filters)
        filters = params.filters or {}
        filters["dataset_id"] = str(params.dataset_id)

        mapping = params.mapping or {}

        try:
            apply_eval_group(
                eval_group=eval_group,
                filters=filters,
                mapping=mapping,
                page_id="DATASET",
                user=context.user,
                workspace=context.workspace,
                deselected_evals=None,
                params=params.params,
            )
        except Exception as e:
            from ai_tools.error_codes import code_from_exception

            return ToolResult.error(
                f"Failed to apply eval group: {str(e)}",
                error_code=code_from_exception(e),
            )

        # Count templates in the group
        template_count = eval_group.eval_templates.count()

        info = key_value_block(
            [
                ("Eval Group", f"{eval_group.name} (`{str(eval_group.id)}`)"),
                ("Dataset", f"{dataset.name} (`{str(dataset.id)}`)"),
                ("Templates Applied", str(template_count)),
            ]
        )

        content = section("Eval Group Applied to Dataset", info)
        content += (
            "\n\n_Evaluation metrics have been created for each template in the group. "
            "Run evaluations on the dataset to see results._"
        )

        return ToolResult(
            content=content,
            data={
                "eval_group_id": str(eval_group.id),
                "eval_group_name": eval_group.name,
                "dataset_id": str(dataset.id),
                "dataset_name": dataset.name,
                "template_count": template_count,
            },
        )

from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    dashboard_link,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class CreateExperimentInput(PydanticBaseModel):
    name: str = Field(
        description="Name for the experiment", min_length=1, max_length=255
    )
    dataset_id: UUID = Field(description="The UUID of the dataset to use")
    column_id: UUID = Field(
        description="The UUID of the input column in the dataset (the column whose values are sent as prompts)"
    )
    prompt_config: list[dict] = Field(
        description=(
            "List of prompt variant configurations. Each must have: "
            "'name' (str), 'messages' (list of {role, content}), "
            "'model' (list of model names like ['gpt-4o']), "
            "'configuration' ({temperature, max_tokens, ...}). "
            "Minimum 2 variants for comparison."
        ),
        min_length=2,
        max_length=10,
    )
    user_eval_template_ids: Optional[list[UUID]] = Field(
        default=None,
        description="Optional list of UserEvalMetric UUIDs to evaluate experiment results",
    )


@register_tool
class CreateExperimentTool(BaseTool):
    name = "create_experiment"
    description = (
        "Creates a new experiment (A/B test) comparing multiple prompt/model variants "
        "on a dataset. Requires a dataset, an input column, and at least 2 prompt configs. "
        "Each prompt config needs: name, messages, model list, and configuration. "
        "A Temporal workflow is started automatically to run the experiment."
    )
    category = "experiments"
    input_model = CreateExperimentInput

    def execute(
        self, params: CreateExperimentInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.services.experiment_service import (
            ServiceError,
            create_experiment,
        )

        result = create_experiment(
            name=params.name,
            dataset_id=str(params.dataset_id),
            column_id=str(params.column_id),
            prompt_config=params.prompt_config,
            user=context.user,
            user_eval_template_ids=(
                [str(uid) for uid in params.user_eval_template_ids]
                if params.user_eval_template_ids
                else None
            ),
        )

        if isinstance(result, ServiceError):
            if result.code == "NOT_FOUND":
                return ToolResult.error(result.message, error_code="NOT_FOUND")
            return ToolResult.error(result.message, error_code=result.code)

        info = key_value_block(
            [
                ("Experiment ID", f"`{result['id']}`"),
                ("Name", result["name"]),
                ("Dataset", result["dataset_name"]),
                ("Input Column", result["column_name"]),
                ("Variants", str(result["variant_count"])),
                ("Status", result["status"]),
                (
                    "Workflow Started",
                    (
                        "Yes"
                        if result["workflow_started"]
                        else "No (will be picked up by periodic task)"
                    ),
                ),
                (
                    "Link",
                    dashboard_link(
                        "experiment", result["id"], label="View in Dashboard"
                    ),
                ),
            ]
        )

        content = section("Experiment Created", info)

        return ToolResult(
            content=content,
            data=result,
        )

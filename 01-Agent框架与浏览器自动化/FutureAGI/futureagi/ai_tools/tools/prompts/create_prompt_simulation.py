from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class CreatePromptSimulationInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    name: str = Field(
        description="Name of the simulation run",
        min_length=1,
        max_length=255,
    )
    prompt_version_id: str = Field(
        description="Prompt version ID (UUID) or version string (e.g. 'v1')",
    )
    scenario_ids: List[UUID] = Field(
        description="List of scenario UUIDs to include (at least one required)",
        min_length=1,
    )
    description: Optional[str] = Field(default=None, description="Optional description")
    evaluations_config: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "List of evaluation config dicts. Each dict should contain "
            "'template_id' (UUID of EvalTemplate) and optionally 'name', "
            "'config', 'mapping', 'filters', 'error_localizer', 'model', 'eval_group'."
        ),
    )
    enable_tool_evaluation: bool = Field(
        default=False,
        description="Enable automatic tool evaluation for this simulation run",
    )

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or whitespace only.")
        return stripped


@register_tool
class CreatePromptSimulationTool(BaseTool):
    name = "create_prompt_simulation"
    description = (
        "Creates a new prompt simulation run for a prompt template. "
        "Links the template with a specific version and scenarios for testing."
    )
    category = "prompts"
    input_model = CreatePromptSimulationInput

    def execute(
        self, params: CreatePromptSimulationInput, context: ToolContext
    ) -> ToolResult:

        from django.core.exceptions import ValidationError
        from django.db import transaction

        from model_hub.models.evals_metric import EvalTemplate
        from model_hub.models.run_prompt import PromptTemplate
        from simulate.models import RunTest, SimulateEvalConfig
        from simulate.utils.prompt_simulation_validators import (
            resolve_prompt_version,
            validate_scenarios_in_org,
        )

        # Validate template exists and belongs to org
        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        # Resolve prompt version (UUID or version string like 'v1')
        try:
            prompt_version = resolve_prompt_version(
                params.prompt_version_id, params.template_id
            )
        except ValidationError as e:
            return ToolResult.validation_error(e.message)

        # Validate all scenarios exist in org
        try:
            scenarios = validate_scenarios_in_org(
                params.scenario_ids, context.organization
            )
        except ValidationError as e:
            return ToolResult.validation_error(e.message)

        with transaction.atomic():
            workspace = template.workspace

            run_test = RunTest.objects.create(
                name=params.name,
                description=params.description or "",
                source_type="prompt",
                prompt_template=template,
                prompt_version=prompt_version,
                agent_definition=None,
                agent_version=None,
                simulator_agent=None,
                organization=context.organization,
                workspace=workspace,
                enable_tool_evaluation=params.enable_tool_evaluation,
            )

            run_test.scenarios.set(scenarios)

            # Handle evaluations config
            eval_count = 0
            skipped_evals = []
            if params.evaluations_config:
                for eval_config_data in params.evaluations_config:
                    template_id = eval_config_data.get("template_id")
                    if not template_id:
                        continue
                    try:
                        eval_template = EvalTemplate.no_workspace_objects.get(
                            id=template_id
                        )
                        SimulateEvalConfig.objects.create(
                            eval_template=eval_template,
                            name=eval_config_data.get("name", f"Eval-{template_id}"),
                            config=eval_config_data.get("config", {}),
                            mapping=eval_config_data.get("mapping", {}),
                            run_test=run_test,
                            filters=eval_config_data.get("filters", {}),
                            error_localizer=eval_config_data.get(
                                "error_localizer", False
                            ),
                            model=eval_config_data.get("model", None),
                            eval_group_id=eval_config_data.get("eval_group", None),
                        )
                        eval_count += 1
                    except EvalTemplate.DoesNotExist:
                        skipped_evals.append(str(template_id))

        info = key_value_block(
            [
                ("ID", f"`{run_test.id}`"),
                ("Name", run_test.name),
                ("Template", template.name),
                ("Version", prompt_version.template_version),
                ("Scenarios", str(scenarios.count())),
                ("Eval Configs", str(eval_count)),
                ("Created", format_datetime(run_test.created_at)),
            ]
        )

        content = section("Prompt Simulation Created", info)

        if skipped_evals:
            content += (
                f"\n\n_Skipped {len(skipped_evals)} eval template(s) "
                f"not found: {', '.join(skipped_evals)}_"
            )

        return ToolResult(
            content=content,
            data={
                "id": str(run_test.id),
                "name": run_test.name,
                "template_id": str(template.id),
                "version": prompt_version.template_version,
                "scenario_count": scenarios.count(),
                "eval_config_count": eval_count,
                "skipped_evals": skipped_evals,
            },
        )

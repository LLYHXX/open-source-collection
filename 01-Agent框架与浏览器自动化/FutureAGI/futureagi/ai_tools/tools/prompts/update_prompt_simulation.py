from typing import List, Optional
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


class UpdatePromptSimulationInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    simulation_id: UUID = Field(
        description="The UUID of the simulation run (RunTest) to update"
    )
    name: Optional[str] = Field(
        default=None,
        description="New name (1-255 characters)",
        max_length=255,
    )
    description: Optional[str] = Field(default=None, description="New description")
    prompt_version_id: Optional[str] = Field(
        default=None,
        description="New prompt version ID (UUID) or version string (e.g. 'v1')",
    )
    scenario_ids: Optional[List[UUID]] = Field(
        default=None,
        description="New list of scenario UUIDs (replaces existing, at least one required)",
        min_length=1,
    )
    enable_tool_evaluation: Optional[bool] = Field(
        default=None,
        description="Enable or disable automatic tool evaluation",
    )

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Name cannot be empty or whitespace only.")
            return stripped
        return v


@register_tool
class UpdatePromptSimulationTool(BaseTool):
    name = "update_prompt_simulation"
    description = (
        "Updates an existing prompt simulation run. "
        "Can change name, description, prompt version, scenarios, or tool evaluation setting."
    )
    category = "prompts"
    input_model = UpdatePromptSimulationInput

    def execute(
        self, params: UpdatePromptSimulationInput, context: ToolContext
    ) -> ToolResult:

        from django.core.exceptions import ValidationError
        from django.db import transaction

        from model_hub.models.run_prompt import PromptTemplate
        from simulate.models import RunTest
        from simulate.utils.prompt_simulation_validators import (
            resolve_prompt_version,
            validate_scenarios_in_org,
        )

        # Validate template
        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        # Validate simulation
        try:
            run_test = RunTest.objects.get(
                id=params.simulation_id,
                prompt_template=template,
                source_type="prompt",
                organization=context.organization,
                deleted=False,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("Simulation", str(params.simulation_id))

        updated_fields = []

        with transaction.atomic():
            if params.name is not None:
                run_test.name = params.name
                updated_fields.append("name")

            if params.description is not None:
                run_test.description = params.description
                updated_fields.append("description")

            if params.prompt_version_id is not None:
                try:
                    prompt_version = resolve_prompt_version(
                        params.prompt_version_id, params.template_id
                    )
                except ValidationError as e:
                    return ToolResult.validation_error(e.message)
                run_test.prompt_version = prompt_version
                updated_fields.append("prompt_version")

            if params.scenario_ids is not None:
                try:
                    scenarios = validate_scenarios_in_org(
                        params.scenario_ids, context.organization
                    )
                except ValidationError as e:
                    return ToolResult.validation_error(e.message)
                run_test.scenarios.set(scenarios)
                updated_fields.append("scenarios")

            if params.enable_tool_evaluation is not None:
                run_test.enable_tool_evaluation = params.enable_tool_evaluation
                updated_fields.append("enable_tool_evaluation")

            if not updated_fields:
                return ToolResult.error(
                    "No fields provided to update.",
                    error_code="VALIDATION_ERROR",
                )

            run_test.save()

        info = key_value_block(
            [
                ("ID", f"`{run_test.id}`"),
                ("Name", run_test.name),
                ("Updated Fields", ", ".join(updated_fields)),
                ("Updated At", format_datetime(run_test.updated_at)),
            ]
        )

        content = section("Prompt Simulation Updated", info)

        return ToolResult(
            content=content,
            data={
                "id": str(run_test.id),
                "name": run_test.name,
                "updated_fields": updated_fields,
            },
        )

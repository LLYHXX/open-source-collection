from typing import Optional
from uuid import UUID

import structlog
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool
from tracer.models.custom_eval_config import ModelChoices

logger = structlog.get_logger(__name__)

VALID_EVAL_MODELS = {choice.value for choice in ModelChoices}


class CreateSimulateEvalConfigInput(PydanticBaseModel):
    run_test_id: UUID = Field(
        description="The UUID of the RunTest (test suite) to add the eval config to"
    )
    eval_template_id: UUID = Field(
        description=(
            "The UUID of the eval template to use. "
            "Use list_eval_templates to find available templates."
        )
    )
    name: Optional[str] = Field(
        default=None,
        description=(
            "Name for this eval config. If not provided, auto-generates "
            "from the eval template name."
        ),
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use for evaluation. If not provided, uses the default.",
    )

    @field_validator("model")
    @classmethod
    def check_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_EVAL_MODELS:
            raise ValueError(
                f"Invalid model '{v}'. Must be one of: {sorted(VALID_EVAL_MODELS)}"
            )
        return v

    mapping: Optional[dict] = Field(
        default=None,
        description=(
            "Mapping of eval template input keys to call execution fields. "
            "Valid voice fields: transcript, voice_recording, assistant_recording, "
            "customer_recording, stereo_recording, agent_prompt. "
            "Valid text fields: transcript, agent_prompt, user_chat_transcript, "
            "assistant_chat_transcript. "
            "If not provided, auto-maps based on the eval template's required keys "
            "and the agent type. "
            "Use list_eval_mapping_options to see all valid field values."
        ),
    )
    config: Optional[dict] = Field(
        default=None,
        description="Runtime config overrides for the eval template",
    )
    error_localizer: bool = Field(
        default=False,
        description="Whether to enable error localizer for this eval",
    )


@register_tool
class CreateSimulateEvalConfigTool(BaseTool):
    name = "create_simulate_eval_config"
    description = (
        "Creates an evaluation config on a simulation run test (test suite). "
        "This configures an eval template to run on call executions in the test. "
        "If mapping is not provided, it auto-maps template keys to the closest "
        "matching call execution fields based on the agent type (voice/text). "
        "If mapping is provided, it validates that all values are valid fields "
        "for the agent type."
    )
    category = "simulation"
    input_model = CreateSimulateEvalConfigInput

    def execute(
        self, params: CreateSimulateEvalConfigInput, context: ToolContext
    ) -> ToolResult:

        from django.db.models import Q

        from ai_tools.tools.simulation.list_eval_mapping_options import (
            auto_assign_mapping,
            get_valid_fields,
        )
        from model_hub.models.evals_metric import EvalTemplate
        from model_hub.utils.function_eval_params import (
            normalize_eval_runtime_config,
        )
        from simulate.models.eval_config import SimulateEvalConfig
        from simulate.models.run_test import RunTest

        # Validate run test
        try:
            run_test = RunTest.objects.select_related("agent_definition").get(
                id=params.run_test_id,
                organization=context.organization,
            )
        except RunTest.DoesNotExist:
            return ToolResult.not_found("RunTest", str(params.run_test_id))

        # Validate eval template
        try:
            template = EvalTemplate.no_workspace_objects.get(
                Q(organization=context.organization) | Q(organization__isnull=True),
                id=params.eval_template_id,
            )
        except EvalTemplate.DoesNotExist:
            return ToolResult.not_found("EvalTemplate", str(params.eval_template_id))

        # Determine agent type
        agent_type = "voice"
        if run_test.agent_definition:
            agent_type = run_test.agent_definition.agent_type or "voice"

        # Get required keys from the eval template config
        template_config = template.config or {}
        required_keys = (
            template_config.get("required_keys", [])
            if isinstance(template_config, dict)
            else []
        )

        if params.mapping:
            # Validate provided mapping values against valid fields
            valid_fields = get_valid_fields(agent_type)
            invalid_values = [
                v for v in params.mapping.values() if v and v not in valid_fields
            ]
            # Skip dataset column IDs (UUIDs) from validation
            if invalid_values:
                invalid_values = [
                    v for v in invalid_values if len(v) < 36 or "-" not in v
                ]
            if invalid_values:
                return ToolResult.error(
                    f"Invalid mapping values: {', '.join(invalid_values)}. "
                    f"Valid options for {agent_type} agent: "
                    f"{', '.join(sorted(get_valid_fields(agent_type)))}. "
                    f"Use `list_eval_mapping_options` to see all valid field values.",
                    error_code="VALIDATION_ERROR",
                )
            final_mapping = params.mapping
        else:
            # Auto-assign mapping based on required keys and agent type
            if required_keys:
                final_mapping = auto_assign_mapping(required_keys, agent_type)
                logger.info(
                    "auto_mapped_simulate_eval_config",
                    run_test_id=str(params.run_test_id),
                    template_id=str(params.eval_template_id),
                    agent_type=agent_type,
                    mapping=final_mapping,
                )
            else:
                final_mapping = {}

        # Build config
        eval_config = normalize_eval_runtime_config(
            template.config, params.config or {}
        )

        # Auto-generate name if not provided
        config_name = params.name or template.name

        # Create the SimulateEvalConfig
        simulate_eval_config = SimulateEvalConfig.objects.create(
            eval_template=template,
            name=config_name,
            config=eval_config,
            mapping=final_mapping,
            run_test=run_test,
            error_localizer=params.error_localizer,
            model=params.model,
        )

        info_pairs = [
            ("Config ID", f"`{simulate_eval_config.id}`"),
            ("Name", config_name),
            ("Template", template.name),
            ("Run Test", run_test.name),
            ("Agent Type", agent_type),
            ("Model", simulate_eval_config.model or "default"),
            ("Error Localizer", str(simulate_eval_config.error_localizer)),
            ("Created", format_datetime(simulate_eval_config.created_at)),
        ]

        if final_mapping:
            mapping_lines = ", ".join(
                f"`{k}` → `{v}`" for k, v in final_mapping.items()
            )
            info_pairs.append(("Mapping", mapping_lines))
            if not params.mapping:
                info_pairs.append(
                    ("Mapping Source", "auto-mapped from agent type fields")
                )

        info = key_value_block(info_pairs)

        # Count total eval configs on this run test
        total_evals = SimulateEvalConfig.objects.filter(run_test=run_test).count()

        content = section("Simulate Eval Config Created", info)
        content += f"\n\n_Total eval configs on this test suite: {total_evals}_"

        return ToolResult(
            content=content,
            data={
                "id": str(simulate_eval_config.id),
                "name": config_name,
                "eval_template_id": str(template.id),
                "run_test_id": str(run_test.id),
                "mapping": final_mapping,
                "total_evals": total_evals,
            },
        )

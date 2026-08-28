from typing import Optional
from uuid import UUID

import structlog
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, markdown_table, section
from ai_tools.registry import register_tool

logger = structlog.get_logger(__name__)

# Keys whose eval input should come from the model's output (assistant response)
_OUTPUT_KEYS = {"output", "response", "generated_audio"}
# Keys whose eval input should come from the model's input (user prompt)
_INPUT_KEYS = {
    "input",
    "query",
    "conversation",
    "audio",
    "input_audio",
    "image",
    "input_image",
}
# All valid mapping targets in prompt workbench context
_VALID_MAPPING_TARGETS = {"input_prompt", "output_prompt"}


def _auto_generate_mapping(
    required_keys: list[str], variable_names: list[str] | None = None
) -> dict[str, str]:
    """Auto-generate mapping from eval required_keys to prompt workbench fields.

    Mapping rules (matching frontend EvaluationActions columnOptions):
      - output-type keys  → "output_prompt" (assistant response)
      - input-type keys   → "input_prompt"  (user content)
      - keys matching a template variable name → variable name
    """
    mapping = {}
    variable_set = set(variable_names) if variable_names else set()
    for key in required_keys:
        if key in _OUTPUT_KEYS:
            mapping[key] = "output_prompt"
        elif key in _INPUT_KEYS:
            mapping[key] = "input_prompt"
        elif key in variable_set:
            mapping[key] = key
    return mapping


def _validate_mapping(
    mapping: dict[str, str],
    required_keys: list[str],
    variable_names: list[str] | None = None,
) -> list[str]:
    """Validate a user-provided mapping. Returns list of error messages (empty = valid)."""
    errors = []
    variable_set = set(variable_names) if variable_names else set()
    valid_targets = _VALID_MAPPING_TARGETS | variable_set

    # Check all required keys are mapped
    missing_keys = [k for k in required_keys if k not in mapping]
    if missing_keys:
        errors.append(
            f"Missing mapping for required key(s): {', '.join(missing_keys)}. "
            f"Each must map to one of: 'input_prompt', 'output_prompt'"
            + (
                f", or a template variable ({', '.join(sorted(variable_set))})"
                if variable_set
                else ""
            )
            + "."
        )

    # Check all mapping values are valid targets
    for key, value in mapping.items():
        if value not in valid_targets:
            errors.append(
                f"Invalid mapping target '{value}' for key '{key}'. "
                f"Must be one of: {', '.join(sorted(valid_targets))}."
            )

    return errors


class SetEvalConfigForPromptInput(PydanticBaseModel):
    template_id: UUID = Field(description="The UUID of the prompt template")
    eval_template_ids: list[UUID] = Field(
        description="List of eval template IDs to link to this prompt template",
        min_length=1,
    )
    mapping: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Optional mapping of eval required keys to prompt fields. "
            "Valid targets: 'input_prompt' (user content), 'output_prompt' (model response), "
            "or a template variable name. Example: {'output': 'output_prompt'}. "
            "If omitted, mapping is auto-generated from the eval template's required_keys."
        ),
    )
    config: Optional[dict] = Field(
        default=None,
        description=(
            "Optional runtime configuration for the eval. "
            "Example: {'params': {'model': 'gpt-4o'}}"
        ),
    )
    kb_id: Optional[UUID] = Field(
        default=None,
        description="Optional knowledge base file ID for the eval config.",
    )
    error_localizer: bool = Field(
        default=False, description="Enable error localizer for eval configs"
    )
    is_run: bool = Field(
        default=False,
        description=(
            "If true, immediately run the evals on the specified versions "
            "(or latest version if none specified)."
        ),
    )
    version_to_run: Optional[list[str]] = Field(
        default=None,
        description=(
            "List of version strings to run evals on (e.g. ['v1', 'v2']). "
            "Only used when is_run=true. Defaults to latest version."
        ),
    )


@register_tool
class SetEvalConfigForPromptTool(BaseTool):
    name = "set_eval_config_for_prompt"
    description = (
        "Links evaluation templates to a prompt template by creating "
        "PromptEvalConfig entries. This allows evaluations to run automatically "
        "when the prompt is executed. Use list_eval_templates to find eval template IDs."
    )
    category = "prompts"
    input_model = SetEvalConfigForPromptInput

    def execute(
        self, params: SetEvalConfigForPromptInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.evals_metric import EvalTemplate
        from model_hub.models.run_prompt import (
            PromptEvalConfig,
            PromptTemplate,
            PromptVersion,
        )
        from model_hub.utils.function_eval_params import normalize_eval_runtime_config
        from tfc.utils.error_codes import get_error_message

        # Validate prompt template
        try:
            template = PromptTemplate.objects.get(
                id=params.template_id,
                organization=context.organization,
                deleted=False,
            )
        except PromptTemplate.DoesNotExist:
            return ToolResult.not_found("Prompt Template", str(params.template_id))

        # Validate eval templates exist
        eval_templates = EvalTemplate.no_workspace_objects.filter(
            id__in=params.eval_template_ids, deleted=False
        )
        found_ids = set(str(t.id) for t in eval_templates)
        missing = [
            str(tid) for tid in params.eval_template_ids if str(tid) not in found_ids
        ]

        if missing:
            return ToolResult.error(
                f"Eval template(s) not found: {', '.join(missing)}. "
                "Use list_eval_templates to see available templates.",
                error_code="NOT_FOUND",
            )

        # Get template variable names for mapping validation/auto-generation
        latest_version = (
            PromptVersion.objects.filter(original_template=template, deleted=False)
            .order_by("-created_at")
            .first()
        )
        variable_names = (
            list((latest_version.variable_names or {}).keys()) if latest_version else []
        )

        # Create PromptEvalConfig entries — one per eval template
        # (matching update_evaluation_configs view behavior)
        created = []
        created_configs = []
        skipped = []
        kb = None

        # Resolve knowledge base if provided
        if params.kb_id:
            try:
                from model_hub.models.knowledge_base import KnowledgeBaseFile

                kb = KnowledgeBaseFile.objects.get(id=params.kb_id)
            except Exception:
                pass

        for eval_template in eval_templates:
            # Duplicate check by name — same validation as the view
            eval_name = eval_template.name
            if PromptEvalConfig.objects.filter(
                name=eval_name, prompt_template=template, deleted=False
            ).exists():
                skipped.append(eval_name)
                continue

            required_keys = eval_template.config.get("required_keys", [])

            # Resolve mapping: use user-provided or auto-generate
            if params.mapping is not None:
                # Validate user-provided mapping against this eval's required keys
                validation_errors = _validate_mapping(
                    params.mapping, required_keys, variable_names
                )
                if validation_errors:
                    return ToolResult.error(
                        f"Invalid mapping for eval '{eval_template.name}': "
                        + " ".join(validation_errors),
                        error_code="VALIDATION_ERROR",
                    )
                mapping = params.mapping
            else:
                # Auto-generate mapping from required_keys
                mapping = _auto_generate_mapping(required_keys, variable_names)

            # Build runtime config — same as update_evaluation_configs view
            user_config = params.config or {}
            user_params = user_config.get("params", {})
            normalized_config = normalize_eval_runtime_config(
                eval_template.config,
                {
                    **user_config,
                    "params": user_params,
                },
            )

            prompt_eval = PromptEvalConfig.objects.create(
                name=eval_name,
                prompt_template=template,
                eval_template=eval_template,
                mapping=mapping,
                config=normalized_config,
                user=context.user,
                kb=kb,
                error_localizer=params.error_localizer,
            )
            created.append(eval_name)
            created_configs.append(prompt_eval)

        if not created and skipped:
            return ToolResult(
                content=section(
                    "Eval Configs Already Linked",
                    f"All {len(skipped)} eval template(s) are already linked to "
                    f"**{template.name}**.\n\n"
                    f"Skipped: {', '.join(skipped)}",
                ),
                data={
                    "template_id": str(template.id),
                    "created": [],
                    "skipped": skipped,
                },
            )

        # If is_run, trigger eval execution for newly created configs
        # (same logic as update_evaluation_configs view)
        eval_run_status = None
        if params.is_run and created_configs:
            try:
                from django.db import transaction

                from model_hub.models.evals_metric import StatusType
                from model_hub.views.prompt_template import (
                    _PROMPT_TEMPLATE_EXECUTOR,
                    PromptTemplateViewSet,
                    _safe_background_task,
                    submit_with_retry,
                    track_running_eval_count,
                )

                version_to_run = params.version_to_run
                if not version_to_run:
                    if latest_version:
                        version_to_run = [latest_version.template_version]

                if version_to_run:
                    # Check if all versions exist — same as view
                    existing_versions = PromptVersion.objects.filter(
                        original_template=template,
                        template_version__in=version_to_run,
                    ).values_list("template_version", flat=True)

                    missing_versions = set(version_to_run) - set(existing_versions)
                    if missing_versions:
                        eval_run_status = (
                            f"Configs created but some versions do not exist: "
                            f"{', '.join(missing_versions)}"
                        )
                    else:
                        executions = PromptVersion.objects.filter(
                            original_template=template,
                            original_template__organization=context.organization,
                            template_version__in=version_to_run,
                            deleted=False,
                        )

                        if executions.exists():
                            created_config_ids = [str(c.id) for c in created_configs]

                            for execution in executions:
                                variable_names_dict = execution.variable_names or {}
                                max_len = max(
                                    (len(v) for v in variable_names_dict.values()),
                                    default=1,
                                )
                                for config_id in created_config_ids:
                                    track_running_eval_count(
                                        start=True,
                                        prompt_config_eval_id=config_id,
                                        operation="set",
                                        num=max_len,
                                    )

                            viewset = PromptTemplateViewSet()
                            _PROMPT_TEMPLATE_EXECUTOR.submit(
                                _safe_background_task(
                                    viewset.run_evals_task,
                                    template,
                                    executions,
                                    created_config_ids,
                                    None,
                                    user_id=str(context.user.id),
                                )
                            )
                            eval_run_status = f"Running on {', '.join(version_to_run)}"
                        else:
                            eval_run_status = (
                                "No valid versions available to run evaluations on."
                            )
                else:
                    eval_run_status = "No versions available to run evaluations on."

            except Exception as e:
                logger.exception("set_eval_config_run_failed", error=str(e))
                eval_run_status = f"Failed to start: {str(e)}"

        rows = []
        for name in created:
            rows.append([name, "Created"])
        for name in skipped:
            rows.append([name, "Already linked"])

        table = markdown_table(["Eval Template", "Status"], rows)

        info_items = [
            ("Prompt Template", template.name),
            ("New Configs", str(len(created))),
            ("Skipped (existing)", str(len(skipped))),
        ]
        if eval_run_status:
            info_items.append(("Eval Run", eval_run_status))

        info = key_value_block(info_items)

        content = section("Eval Configs Set for Prompt", info)
        content += f"\n\n{table}"
        if eval_run_status and "Running" in eval_run_status:
            content += "\n\n_Evals are running asynchronously. Use `get_prompt_template` to check results._"
        else:
            content += "\n\n_Use `get_prompt_eval_configs` to see all linked evaluations, or `run_prompt_evals` to run them._"

        return ToolResult(
            content=content,
            data={
                "template_id": str(template.id),
                "template_name": template.name,
                "created": created,
                "skipped": skipped,
                "eval_run_status": eval_run_status,
            },
        )

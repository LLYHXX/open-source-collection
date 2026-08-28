from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
)
from ai_tools.registry import register_tool


class RerunExperimentInput(PydanticBaseModel):
    experiment_ids: list[str] = Field(
        description="List of experiment names or UUIDs to re-run",
        min_length=1,
        max_length=10,
    )
    max_concurrent_rows: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max concurrent rows for Temporal workflow",
    )


@register_tool
class RerunExperimentTool(BaseTool):
    name = "rerun_experiment"
    description = (
        "Re-runs one or more experiments. "
        "Resets variant statuses and re-processes all rows with the current prompt configs. "
        "Previous results will be overwritten."
    )
    category = "experiments"
    input_model = RerunExperimentInput

    def execute(self, params: RerunExperimentInput, context: ToolContext) -> ToolResult:

        from ai_tools.resolvers import resolve_experiment
        from model_hub.models.experiments import ExperimentsTable

        # Resolve each identifier (name or UUID) to an experiment
        resolved_ids = []
        resolve_errors = []
        for identifier in params.experiment_ids:
            exp_obj, err = resolve_experiment(identifier, context.organization)
            if err:
                resolve_errors.append(f"{identifier}: {err}")
            else:
                resolved_ids.append(exp_obj.id)

        if resolve_errors and not resolved_ids:
            return ToolResult.error(
                "No matching experiments found.\n" + "\n".join(resolve_errors),
                error_code="NOT_FOUND",
            )

        experiments = ExperimentsTable.objects.filter(
            id__in=resolved_ids,
            dataset__organization=context.organization,
            deleted=False,
        )

        if not experiments.exists():
            return ToolResult.error(
                "No matching experiments found.",
                error_code="NOT_FOUND",
            )

        queued = []
        errors = []

        for exp in experiments:
            try:
                from model_hub.models.choices import StatusType

                # Reset status
                exp.status = StatusType.QUEUED.value
                exp.save(update_fields=["status", "updated_at"])

                # Soft-delete old experiment datasets (matches backend PUT re_run behavior)
                experiment_datasets = exp.experiments_datasets
                if experiment_datasets.exists():
                    experiment_datasets.update(deleted=True)

                # Try Temporal workflow
                try:
                    from tfc.temporal.experiments.client import (
                        start_experiment_workflow,
                    )

                    start_experiment_workflow(
                        str(exp.id),
                        max_concurrent_rows=params.max_concurrent_rows,
                    )
                except Exception:
                    # Fallback to Celery
                    from model_hub.tasks.experiment_runner import process_experiments

                    exp.status = StatusType.RUNNING.value
                    exp.save(update_fields=["status"])
                    process_experiments.apply_async(args=([str(exp.id)],))

                queued.append(exp.name)
            except Exception as e:
                errors.append(f"{exp.name}: {str(e)}")

        info = key_value_block(
            [
                ("Experiments Re-run", str(len(queued))),
                ("Names", ", ".join(queued) if queued else "—"),
                ("Errors", str(len(errors)) if errors else "None"),
            ]
        )

        content = section("Experiments Re-run", info)
        if errors:
            content += "\n\n### Errors\n\n" + "\n".join(f"- {e}" for e in errors)
        content += "\n\n_Experiments are processing asynchronously. Use `get_experiment_results` to check progress._"

        return ToolResult(
            content=content,
            data={"queued": queued, "errors": errors},
        )

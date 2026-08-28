from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class RunExperimentEvalsInput(PydanticBaseModel):
    experiment_id: UUID = Field(
        description="The UUID of the experiment to run additional evaluations on"
    )
    eval_template_ids: list[UUID] = Field(
        description=(
            "List of UserEvalMetric IDs (evaluation template IDs) to run on the experiment. "
            "These must already be configured on the experiment via add_experiment_eval."
        ),
        min_length=1,
    )


@register_tool
class RunExperimentEvalsTool(BaseTool):
    name = "run_experiment_evals"
    description = (
        "Runs additional evaluations on an existing experiment's results. "
        "The eval templates must already be added to the experiment via add_experiment_eval. "
        "This triggers async processing of the specified evals on all experiment rows."
    )
    category = "experiments"
    input_model = RunExperimentEvalsInput

    def execute(
        self, params: RunExperimentEvalsInput, context: ToolContext
    ) -> ToolResult:
        import structlog
        from django.shortcuts import get_object_or_404

        from model_hub.models.choices import StatusType
        from model_hub.models.develop_dataset import UserEvalMetric
        from model_hub.models.experiments import ExperimentsTable
        from model_hub.services.experiment_runner import ExperimentRunner

        logger = structlog.get_logger(__name__)

        # Get the experiment
        try:
            experiment = (
                ExperimentsTable.objects.select_related("dataset")
                .prefetch_related("experiments_datasets", "user_eval_template_ids")
                .get(
                    id=params.experiment_id,
                    deleted=False,
                )
            )
        except ExperimentsTable.DoesNotExist:
            return ToolResult.not_found("Experiment", str(params.experiment_id))

        # Verify organization access
        if (
            experiment.dataset
            and experiment.dataset.organization != context.organization
        ):
            return ToolResult.not_found("Experiment", str(params.experiment_id))

        eval_template_ids = [str(eid) for eid in params.eval_template_ids]

        try:
            # Update source_id on the eval metrics
            UserEvalMetric.objects.filter(id__in=eval_template_ids).update(
                source_id=experiment.id
            )

            # Initialize the experiment runner and process evals
            experiment_runner = ExperimentRunner(experiment_id=experiment.id)
            experiment_runner.load_experiment()
            experiment_runner.empty_or_create_evals_column(
                eval_template_ids=eval_template_ids
            )

            # Update eval status
            experiment.user_eval_template_ids.all().filter(
                id__in=eval_template_ids
            ).update(status=StatusType.EXPERIMENT_EVALUATION.value)

            logger.info(
                "mcp_experiment_evals_triggered",
                experiment_id=str(experiment.id),
                eval_count=len(eval_template_ids),
            )

        except Exception as e:
            logger.exception(
                "mcp_experiment_evals_failed",
                experiment_id=str(experiment.id),
                error=str(e),
            )
            return ToolResult.error(
                f"Failed to run additional evaluations: {str(e)}",
                error_code="INTERNAL_ERROR",
            )

        info = key_value_block(
            [
                ("Experiment", experiment.name),
                ("Evals Triggered", str(len(eval_template_ids))),
                ("Status", "Running"),
            ]
        )

        content = section("Experiment Evals Started", info)
        content += (
            "\n\n_Evaluations are running asynchronously. "
            "Use `get_experiment_results` to check progress._"
        )

        return ToolResult(
            content=content,
            data={
                "experiment_id": str(experiment.id),
                "eval_template_ids": eval_template_ids,
                "status": "running",
            },
        )

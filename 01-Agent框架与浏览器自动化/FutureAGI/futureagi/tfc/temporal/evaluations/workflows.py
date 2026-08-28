"""
Temporal workflows for SDK evaluations.

These workflows handle on-demand evaluation execution:
- RunEvaluationWorkflow: Single evaluation
- RunEvaluationBatchWorkflow: Multiple evaluations with controlled concurrency (CI/CD)

IMPORTANT: Do NOT use workflow.logger in workflows - it uses Python's stdlib
logging which acquires locks and causes deadlocks. Logging should be done
in activities instead.
"""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import types only (no Django imports allowed in workflow sandbox)
from tfc.temporal.evaluations.types import (
    RunEvaluationBatchWorkflowInput,
    RunEvaluationBatchWorkflowOutput,
    RunEvaluationWorkflowInput,
    RunEvaluationWorkflowOutput,
    RunSingleEvaluationInput,
)

# Import Django model with sandbox passthrough for status enum access
with workflow.unsafe.imports_passed_through():
    from model_hub.models.evaluation import StatusChoices

# =============================================================================
# Retry Policies
# =============================================================================

EVALUATION_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=3,
    backoff_coefficient=2.0,
)


# =============================================================================
# Workflows
# =============================================================================


@workflow.defn
class RunEvaluationWorkflow:
    """
    Workflow to run a single evaluation on-demand.

    Triggered immediately when an async evaluation is requested via the SDK.
    Replaces the polling-based Celery approach.
    """

    @workflow.run
    async def run(
        self, input: RunEvaluationWorkflowInput
    ) -> RunEvaluationWorkflowOutput:
        # NOTE: Do NOT use workflow.logger - it causes deadlocks due to stdlib logging locks

        # Import activity reference (by name to avoid sandbox issues)
        result = await workflow.execute_activity(
            "run_single_evaluation_activity",
            RunSingleEvaluationInput(evaluation_id=input.evaluation_id),
            start_to_close_timeout=timedelta(hours=12),
            heartbeat_timeout=timedelta(minutes=5),
            retry_policy=EVALUATION_RETRY_POLICY,
        )

        # When using string-based activity invocation, result is a dict, not a dataclass
        return RunEvaluationWorkflowOutput(
            evaluation_id=result["evaluation_id"],
            status=result["status"],
            error=result.get("error"),
        )


@workflow.defn
class RunEvaluationBatchWorkflow:
    """
    Workflow to run multiple evaluations with controlled concurrency.

    Used by CI/CD evaluation runs to process batches of evaluations
    without overwhelming the system.
    """

    @workflow.run
    async def run(
        self, input: RunEvaluationBatchWorkflowInput
    ) -> RunEvaluationBatchWorkflowOutput:
        # NOTE: Do NOT use workflow.logger - it causes deadlocks due to stdlib logging locks

        total = len(input.evaluation_ids)
        completed = 0
        failed = 0

        # Use semaphore for controlled concurrency
        semaphore = asyncio.Semaphore(input.max_concurrent)

        async def process_one(eval_id: str) -> bool:
            """Process single evaluation with semaphore."""
            async with semaphore:
                try:
                    result = await workflow.execute_activity(
                        "run_single_evaluation_activity",
                        RunSingleEvaluationInput(evaluation_id=eval_id),
                        start_to_close_timeout=timedelta(hours=12),
                        heartbeat_timeout=timedelta(minutes=5),
                        retry_policy=EVALUATION_RETRY_POLICY,
                    )
                    return result["status"] == StatusChoices.COMPLETED
                except Exception:
                    return False

        # Process all evaluations concurrently (with limit)
        tasks = [process_one(eval_id) for eval_id in input.evaluation_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        for result in results:
            if isinstance(result, bool) and result:
                completed += 1
            else:
                failed += 1

        status = (
            "COMPLETED" if failed == 0 else "PARTIAL" if completed > 0 else "FAILED"
        )

        return RunEvaluationBatchWorkflowOutput(
            total=total,
            completed=completed,
            failed=failed,
            status=status,
        )


__all__ = [
    "RunEvaluationWorkflow",
    "RunEvaluationBatchWorkflow",
]

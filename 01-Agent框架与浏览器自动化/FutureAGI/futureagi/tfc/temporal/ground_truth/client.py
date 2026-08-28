"""
Client helper to trigger ground truth embedding workflows.
"""

import structlog

from tfc.temporal.ground_truth.types import GenerateEmbeddingsWorkflowInput

logger = structlog.get_logger(__name__)


async def trigger_embedding_generation(ground_truth_id: str) -> str | None:
    """
    Start the GenerateGroundTruthEmbeddingsWorkflow for a ground truth dataset.

    Returns the workflow run ID, or None if the trigger fails.
    """
    try:
        from tfc.temporal.common.client import get_client

        client = await get_client()

        workflow_id = f"gt-embed-{ground_truth_id}"

        from tfc.temporal.ground_truth.workflows import (
            GenerateGroundTruthEmbeddingsWorkflow,
        )

        handle = await client.start_workflow(
            GenerateGroundTruthEmbeddingsWorkflow.run,
            GenerateEmbeddingsWorkflowInput(ground_truth_id=ground_truth_id),
            id=workflow_id,
            task_queue="tasks_xl",
        )

        logger.info(
            "embedding_workflow_started",
            gt_id=ground_truth_id,
            workflow_id=workflow_id,
            run_id=handle.result_run_id,
        )

        return handle.result_run_id

    except Exception as e:
        logger.error(
            "embedding_workflow_trigger_failed",
            gt_id=ground_truth_id,
            error=str(e),
        )
        return None

"""
Temporal client helpers for Dataset Optimization.

Following the same pattern as agent_prompt_optimiser/client.py.
"""

import structlog
from asgiref.sync import async_to_sync

from tfc.temporal.common.client import get_client, start_workflow_sync
from tfc.temporal.dataset_optimization.types import DatasetOptimizationWorkflowInput
from tfc.temporal.dataset_optimization.workflows import DatasetOptimizationWorkflow

logger = structlog.get_logger(__name__)


def _workflow_id(run_id: str) -> str:
    return f"dataset-optimization-{run_id}"


def start_dataset_optimization_workflow(
    run_id: str, task_queue: str = "tasks_xl"
) -> str:
    """
    Start the dataset optimization workflow.

    Args:
        run_id: The OptimizeDataset ID
        task_queue: Temporal task queue (default: tasks_xl)

    Returns:
        Workflow ID
    """
    handle = start_workflow_sync(
        workflow_class=DatasetOptimizationWorkflow,
        workflow_input=DatasetOptimizationWorkflowInput(
            run_id=run_id, task_queue=task_queue
        ),
        workflow_id=_workflow_id(run_id),
        task_queue=task_queue,
    )
    return handle.id


def cancel_dataset_optimization(run_id: str) -> bool:
    """
    Cancel a running dataset optimization workflow.

    Args:
        run_id: The OptimizeDataset ID

    Returns:
        True if cancellation signal sent successfully
    """
    return async_to_sync(_cancel_dataset_optimization_async)(run_id)


async def _cancel_dataset_optimization_async(run_id: str) -> bool:
    """Async implementation for cancelling dataset optimization workflow."""
    workflow_id = _workflow_id(run_id)

    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.cancel()
        logger.info("Cancelled dataset optimization workflow", workflow_id=workflow_id)
        return True
    except Exception as e:
        logger.warning(f"Could not cancel workflow {workflow_id}: {e}")
        return False

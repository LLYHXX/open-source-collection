"""
Temporal client utilities for SDK evaluations.

Domain-specific workflow starters for on-demand evaluation execution.
Uses the centralized client from tfc.temporal.common.
"""

from typing import List, Optional

from tfc.temporal.common.client import (
    start_workflow_async,
    start_workflow_sync,
)

# =============================================================================
# Workflow ID Helpers
# =============================================================================


def _get_evaluation_workflow_id(evaluation_id: str) -> str:
    """Generate workflow ID for a single evaluation."""
    return f"evaluation-{evaluation_id}"


def _get_batch_evaluation_workflow_id(prefix: str = "batch") -> str:
    """Generate workflow ID for a batch evaluation."""
    import uuid

    return f"evaluation-batch-{prefix}-{uuid.uuid4().hex[:8]}"


# =============================================================================
# Single Evaluation Workflow Starters
# =============================================================================


async def start_evaluation_workflow_async(
    evaluation_id: str,
    task_queue: str = "tasks_s",
) -> str:
    """
    Start an evaluation workflow asynchronously.

    Args:
        evaluation_id: The Evaluation UUID to process
        task_queue: Temporal task queue to use

    Returns:
        The workflow ID
    """
    from tfc.temporal.evaluations.types import RunEvaluationWorkflowInput
    from tfc.temporal.evaluations.workflows import RunEvaluationWorkflow

    workflow_id = _get_evaluation_workflow_id(evaluation_id)

    handle = await start_workflow_async(
        workflow_class=RunEvaluationWorkflow,
        workflow_input=RunEvaluationWorkflowInput(
            evaluation_id=evaluation_id,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,  # Don't cancel - let existing run complete
    )

    return handle.id


def start_evaluation_workflow(
    evaluation_id: str,
    task_queue: str = "tasks_s",
) -> str:
    """
    Start an evaluation workflow synchronously.

    Convenience wrapper for Django views.

    Args:
        evaluation_id: The Evaluation UUID to process
        task_queue: Temporal task queue to use

    Returns:
        The workflow ID
    """
    from tfc.temporal.evaluations.types import RunEvaluationWorkflowInput
    from tfc.temporal.evaluations.workflows import RunEvaluationWorkflow

    workflow_id = _get_evaluation_workflow_id(evaluation_id)

    handle = start_workflow_sync(
        workflow_class=RunEvaluationWorkflow,
        workflow_input=RunEvaluationWorkflowInput(
            evaluation_id=evaluation_id,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return handle.id


# =============================================================================
# Batch Evaluation Workflow Starters
# =============================================================================


async def start_evaluation_batch_workflow_async(
    evaluation_ids: List[str],
    max_concurrent: int = 10,
    task_queue: str = "tasks_s",
    workflow_id_prefix: str = "batch",
) -> str:
    """
    Start a batch evaluation workflow asynchronously.

    Args:
        evaluation_ids: List of Evaluation UUIDs to process
        max_concurrent: Maximum concurrent evaluations
        task_queue: Temporal task queue to use
        workflow_id_prefix: Prefix for workflow ID (useful for CI/CD runs)

    Returns:
        The workflow ID
    """
    from tfc.temporal.evaluations.types import RunEvaluationBatchWorkflowInput
    from tfc.temporal.evaluations.workflows import RunEvaluationBatchWorkflow

    workflow_id = _get_batch_evaluation_workflow_id(workflow_id_prefix)

    handle = await start_workflow_async(
        workflow_class=RunEvaluationBatchWorkflow,
        workflow_input=RunEvaluationBatchWorkflowInput(
            evaluation_ids=evaluation_ids,
            max_concurrent=max_concurrent,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return handle.id


def start_evaluation_batch_workflow(
    evaluation_ids: List[str],
    max_concurrent: int = 10,
    task_queue: str = "tasks_s",
    workflow_id_prefix: str = "batch",
) -> str:
    """
    Start a batch evaluation workflow synchronously.

    Convenience wrapper for Django views.

    Args:
        evaluation_ids: List of Evaluation UUIDs to process
        max_concurrent: Maximum concurrent evaluations
        task_queue: Temporal task queue to use
        workflow_id_prefix: Prefix for workflow ID (useful for CI/CD runs)

    Returns:
        The workflow ID
    """
    from tfc.temporal.evaluations.types import RunEvaluationBatchWorkflowInput
    from tfc.temporal.evaluations.workflows import RunEvaluationBatchWorkflow

    workflow_id = _get_batch_evaluation_workflow_id(workflow_id_prefix)

    handle = start_workflow_sync(
        workflow_class=RunEvaluationBatchWorkflow,
        workflow_input=RunEvaluationBatchWorkflowInput(
            evaluation_ids=evaluation_ids,
            max_concurrent=max_concurrent,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return handle.id


__all__ = [
    "start_evaluation_workflow",
    "start_evaluation_workflow_async",
    "start_evaluation_batch_workflow",
    "start_evaluation_batch_workflow_async",
]

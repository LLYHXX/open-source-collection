"""
Temporal workflows and activities for SDK evaluations.

This module provides on-demand evaluation execution, replacing the
polling-based Celery approach.

Usage:
    from tfc.temporal.evaluations import start_evaluation_workflow

    # Trigger evaluation immediately when async eval is requested
    workflow_id = start_evaluation_workflow(evaluation_id=str(evaluation.id))
"""

from tfc.temporal.evaluations.client import (
    start_evaluation_batch_workflow,
    start_evaluation_batch_workflow_async,
    start_evaluation_workflow,
    start_evaluation_workflow_async,
)
from tfc.temporal.evaluations.types import (
    RunEvaluationBatchWorkflowInput,
    RunEvaluationBatchWorkflowOutput,
    RunEvaluationWorkflowInput,
    RunEvaluationWorkflowOutput,
    RunSingleEvaluationInput,
    RunSingleEvaluationOutput,
)

__all__ = [
    # Client functions
    "start_evaluation_workflow",
    "start_evaluation_workflow_async",
    "start_evaluation_batch_workflow",
    "start_evaluation_batch_workflow_async",
    # Types
    "RunSingleEvaluationInput",
    "RunSingleEvaluationOutput",
    "RunEvaluationWorkflowInput",
    "RunEvaluationWorkflowOutput",
    "RunEvaluationBatchWorkflowInput",
    "RunEvaluationBatchWorkflowOutput",
]

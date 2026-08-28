"""
Type definitions for evaluation Temporal activities and workflows.

These are separate from activities to avoid Django imports in workflow sandbox.
"""

from dataclasses import dataclass
from typing import Any, List, Optional

# =============================================================================
# On-Demand Single Evaluation Types (SDK async evaluations)
# =============================================================================


@dataclass
class RunSingleEvaluationInput:
    """Input for run_single_evaluation_activity - processes one Evaluation object."""

    evaluation_id: str


@dataclass
class RunSingleEvaluationOutput:
    """Output for run_single_evaluation_activity."""

    evaluation_id: str
    status: str  # "COMPLETED" or "FAILED"
    error: Optional[str] = None


@dataclass
class RunEvaluationWorkflowInput:
    """Input for RunEvaluationWorkflow - single evaluation on-demand."""

    evaluation_id: str
    task_queue: str = "tasks_s"


@dataclass
class RunEvaluationWorkflowOutput:
    """Output for RunEvaluationWorkflow."""

    evaluation_id: str
    status: str
    error: Optional[str] = None


@dataclass
class RunEvaluationBatchWorkflowInput:
    """Input for RunEvaluationBatchWorkflow - multiple evaluations (CI/CD)."""

    evaluation_ids: List[str]
    max_concurrent: int = 10
    task_queue: str = "tasks_s"


@dataclass
class RunEvaluationBatchWorkflowOutput:
    """Output for RunEvaluationBatchWorkflow."""

    total: int
    completed: int
    failed: int
    status: str


# =============================================================================
# Activity Input/Output Types (Polling-based - legacy)
# =============================================================================


@dataclass
class ProcessEvaluationInput:
    """Input for process_evaluation_activity."""

    eval_id: str
    eval_type: str  # "single", "experiment", or "optimization"


@dataclass
class ProcessEvaluationOutput:
    """Output for process_evaluation_activity."""

    eval_id: str
    status: str
    error: Optional[str] = None


@dataclass
class ProcessEvalBatchInput:
    """Input for process_eval_batch_activity."""

    column_id: str
    row_ids: list[str]
    runner_params: dict[str, Any]


@dataclass
class ProcessEvalBatchOutput:
    """Output for process_eval_batch_activity."""

    column_id: str
    rows_processed: int
    status: str
    error: Optional[str] = None


@dataclass
class ErrorLocalizerInput:
    """Input for error_localizer_activity."""

    task_id: str


@dataclass
class ErrorLocalizerOutput:
    """Output for error_localizer_activity."""

    task_id: str
    status: str
    error: Optional[str] = None


@dataclass
class FindPendingEvalsInput:
    """Input for find_pending_evals_activity."""

    limit: int = 30


@dataclass
class FindPendingEvalsOutput:
    """Output for find_pending_evals_activity."""

    evaluations: list[dict[str, str]]  # List of {"eval_id": str, "type": str}
    count: int


@dataclass
class FindPendingErrorLocalizerInput:
    """Input for find_pending_error_localizer_activity."""

    limit: int = 50


@dataclass
class FindPendingErrorLocalizerOutput:
    """Output for find_pending_error_localizer_activity."""

    task_ids: list[str]
    count: int


# =============================================================================
# Workflow Input/Output Types
# =============================================================================


@dataclass
class RunEvaluationsWorkflowInput:
    """Input for RunEvaluationsWorkflow."""

    limit: int = 30
    max_concurrent: int = 10
    task_queue: str = "default"


@dataclass
class RunEvaluationsWorkflowOutput:
    """Output for RunEvaluationsWorkflow."""

    total_processed: int
    successful: int
    failed: int
    status: str


@dataclass
class RunErrorLocalizerWorkflowInput:
    """Input for RunErrorLocalizerWorkflow."""

    limit: int = 50
    max_concurrent: int = 10
    task_queue: str = "default"


@dataclass
class RunErrorLocalizerWorkflowOutput:
    """Output for RunErrorLocalizerWorkflow."""

    total_processed: int
    successful: int
    failed: int
    status: str


__all__ = [
    # On-demand evaluation types (SDK async)
    "RunSingleEvaluationInput",
    "RunSingleEvaluationOutput",
    "RunEvaluationWorkflowInput",
    "RunEvaluationWorkflowOutput",
    "RunEvaluationBatchWorkflowInput",
    "RunEvaluationBatchWorkflowOutput",
    # Activity types (legacy polling)
    "ProcessEvaluationInput",
    "ProcessEvaluationOutput",
    "ProcessEvalBatchInput",
    "ProcessEvalBatchOutput",
    "ErrorLocalizerInput",
    "ErrorLocalizerOutput",
    "FindPendingEvalsInput",
    "FindPendingEvalsOutput",
    "FindPendingErrorLocalizerInput",
    "FindPendingErrorLocalizerOutput",
    # Workflow types (legacy polling)
    "RunEvaluationsWorkflowInput",
    "RunEvaluationsWorkflowOutput",
    "RunErrorLocalizerWorkflowInput",
    "RunErrorLocalizerWorkflowOutput",
]

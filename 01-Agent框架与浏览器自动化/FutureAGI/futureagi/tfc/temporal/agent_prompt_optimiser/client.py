"""
Temporal client helpers for Agent Prompt Optimiser.

Note: Signals (pause/resume/cancel) and queries (get_progress) have been removed.
Progress is now tracked via DB (PromptTrial records) instead of workflow queries.
"""

from tfc.temporal.agent_prompt_optimiser.types import (
    RunAgentPromptOptimiserWorkflowInput,
)
from tfc.temporal.agent_prompt_optimiser.workflows import AgentPromptOptimiserWorkflow
from tfc.temporal.common.client import start_workflow_sync


def _workflow_id(run_id: str) -> str:
    return f"agent-prompt-optimiser-{run_id}"


def start_agent_prompt_optimiser_workflow(
    run_id: str, task_queue: str = "tasks_xl"
) -> str:
    """
    Start the agent prompt optimiser workflow.

    Args:
        run_id: The AgentPromptOptimiserRun ID
        task_queue: Temporal task queue (default: tasks_xl)

    Returns:
        Workflow ID
    """
    handle = start_workflow_sync(
        workflow_class=AgentPromptOptimiserWorkflow,
        workflow_input=RunAgentPromptOptimiserWorkflowInput(
            run_id=run_id, task_queue=task_queue
        ),
        workflow_id=_workflow_id(run_id),
        task_queue=task_queue,
    )
    return handle.id

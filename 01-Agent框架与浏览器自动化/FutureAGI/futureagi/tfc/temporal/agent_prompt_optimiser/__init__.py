# Import eval_activities to trigger @temporal_activity registration
import tfc.temporal.agent_prompt_optimiser.eval_activities  # noqa: F401
from tfc.temporal.agent_prompt_optimiser.activities import ALL_ACTIVITIES
from tfc.temporal.agent_prompt_optimiser.workflows import (
    AgentPromptOptimiserWorkflow,
    EvaluateTrialWorkflow,
)


def get_workflows():
    return [AgentPromptOptimiserWorkflow, EvaluateTrialWorkflow]


def get_activities():
    return ALL_ACTIVITIES


__all__ = [
    "get_workflows",
    "get_activities",
    "AgentPromptOptimiserWorkflow",
    "EvaluateTrialWorkflow",
]

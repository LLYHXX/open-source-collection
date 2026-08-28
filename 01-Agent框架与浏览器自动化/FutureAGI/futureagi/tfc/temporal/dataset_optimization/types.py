"""
Type definitions for Dataset Optimization Temporal workflow.

Following the same pattern as agent_prompt_optimiser/types.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DatasetOptimizationWorkflowInput:
    run_id: str
    task_queue: str = "tasks_xl"
    resume: bool = True


@dataclass
class DatasetOptimizationWorkflowOutput:
    run_id: str
    status: str
    best_prompt: Optional[str] = None
    best_score: Optional[float] = None
    trials_completed: int = 0
    error: Optional[str] = None


@dataclass
class SetupRunOutput:
    run_id: str
    total_trials: int
    current_trial_number: int
    optimizer_state: Optional[Dict[str, Any]] = None
    best_prompt: Optional[str] = None
    best_score: Optional[float] = None


@dataclass
class TrialResult:
    """Result from a single optimization trial."""

    trial_number: int
    prompt: str
    average_score: float
    is_baseline: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

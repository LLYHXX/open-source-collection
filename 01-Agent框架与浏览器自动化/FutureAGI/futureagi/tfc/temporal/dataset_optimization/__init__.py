"""
Dataset Optimization Temporal module.

Provides workflows and activities for running dataset optimization.
"""

from tfc.temporal.dataset_optimization.activities import ALL_ACTIVITIES
from tfc.temporal.dataset_optimization.workflows import DatasetOptimizationWorkflow


def get_workflows():
    return [DatasetOptimizationWorkflow]


def get_activities():
    return ALL_ACTIVITIES


__all__ = [
    "get_workflows",
    "get_activities",
    "DatasetOptimizationWorkflow",
]

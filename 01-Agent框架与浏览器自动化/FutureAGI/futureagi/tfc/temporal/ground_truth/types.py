"""
Type definitions for ground truth embedding Temporal activities/workflows.
Separate from activities to avoid Django imports in workflow sandbox.
"""

from dataclasses import dataclass


@dataclass
class GenerateEmbeddingsInput:
    """Input for generate_ground_truth_embeddings_activity."""

    ground_truth_id: str


@dataclass
class GenerateEmbeddingsOutput:
    """Output for generate_ground_truth_embeddings_activity."""

    ground_truth_id: str
    rows_embedded: int
    status: str  # "completed" or "failed"
    error: str | None = None


@dataclass
class GenerateEmbeddingsWorkflowInput:
    """Input for GenerateGroundTruthEmbeddingsWorkflow."""

    ground_truth_id: str


@dataclass
class GenerateEmbeddingsWorkflowOutput:
    """Output for GenerateGroundTruthEmbeddingsWorkflow."""

    ground_truth_id: str
    rows_embedded: int
    status: str
    error: str | None = None

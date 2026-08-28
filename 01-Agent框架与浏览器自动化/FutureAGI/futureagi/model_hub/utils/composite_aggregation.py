"""
Composite eval aggregation utilities (Phase 7G).

Pure functions for aggregating scores, summaries, and error localizer
results across child evals in a composite evaluation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model_hub.types import CompositeChildResult

logger = logging.getLogger(__name__)


def aggregate_scores(
    scores_and_weights: list[tuple[float, float]],
    function: str,
    child_thresholds: list[float] | None = None,
) -> float | None:
    """
    Aggregate normalized 0-1 scores using the specified function.

    Args:
        scores_and_weights: List of (score, weight) tuples for completed children.
            Scores must be normalized to [0.0, 1.0].
        function: Aggregation function name — one of:
            "weighted_avg", "avg", "min", "max", "pass_rate"
        child_thresholds: Per-child pass thresholds (for pass_rate only).
            Must match length of scores_and_weights. Defaults to 0.5 for each.

    Returns:
        Aggregated score in [0.0, 1.0], or None if no valid scores.
    """
    if not scores_and_weights:
        return None

    scores = [s for s, _ in scores_and_weights]
    weights = [w for _, w in scores_and_weights]

    if function == "weighted_avg":
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        return sum(s * w for s, w in scores_and_weights) / total_weight

    if function == "avg":
        return sum(scores) / len(scores)

    if function == "min":
        return min(scores)

    if function == "max":
        return max(scores)

    if function == "pass_rate":
        if child_thresholds is None:
            child_thresholds = [0.5] * len(scores)
        passed = sum(
            1
            for score, threshold in zip(scores, child_thresholds)
            if score >= threshold
        )
        # Denominator is the number of scored children, not all children.
        # Callers that want a rate over total children (including failed/null)
        # must pass a total_children argument — for now this is "of scored".
        denominator = len(scores)
        if denominator == 0:
            return None
        return passed / denominator

    logger.warning(
        "Unknown aggregation function: %s, falling back to weighted_avg", function
    )
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    return sum(s * w for s, w in scores_and_weights) / total_weight


def aggregate_summaries(children: list[CompositeChildResult]) -> str:
    """
    Build a structured summary from child eval results.

    Each child's name, score, pass/fail status, and reason are included.
    No LLM synthesis — fast, deterministic, cheap.

    Args:
        children: List of CompositeChildResult objects.

    Returns:
        Formatted summary string.
    """
    parts = []
    for child in children:
        if child.status == "failed":
            parts.append(
                f"[{child.child_name}] (FAILED: {child.error or 'unknown error'})"
            )
            continue

        score_str = f"{child.score:.2f}" if child.score is not None else "N/A"
        parts.append(
            f"[{child.child_name}] (score: {score_str}, weight: {child.weight})"
        )
        if child.reason:
            parts.append(child.reason)
        parts.append("")  # blank line separator

    return "\n".join(parts).strip()


def aggregate_error_localizers(children: list[CompositeChildResult]) -> dict:
    """
    Group error localizer results by child eval name.

    Each child's error_localizer_result is included as-is.
    No merging or re-ranking across children.

    Args:
        children: List of CompositeChildResult objects.

    Returns:
        Dict mapping child_name to error_localizer_result (or None if not available).
    """
    result = {}
    for child in children:
        if child.error_localizer_result is not None:
            result[child.child_name] = child.error_localizer_result
    return result

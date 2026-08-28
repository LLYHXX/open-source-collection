from abc import ABC, abstractmethod
from typing import Any

# Registry mapping platform name -> transformer class instance
_TRANSFORMER_REGISTRY: dict[str, "BaseTraceTransformer"] = {}


def register_transformer(platform: str, transformer: "BaseTraceTransformer"):
    """Register a platform trace transformer."""
    _TRANSFORMER_REGISTRY[platform] = transformer


def get_transformer(platform: str) -> "BaseTraceTransformer":
    """Get the transformer instance for a given platform."""
    transformer = _TRANSFORMER_REGISTRY.get(platform)
    if transformer is None:
        raise ValueError(
            f"No trace transformer registered for platform '{platform}'. "
            f"Available: {list(_TRANSFORMER_REGISTRY.keys())}"
        )
    return transformer


class BaseTraceTransformer(ABC):
    """Abstract base class for data transformers.

    Each platform implements this to map its data model to FutureAGI models.
    """

    @abstractmethod
    def transform_trace(
        self,
        raw_trace: dict[str, Any],
        project_id: str,
    ) -> dict[str, Any]:
        """Transform a platform trace into FutureAGI Trace model fields.

        Returns:
            Dict of field values for Trace model (ready for update_or_create).
        """
        ...

    @abstractmethod
    def transform_observations(
        self,
        raw_trace: dict[str, Any],
        trace_id: str,
        project_id: str,
    ) -> list[dict[str, Any]]:
        """Transform platform observations into FutureAGI ObservationSpan dicts.

        Returns:
            List of dicts, each with field values for ObservationSpan model.
        """
        ...

    @abstractmethod
    def transform_scores(
        self,
        raw_trace: dict[str, Any],
        trace_id: str,
    ) -> list[dict[str, Any]]:
        """Transform platform scores into FutureAGI EvalLogger dicts.

        Returns:
            List of dicts, each with field values for EvalLogger model.
        """
        ...

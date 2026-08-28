from enum import Enum

from .groundedness import GroundednessScore
from .passed import Passed
from .similarity_score import SimilarityScore


class MetricType(Enum):
    GROUNDEDNESS = "groundedness"
    PASSED = "passed"
    SIMILARITY_SCORE = "similarity_score"
    SCORE = "score"

    @staticmethod
    def get_class(metric_type):
        """
        Returns the class of the metric type.
        """
        if metric_type == MetricType.GROUNDEDNESS.value:
            return GroundednessScore
        elif metric_type == MetricType.PASSED.value:
            return Passed
        elif metric_type == MetricType.SIMILARITY_SCORE.value:
            return SimilarityScore
        else:
            raise NotImplementedError(f"Metric type {metric_type} not implemented.")

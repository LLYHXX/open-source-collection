from decimal import Decimal

from .metric import Metric


class SimilarityScore(Metric):
    """
    Decimal metric indicating the similarity score between the response and the ground truth.
    """

    @staticmethod
    def compute(similarity_score: int | float | Decimal) -> Decimal:
        """
        Computes the result.

        Returns:
            Decimal: similarity score between the response and the ground truth.
        """
        return Decimal(similarity_score)

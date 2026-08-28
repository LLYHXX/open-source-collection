from rest_framework import serializers

from model_hub.models import OptimizeDataset
from model_hub.serializers.metric import MetricSerializerNameAndId


class OptimizeDatasetSerializer(serializers.ModelSerializer):
    metrics = MetricSerializerNameAndId(many=True)

    class Meta:
        model = OptimizeDataset
        fields = (
            "id",
            "created_at",
            "name",
            "optimize_type",
            "environment",
            "version",
            "status",
            "metrics",
            "start_date",
            "end_date",
        )


# class OptimizeDatasetViewSerializer(serializers.ModelSerializer):
#     metrics = MetricSerializer(many=True)
#     model = AIModelSerializer()

#     class Meta:
#         model = OptimizeDataset
#         fields = (
#             "id",
#             "created_at",
#             "name",
#             "optimize_type",
#             "metrics",
#             "start_date",
#             "end_date",
#             "model",
#             "environment",
#             "version",
#             "status",
#         )


# Serializer for OptimizeDataset model
class OptimizeDatasetKbSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizeDataset
        fields = [
            "id",
            "knowledge_base_metrics",
            "knowledge_base_filters",
            "optimized_k_prompts",
            "name",
            "prompt",
            "variables",
            "status",
        ]

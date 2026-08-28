from rest_framework import serializers

from model_hub.models import Metric
from model_hub.serializers.ai_model import AIModelsSerializer


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = "__all__"


class MetricSerializerWithAIModel(serializers.ModelSerializer):
    model = AIModelsSerializer(read_only=True)

    class Meta:
        model = Metric
        fields = "__all__"


class MetricSerializerNameAndId(serializers.ModelSerializer):
    class Meta:
        model = Metric
        fields = ["id", "name"]

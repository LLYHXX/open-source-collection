from rest_framework import serializers

from model_hub.models import AIModel
from model_hub.serializers.monitor import MonitorSerializer


class AIModelSerializer(serializers.ModelSerializer):
    monitors = MonitorSerializer(read_only=True, many=True)

    class Meta:
        model = AIModel
        fields = "__all__"


class AIModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = (
            "id",
            "model_type",
            "user_model_id",
            "baseline_model_environment",
            "baseline_model_version",
        )


class AIModelsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = (
            "id",
            "model_type",
            "user_model_id",
        )

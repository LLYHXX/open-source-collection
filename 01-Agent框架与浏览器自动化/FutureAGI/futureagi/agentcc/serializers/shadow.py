from rest_framework import serializers

from agentcc.models.shadow_experiment import AgentccShadowExperiment
from agentcc.models.shadow_result import AgentccShadowResult


class AgentccShadowExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccShadowExperiment
        fields = [
            "id",
            "name",
            "description",
            "source_model",
            "shadow_model",
            "shadow_provider",
            "sample_rate",
            "status",
            "total_comparisons",
            "config",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_comparisons",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_sample_rate(self, value):
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("sample_rate must be between 0.0 and 1.0")
        return value


class AgentccShadowResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccShadowResult
        fields = [
            "id",
            "experiment",
            "request_id",
            "source_model",
            "shadow_model",
            "source_response",
            "shadow_response",
            "source_latency_ms",
            "shadow_latency_ms",
            "source_tokens",
            "shadow_tokens",
            "source_status_code",
            "shadow_status_code",
            "shadow_error",
            "prompt_hash",
            "created_at",
        ]
        read_only_fields = fields

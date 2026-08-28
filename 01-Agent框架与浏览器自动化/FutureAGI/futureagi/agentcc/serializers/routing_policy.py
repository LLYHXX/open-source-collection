from rest_framework import serializers

from agentcc.models.routing_policy import AgentccRoutingPolicy


class AgentccRoutingPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccRoutingPolicy
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "version",
            "config",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_config(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("config must be a JSON object")
        return value

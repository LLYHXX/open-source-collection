from rest_framework import serializers

from agentcc.models.session import AgentccSession


class AgentccSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccSession
        fields = [
            "id",
            "organization",
            "session_id",
            "name",
            "status",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

    def validate_status(self, value):
        valid = [c[0] for c in AgentccSession.STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"status must be one of: {', '.join(valid)}"
            )
        return value

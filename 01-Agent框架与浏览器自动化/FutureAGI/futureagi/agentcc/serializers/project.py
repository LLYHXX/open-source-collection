from rest_framework import serializers

from agentcc.models import AgentccProject


class AgentccProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccProject
        fields = [
            "id",
            "tracer_project",
            "name",
            "description",
            "config",
            "organization",
            "workspace",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "workspace",
            "created_at",
            "updated_at",
        ]

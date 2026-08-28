import re

from rest_framework import serializers

from agentcc.models.prompt_template import AgentccPromptTemplate


class AgentccPromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentccPromptTemplate
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "version",
            "template",
            "variables",
            "model",
            "environment",
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

    def validate_variables(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("variables must be a JSON array")
        for v in value:
            if not isinstance(v, dict) or "name" not in v:
                raise serializers.ValidationError(
                    "Each variable must be an object with a 'name' field"
                )
        return value


class AgentccPromptTemplateRenderSerializer(serializers.Serializer):
    """Serializer for rendering a prompt template with variables."""

    variables = serializers.DictField(required=True)

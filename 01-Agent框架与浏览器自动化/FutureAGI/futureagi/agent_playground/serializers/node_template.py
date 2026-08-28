from rest_framework import serializers

from agent_playground.models.node_template import NodeTemplate


class NodeTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing node templates."""

    class Meta:
        model = NodeTemplate
        fields = [
            "id",
            "name",
            "display_name",
            "description",
            "icon",
            "categories",
        ]
        read_only_fields = fields


class NodeTemplateDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for node templates."""

    class Meta:
        model = NodeTemplate
        fields = [
            "id",
            "name",
            "display_name",
            "description",
            "icon",
            "categories",
            "input_definition",
            "output_definition",
            "input_mode",
            "output_mode",
            "config_schema",
        ]
        read_only_fields = fields

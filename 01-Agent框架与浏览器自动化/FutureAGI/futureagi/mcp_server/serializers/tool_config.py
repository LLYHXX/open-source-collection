from rest_framework import serializers

from mcp_server.constants import TOOL_GROUPS
from mcp_server.models.tool_config import MCPToolGroupConfig


class MCPToolGroupConfigSerializer(serializers.ModelSerializer):
    available_groups = serializers.SerializerMethodField()

    class Meta:
        model = MCPToolGroupConfig
        fields = ["enabled_groups", "disabled_tools", "available_groups"]

    def get_available_groups(self, obj):
        result = []
        for slug, meta in TOOL_GROUPS.items():
            result.append(
                {
                    "slug": slug,
                    "name": meta["name"],
                    "description": meta["description"],
                    "enabled": slug in (obj.enabled_groups or []),
                }
            )
        return result


class MCPToolGroupConfigUpdateSerializer(serializers.Serializer):
    enabled_groups = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    disabled_tools = serializers.ListField(
        child=serializers.CharField(), required=False
    )

    def validate_enabled_groups(self, value):
        valid_groups = set(TOOL_GROUPS.keys())
        for group in value:
            if group not in valid_groups:
                raise serializers.ValidationError(f"Invalid group: {group}")
        return value

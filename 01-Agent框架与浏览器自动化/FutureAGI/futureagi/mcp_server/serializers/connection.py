from rest_framework import serializers

from mcp_server.models.connection import MCPConnection
from mcp_server.serializers.tool_config import MCPToolGroupConfigSerializer


class MCPConnectionSerializer(serializers.ModelSerializer):
    tool_config = MCPToolGroupConfigSerializer(read_only=True)

    class Meta:
        model = MCPConnection
        fields = [
            "id",
            "connection_mode",
            "is_active",
            "client_name",
            "client_version",
            "created_at",
            "updated_at",
            "tool_config",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tool_config"]


class MCPConnectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCPConnection
        fields = ["connection_mode", "is_active"]

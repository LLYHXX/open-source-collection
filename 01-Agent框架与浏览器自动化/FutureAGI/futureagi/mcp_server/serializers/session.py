from rest_framework import serializers

from mcp_server.models.session import MCPSession


class MCPSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCPSession
        fields = [
            "id",
            "status",
            "transport",
            "client_name",
            "client_version",
            "client_os",
            "started_at",
            "last_activity_at",
            "ended_at",
            "tool_call_count",
            "error_count",
        ]

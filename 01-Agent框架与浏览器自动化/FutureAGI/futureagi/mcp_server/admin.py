from django.contrib import admin

from mcp_server.models.connection import MCPConnection
from mcp_server.models.oauth_client import MCPOAuthClient
from mcp_server.models.session import MCPSession
from mcp_server.models.tool_config import MCPToolGroupConfig
from mcp_server.models.usage import MCPUsageRecord


@admin.register(MCPConnection)
class MCPConnectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "organization",
        "workspace",
        "connection_mode",
        "is_active",
        "created_at",
    ]
    list_filter = ["connection_mode", "is_active"]
    search_fields = ["user__email", "organization__name"]
    raw_id_fields = ["user", "organization", "workspace", "api_key"]


@admin.register(MCPToolGroupConfig)
class MCPToolGroupConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "connection", "enabled_groups"]
    raw_id_fields = ["connection"]


@admin.register(MCPSession)
class MCPSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "status",
        "transport",
        "tool_call_count",
        "started_at",
    ]
    list_filter = ["status", "transport"]
    search_fields = ["user__email"]
    raw_id_fields = ["connection", "user", "organization", "workspace"]


@admin.register(MCPUsageRecord)
class MCPUsageRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "tool_name", "response_status", "latency_ms", "called_at"]
    list_filter = ["response_status", "tool_name"]
    search_fields = ["tool_name"]
    raw_id_fields = ["session", "organization", "workspace", "user"]


@admin.register(MCPOAuthClient)
class MCPOAuthClientAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "client_id", "is_active", "created_at"]
    list_filter = ["is_active"]

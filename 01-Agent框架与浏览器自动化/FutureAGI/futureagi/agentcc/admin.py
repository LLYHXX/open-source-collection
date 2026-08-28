from django.contrib import admin

from agentcc.models import (
    AgentccAPIKey,
    AgentccBlocklist,
    AgentccCustomPropertySchema,
    AgentccGuardrailFeedback,
    AgentccGuardrailPolicy,
    AgentccProject,
    AgentccRequestLog,
    AgentccRoutingPolicy,
    AgentccSession,
    AgentccWebhook,
    AgentccWebhookEvent,
)


@admin.register(AgentccProject)
class AgentccProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccAPIKey)
class AgentccAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "key_prefix", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "owner", "key_prefix")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccRequestLog)
class AgentccRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        "request_id",
        "model",
        "provider",
        "status_code",
        "latency_ms",
        "started_at",
    )
    list_filter = ("is_error", "is_stream", "provider")
    search_fields = ("request_id", "model", "provider")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccGuardrailPolicy)
class AgentccGuardrailPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "scope", "mode", "is_active", "priority", "created_at")
    list_filter = ("scope", "mode", "is_active")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccBlocklist)
class AgentccBlocklistAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccGuardrailFeedback)
class AgentccGuardrailFeedbackAdmin(admin.ModelAdmin):
    list_display = ("check_name", "feedback", "created_by", "created_at")
    list_filter = ("feedback", "check_name")
    search_fields = ("check_name", "comment")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccSession)
class AgentccSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("session_id", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccWebhook)
class AgentccWebhookAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "url")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccWebhookEvent)
class AgentccWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "webhook", "status", "attempts", "created_at")
    list_filter = ("status", "event_type")
    search_fields = ("event_type",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccCustomPropertySchema)
class AgentccCustomPropertySchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "property_type", "required", "created_at")
    list_filter = ("property_type", "required")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AgentccRoutingPolicy)
class AgentccRoutingPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

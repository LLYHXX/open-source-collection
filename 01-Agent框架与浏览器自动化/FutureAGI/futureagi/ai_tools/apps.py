from django.apps import AppConfig


class AiToolsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai_tools"
    verbose_name = "AI Tools"

    def ready(self):
        # Import all tool modules to trigger @register_tool decorators
        import ai_tools.tools  # noqa: F401

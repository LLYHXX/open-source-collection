from django.apps import AppConfig


class AgentccConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agentcc"
    # app_label pinned to "prism" so django_migrations / django_content_type
    # rows (recorded pre-rename) keep matching without a data migration.
    # Python import path is agentcc; Django's internal app_label stays prism.
    label = "prism"

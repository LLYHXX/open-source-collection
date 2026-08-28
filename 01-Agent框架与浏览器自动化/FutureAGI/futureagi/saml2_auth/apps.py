from django.apps import AppConfig


class Saml2AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "saml2_auth"

    def ready(self):
        pass

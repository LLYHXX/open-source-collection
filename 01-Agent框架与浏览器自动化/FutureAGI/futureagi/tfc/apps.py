from django.apps import AppConfig


class TfcConfig(AppConfig):
    name = "tfc"
    verbose_name = "TFC"

    def ready(self):
        """
        Called when Django is fully loaded.

        This is the proper place to import signal handlers.
        """
        # Import signals to register them
        # This must be done here, not in __init__.py, to avoid
        # importing Django before it's configured.
        from tfc.utils import signals  # noqa: F401

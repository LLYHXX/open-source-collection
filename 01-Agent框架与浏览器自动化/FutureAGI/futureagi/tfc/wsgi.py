"""
WSGI config for tfc project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

# Must set DJANGO_SETTINGS_MODULE before any Django or telemetry imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfc.settings.settings")

# OpenTelemetry instrumentation - must be initialized before Django
# This enables distributed tracing including LLM spans
try:
    from tfc.telemetry import init_telemetry, instrument_for_django

    provider = init_telemetry(component="django")
    if provider:
        instrument_for_django()
except ImportError as e:
    import logging

    logging.getLogger(__name__).warning(f"Failed to initialize telemetry: {e}")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

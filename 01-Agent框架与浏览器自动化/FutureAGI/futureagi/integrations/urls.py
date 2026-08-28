from django.urls import include, path
from rest_framework.routers import DefaultRouter

from integrations.views.integration_connection import IntegrationConnectionViewSet
from integrations.views.sync_log import SyncLogViewSet

router = DefaultRouter()
router.register(
    r"connections", IntegrationConnectionViewSet, basename="integration-connections"
)
router.register(r"sync-logs", SyncLogViewSet, basename="sync-logs")

urlpatterns = [
    path("", include(router.urls)),
]

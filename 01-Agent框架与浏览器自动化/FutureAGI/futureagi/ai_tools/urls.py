from django.urls import path

from ai_tools.views import ToolDiscoveryView

urlpatterns = [
    path("tools/", ToolDiscoveryView.as_view(), name="ai-tools-discovery"),
]

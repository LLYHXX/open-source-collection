from django.urls import path

from mcp_server.views.analytics import (
    MCPAnalyticsSummaryView,
    MCPAnalyticsTimelineView,
    MCPAnalyticsToolsView,
)
from mcp_server.views.config import MCPConfigView, MCPToolGroupsView
from mcp_server.views.health import MCPHealthView
from mcp_server.views.oauth import (
    MCPOAuthAuthorizeView,
    MCPOAuthConsentView,
    MCPOAuthTokenView,
)

try:
    from mcp_server.views.oauth_approve import (
        MCPOAuthApproveInfoView,
        MCPOAuthApproveView,
    )

    _HAS_MCP_APPROVE = True
except ImportError:
    _HAS_MCP_APPROVE = False
from mcp_server.views.sessions import MCPSessionDetailView, MCPSessionListView
from mcp_server.views.transport import MCPToolCallView, MCPToolListView

urlpatterns = [
    # Health check (unauthenticated)
    path("health/", MCPHealthView.as_view(), name="mcp-health"),
    # Internal API (for stdio proxy and direct API)
    path("internal/tool-call/", MCPToolCallView.as_view(), name="mcp-tool-call"),
    path("internal/tools/", MCPToolListView.as_view(), name="mcp-tool-list"),
    # Dashboard API: Configuration
    path("config/", MCPConfigView.as_view(), name="mcp-config"),
    path("config/tool-groups/", MCPToolGroupsView.as_view(), name="mcp-tool-groups"),
    # Dashboard API: Sessions
    path("sessions/", MCPSessionListView.as_view(), name="mcp-sessions"),
    path(
        "sessions/<uuid:session_id>/",
        MCPSessionDetailView.as_view(),
        name="mcp-session-detail",
    ),
    # Dashboard API: Analytics
    path(
        "analytics/summary/",
        MCPAnalyticsSummaryView.as_view(),
        name="mcp-analytics-summary",
    ),
    path(
        "analytics/tools/", MCPAnalyticsToolsView.as_view(), name="mcp-analytics-tools"
    ),
    path(
        "analytics/timeline/",
        MCPAnalyticsTimelineView.as_view(),
        name="mcp-analytics-timeline",
    ),
    # OAuth 2.0
    path(
        "oauth/authorize/", MCPOAuthAuthorizeView.as_view(), name="mcp-oauth-authorize"
    ),
    path("oauth/consent/", MCPOAuthConsentView.as_view(), name="mcp-oauth-consent"),
    path("oauth/token/", MCPOAuthTokenView.as_view(), name="mcp-oauth-token"),
]

# OAuth approval endpoints for MCP SDK flow (requires mcp package)
if _HAS_MCP_APPROVE:
    urlpatterns += [
        path(
            "oauth/approve-info/",
            MCPOAuthApproveInfoView.as_view(),
            name="mcp-oauth-approve-info",
        ),
        path("oauth/approve/", MCPOAuthApproveView.as_view(), name="mcp-oauth-approve"),
    ]

import hmac

from rest_framework.permissions import BasePermission

from agentcc.services.gateway_client import AGENTCC_ADMIN_TOKEN


class IsAdminToken(BasePermission):
    """Authenticate requests using the gateway admin token."""

    def has_permission(self, request, view):
        if not AGENTCC_ADMIN_TOKEN:
            return False
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return bool(token) and hmac.compare_digest(token, AGENTCC_ADMIN_TOKEN)
        return False

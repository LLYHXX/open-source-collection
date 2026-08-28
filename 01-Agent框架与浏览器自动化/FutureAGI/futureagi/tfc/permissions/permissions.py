import os

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class APIKeyPermission(BasePermission):
    def has_permission(self, request, view):
        api_key_header = request.META.get("HTTP_X_API_KEY")
        if not api_key_header:
            raise AuthenticationFailed("No API key provided")

        expected_api_key = os.getenv("API_KEY")
        if not expected_api_key:
            raise AuthenticationFailed("API key not configured on server")

        if api_key_header != expected_api_key:
            raise AuthenticationFailed("Invalid API key")

        return True

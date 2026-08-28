from urllib.parse import parse_qs

import structlog
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections, connection

from accounts.authentication import decode_token

logger = structlog.get_logger(__name__)

User = get_user_model()


class JWTAuthMiddleware:
    """Middleware to authenticate WebSocket connections using JWT from query parameters."""

    def __init__(self, inner):
        self.inner = inner

    async def close_connection(self, send, code, reason):
        """Properly close a WebSocket connection with custom code."""
        # First, send a proper WebSocket accept to establish the connection
        await send(
            {
                "type": "websocket.accept",
            }
        )

        # Then, send a proper close frame with the custom code
        await send(
            {
                "type": "websocket.close",
                "code": code,
                "reason": reason,
            }
        )

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if token:
            user = await self.get_user_from_token(token)
            if isinstance(user, AnonymousUser):
                await self.close_connection(send, 4003, "Invalid token provided")
                return

            scope["user"] = user
        else:
            await self.close_connection(send, 4003, "Invalid token provided")
            return

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Validates JWT token and retrieves user"""
        try:
            close_old_connections()
            with connection.cursor():
                try:
                    user, token = decode_token(token)
                    return user
                except Exception as e:
                    logger.warning(
                        "websocket_auth_failed",
                        reason=str(e),
                        error_type=type(e).__name__,
                    )
                    return AnonymousUser()

        except Exception as e:
            logger.error(
                "websocket_auth_error",
                reason=str(e),
                error_type=type(e).__name__,
            )
            return AnonymousUser()
        finally:
            # Always ensure connections are closed
            close_old_connections()

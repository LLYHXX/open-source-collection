import asyncio
import json
from urllib.parse import parse_qs

import redis.asyncio as aioredis
import structlog
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

logger = structlog.get_logger(__name__)


class SimulationUpdateConsumer(AsyncJsonWebsocketConsumer):
    """
    Dedicated WebSocket consumer for simulation grid updates.

    Frontend connects with test_id query param. The consumer verifies the
    user's organization, subscribes to the org-scoped Redis pub/sub channel,
    and forwards messages so the simulation runs grid refreshes in real-time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscriber_task = None
        self._redis = None
        self._pubsub = None
        self.test_id = None
        self.organization_id = None

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        # Verify user has an organization (prevents cross-org data leaks)
        org_id = await self._get_organization_id()
        if org_id is None:
            await self.close(code=4002)
            return
        self.organization_id = str(org_id)

        # Parse query string using parse_qs for proper URL-decoding
        params = parse_qs(self.scope.get("query_string", b"").decode())
        self.test_id = params.get("test_id", [None])[0]

        if not self.test_id:
            await self.close(code=4003)
            return

        await self.accept()
        logger.info(
            "simulation_ws_connected",
            test_id=self.test_id,
            organization_id=self.organization_id,
        )
        self._subscriber_task = asyncio.create_task(self._subscribe_redis())

    @database_sync_to_async
    def _get_organization_id(self):
        user = self.scope.get("user")
        if not user:
            return None
        try:
            from accounts.models.organization_membership import OrganizationMembership

            membership = (
                OrganizationMembership.objects.filter(user=user, is_active=True)
                .select_related("organization")
                .first()
            )
            if membership:
                return membership.organization.id
            # Fallback to legacy FK
            if getattr(user, "organization", None):
                return user.organization.id
            return None
        except Exception:
            return None

    async def disconnect(self, close_code):
        logger.info(
            "simulation_ws_disconnected",
            test_id=self.test_id,
            close_code=close_code,
        )
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    async def _subscribe_redis(self):
        channel = f"simulation_updates:{self.organization_id}:{self.test_id}"
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(channel)
            logger.info("simulation_ws_subscribed", channel=channel)

            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.send_json(data)
                    except Exception:
                        logger.exception("Error forwarding Redis message to WebSocket")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Redis subscription error", channel=channel)
            try:
                await self.send_json(
                    {"type": "error", "message": "Subscription failed"}
                )
                await self.close(code=4500)
            except Exception:
                pass

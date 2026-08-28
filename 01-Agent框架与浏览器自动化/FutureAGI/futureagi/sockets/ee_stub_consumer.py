from channels.generic.websocket import AsyncJsonWebsocketConsumer


class EEUpgradeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json(
            {
                "error": "Not available on OSS. Upgrade your plan.",
                "upgrade_required": True,
                "feature": "falcon_ai",
            }
        )
        await self.close(code=4402)

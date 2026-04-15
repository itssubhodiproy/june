import json

from redis.asyncio import Redis

from app.config import settings
from app.types import (
    DocumentErrorEvent,
    DocumentParsingTask,
    DocumentProcessingEvent,
    DocumentReadyEvent,
)


class RedisClient:
    def __init__(self) -> None:
        self.client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def pop_document_task(self) -> DocumentParsingTask:
        _, payload = await self.client.brpop(settings.QUEUE_NAME)
        return DocumentParsingTask.model_validate_json(payload)

    async def publish_processing(self, event: DocumentProcessingEvent) -> None:
        await self.client.publish(f"table:{event.table_id}", json.dumps(event.model_dump()))

    async def publish_ready(self, event: DocumentReadyEvent) -> None:
        await self.client.publish(f"table:{event.table_id}", json.dumps(event.model_dump()))

    async def publish_error(self, event: DocumentErrorEvent) -> None:
        await self.client.publish(f"table:{event.table_id}", json.dumps(event.model_dump()))

    async def close(self) -> None:
        await self.client.aclose()

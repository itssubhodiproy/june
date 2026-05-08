import json

from redis.asyncio import Redis

from app.config import settings
from app.types import (
    CellCompletedEvent,
    CellErrorEvent,
    ExtractionTask,
    RunCompletedEvent,
)


class RedisClient:
    def __init__(self) -> None:
        self.client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def enqueue_extraction_task(self, task: ExtractionTask) -> None:
        await self.client.lpush(settings.QUEUE_NAME, task.model_dump_json())

    async def pop_extraction_task(self, timeout: int = 0) -> ExtractionTask | None:
        result = await self.client.brpop(settings.QUEUE_NAME, timeout=timeout)
        if result is None:
            return None
        _, payload = result
        return ExtractionTask.model_validate_json(payload)

    async def publish_cell_completed(self, event: CellCompletedEvent) -> None:
        await self.client.publish(
            f"table:{event.table_id}",
            json.dumps(event.model_dump()),
        )

    async def publish_cell_error(self, event: CellErrorEvent) -> None:
        await self.client.publish(
            f"table:{event.table_id}",
            json.dumps(event.model_dump()),
        )

    async def publish_run_completed(self, event: RunCompletedEvent) -> None:
        await self.client.publish(
            f"table:{event.table_id}",
            json.dumps(event.model_dump()),
        )

    async def close(self) -> None:
        await self.client.aclose()

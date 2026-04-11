import json
from uuid import uuid4, UUID

from redis.asyncio import Redis


async def enqueue_document_parsing(
    redis: Redis,
    *,
    document_id: UUID,
    file_key: str,
    table_id: UUID,
) -> None:
    payload = {
        "task_id": str(uuid4()),
        "document_id": str(document_id),
        "file_key": file_key,
        "table_id": str(table_id),
        "retry_count": 0,
    }
    await redis.lpush("document_parsing", json.dumps(payload))

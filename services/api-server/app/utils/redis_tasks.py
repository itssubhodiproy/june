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

async def enqueue_extraction_run(
    redis: Redis,
    *,
    table_id: UUID,
    type: str = "run_all",
    cell_id: UUID | None = None,
) -> None:
    payload = {
        "table_id": str(table_id),
        "type": type,
    }
    if cell_id:
        payload["cell_id"] = str(cell_id)
    await redis.lpush("extraction_tasks", json.dumps(payload))

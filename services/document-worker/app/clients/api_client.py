import httpx

from app.config import settings
from app.types import ChunkPayload


class ApiClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.API_SERVER_URL,
            timeout=30.0,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
        )

    async def store_chunks(self, document_id: str, chunks: list[ChunkPayload]) -> dict:
        response = await self.client.post(
            f"/api/documents/{document_id}/chunks",
            json={"chunks": [chunk.model_dump() for chunk in chunks]},
        )
        response.raise_for_status()
        return response.json()

    async def update_document(
        self,
        document_id: str,
        *,
        parse_status: str,
        page_count: int | None = None,
    ) -> dict:
        payload: dict[str, object] = {"parse_status": parse_status}
        if page_count is not None:
            payload["page_count"] = page_count

        response = await self.client.patch(
            f"/api/documents/{document_id}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        await self.client.aclose()

import httpx

from app.config import settings
from app.types import (
    BulkUpdateResponse,
    CellUpdatePayload,
    ChunkSearchResponse,
    ExtractionManifest,
)


class ApiClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.API_SERVER_URL,
            timeout=30.0,
            headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
        )

    async def get_extraction_manifest(
        self,
        table_id: str,
        *,
        cell_id: str | None = None,
    ) -> ExtractionManifest:
        params = {"cell_id": cell_id} if cell_id is not None else None
        response = await self.client.get(
            f"/api/tables/{table_id}/extraction-manifest",
            params=params,
        )
        response.raise_for_status()
        return ExtractionManifest.model_validate(response.json())

    async def search_document_chunks(
        self,
        document_id: str,
        *,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> ChunkSearchResponse:
        response = await self.client.post(
            f"/api/documents/{document_id}/chunk-search",
            json={
                "query_embedding": query_embedding,
                "top_k": top_k if top_k is not None else settings.RAG_TOP_K,
            },
        )
        response.raise_for_status()
        return ChunkSearchResponse.model_validate(response.json())

    async def bulk_update_cells(
        self,
        table_id: str,
        results: list[CellUpdatePayload],
    ) -> BulkUpdateResponse:
        response = await self.client.post(
            f"/api/tables/{table_id}/cells/bulk-update",
            json={"results": [result.model_dump(mode="json") for result in results]},
        )
        response.raise_for_status()
        return BulkUpdateResponse.model_validate(response.json())

    async def aclose(self) -> None:
        await self.client.aclose()

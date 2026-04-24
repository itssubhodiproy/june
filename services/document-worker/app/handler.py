import asyncio
import logging
from dataclasses import dataclass

from app.clients.api_client import ApiClient
from app.clients.redis_client import RedisClient
from app.clients.s3_client import S3Client
from app.config import settings
from app.embedding.client import create_embedding_client
from app.parsing.chunker import DocumentChunker
from app.parsing.parser import create_parser
from app.types import (
    ChunkPayload,
    DocumentErrorEvent,
    DocumentParsingTask,
    DocumentProcessingEvent,
    DocumentReadyEvent,
)


@dataclass
class HandlerDependencies:
    redis: RedisClient
    s3: S3Client
    api: ApiClient


class DocumentProcessingError(Exception):
    def __init__(self, message: str, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class DocumentHandler:
    def __init__(self, deps: HandlerDependencies) -> None:
        self._deps = deps
        self._parser = create_parser()
        self._chunker = DocumentChunker()
        self._embedding = create_embedding_client()
        self._embed_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EMBEDS)

    async def handle(self, task: DocumentParsingTask) -> None:
        doc_id = task.document_id
        table_id = task.table_id

        await self._deps.redis.publish_processing(
            DocumentProcessingEvent(
                type="doc_processing", document_id=doc_id, table_id=table_id
            )
        )

        try:
            pdf_bytes = await asyncio.to_thread(self._deps.s3.download, task.file_key)

            parsed = await self._parser.parse(pdf_bytes)

            if not parsed.pages:
                raise DocumentProcessingError(
                    "Parser returned no pages", retryable=False
                )

            chunks = self._chunker.chunk(parsed)

            embeddings = await self._embed_chunks([c.text_content for c in chunks])

            chunk_payloads = [
                ChunkPayload(
                    chunk_index=c.chunk_index,
                    text_content=c.text_content,
                    page_number=c.page_number,
                    section=c.section,
                    bbox=c.bbox,
                    embedding=emb,
                )
                for c, emb in zip(chunks, embeddings)
            ]

            await self._deps.api.store_chunks(doc_id, chunk_payloads)

            await self._deps.api.update_document(
                doc_id,
                parse_status="ready",
                page_count=len(parsed.pages),
            )

            await self._deps.redis.publish_ready(
                DocumentReadyEvent(
                    type="doc_ready",
                    document_id=doc_id,
                    table_id=table_id,
                    page_count=len(parsed.pages),
                )
            )
        except DocumentProcessingError:
            raise
        except Exception as exc:
            logging.exception("Unexpected error processing document %s", doc_id)
            raise DocumentProcessingError(str(exc), retryable=True) from exc

    async def _embed_chunks(self, texts: list[str]) -> list[list[float]]:
        async with self._embed_semaphore:
            return await self._embedding.embed(texts)

    async def _handle_failure(
        self,
        document_id: str,
        table_id: str,
    ) -> None:
        await self._deps.api.update_document(
            document_id,
            parse_status="error",
        )

        await self._deps.redis.publish_error(
            DocumentErrorEvent(
                type="doc_error",
                document_id=document_id,
                table_id=table_id,
            )
        )

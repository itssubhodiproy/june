from app.clients.api_client import ApiClient
from app.config import settings
from app.embedding.client import EmbeddingClient, create_embedding_client
from app.rag.reranker import Reranker, create_reranker
from app.types import RAGContextResult, RetrievedChunk


class RAGPipeline:
    def __init__(
        self,
        api: ApiClient,
        *,
        embedding_client: EmbeddingClient | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self._api = api
        self._embedding_client = embedding_client or create_embedding_client()
        self._reranker = reranker or create_reranker()

    async def build_context(
        self,
        *,
        document_id: str,
        column_prompt: str,
    ) -> RAGContextResult:
        query_embedding = await self._embedding_client.embed_query(column_prompt)
        search_response = await self._api.search_document_chunks(
            document_id,
            query_embedding=query_embedding,
            top_k=settings.RAG_TOP_K,
        )
        retrieved_chunks = search_response.chunks

        if not retrieved_chunks:
            return RAGContextResult(
                chunks=[],
                context="[No relevant chunks returned]",
            )

        reranked_chunks = await self._reranker.rerank(
            query=column_prompt,
            chunks=retrieved_chunks,
            top_n=settings.RAG_RERANK_TOP_N,
        )

        context = self._format_context(reranked_chunks)
        return RAGContextResult(chunks=reranked_chunks, context=context)

    def _format_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "[No relevant chunks returned]"

        formatted_chunks: list[str] = []
        current_length = 0

        for chunk in chunks:
            section = chunk.section or "Unlabeled section"
            rendered = (
                f"[Chunk: {chunk.id} | Page {chunk.page_number}, {section}]\n"
                f"{chunk.text_content}"
            )

            next_length = current_length + len(rendered)
            if formatted_chunks and next_length > settings.RAG_MAX_CONTEXT_CHARS:
                break

            formatted_chunks.append(rendered)
            current_length = next_length + 2

        return "\n\n".join(formatted_chunks)

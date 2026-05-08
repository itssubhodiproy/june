from abc import ABC, abstractmethod

import cohere

from app.config import settings
from app.types import RetrievedChunk


class Reranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int,
    ) -> list[RetrievedChunk]:
        raise NotImplementedError


class CohereReranker(Reranker):
    def __init__(self) -> None:
        if not settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY is required when RERANK_PROVIDER=cohere")

        self._client = cohere.AsyncClientV2(api_key=settings.COHERE_API_KEY)
        self._model = settings.COHERE_RERANK_MODEL

    async def rerank(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        response = await self._client.rerank(
            model=self._model,
            query=query,
            documents=[chunk.text_content for chunk in chunks],
            top_n=min(top_n, len(chunks)),
        )

        reranked: list[RetrievedChunk] = []
        for result in response.results:
            reranked.append(chunks[result.index])

        return reranked


def create_reranker() -> Reranker:
    if settings.RERANK_PROVIDER == "cohere":
        return CohereReranker()

    raise ValueError(f"Unsupported rerank provider: {settings.RERANK_PROVIDER}")

from abc import ABC, abstractmethod

import cohere

from app.config import settings


class EmbeddingClient(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class CohereEmbeddingClient(EmbeddingClient):
    # Cohere v4 embed has a practical batch limit around 96 inputs per call.
    BATCH_SIZE = 96

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.COHERE_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.client = cohere.AsyncClientV2(api_key=self.api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[start : start + self.BATCH_SIZE]
            response = await self.client.embed(
                model=self.model,
                texts=batch,
                input_type="search_document",
                embedding_types=["float"],
                output_dimension=settings.EMBEDDING_DIMENSION,
            )
            embeddings.extend(response.embeddings.float)

        return embeddings


def create_embedding_client() -> EmbeddingClient:
    if settings.EMBEDDING_PROVIDER == "cohere":
        return CohereEmbeddingClient()
    raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")

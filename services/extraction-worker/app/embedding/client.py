from abc import ABC, abstractmethod

import cohere

from app.config import settings


class EmbeddingClient(ABC):
    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


class CohereEmbeddingClient(EmbeddingClient):
    def __init__(self) -> None:
        if not settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY is required when EMBEDDING_PROVIDER=cohere")

        self._client = cohere.AsyncClientV2(api_key=settings.COHERE_API_KEY)
        self._model = settings.EMBEDDING_MODEL

    async def embed_query(self, text: str) -> list[float]:
        response = await self._client.embed(
            model=self._model,
            texts=[text],
            input_type="search_query",
            embedding_types=["float"],
            output_dimension=settings.EMBEDDING_DIMENSION,
        )
        return response.embeddings.float[0]


def create_embedding_client() -> EmbeddingClient:
    if settings.EMBEDDING_PROVIDER == "cohere":
        return CohereEmbeddingClient()

    raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")

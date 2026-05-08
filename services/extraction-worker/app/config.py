from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    REDIS_URL: str
    API_SERVER_URL: str
    INTERNAL_SERVICE_TOKEN: str

    LLM_PROVIDER: str = "openai"
    RERANK_PROVIDER: str = "cohere"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str | None = None

    COHERE_API_KEY: str | None = None
    EMBEDDING_PROVIDER: str = "cohere"
    EMBEDDING_MODEL: str = "embed-v4.0"
    EMBEDDING_DIMENSION: int = 1536
    COHERE_RERANK_MODEL: str = "rerank-v3.5"

    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4096

    MAX_CONCURRENT_EXTRACTIONS: int = 20
    RAG_TOP_K: int = 10
    RAG_RERANK_TOP_N: int = 5
    RAG_MAX_CONTEXT_CHARS: int = 24000
    MAX_RETRIES: int = 3
    QUEUE_NAME: str = "extraction_tasks"


settings = Settings()

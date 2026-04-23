from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    REDIS_URL: str
    API_SERVER_URL: str
    INTERNAL_SERVICE_TOKEN: str = "dev-internal-service-token"

    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str

    PARSER: str = "liteparse"
    PARSER_DPI: int = 150

    EMBEDDING_PROVIDER: str = "cohere"
    COHERE_API_KEY: str
    EMBEDDING_MODEL: str = "embed-v4.0"
    EMBEDDING_DIMENSION: int = 1536

    MAX_CONCURRENT_PARSES: int = 1
    MAX_CONCURRENT_EMBEDS: int = 5
    MAX_RETRIES: int = 3
    QUEUE_NAME: str = "document_parsing"


settings = Settings()

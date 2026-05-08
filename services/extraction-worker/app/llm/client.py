from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings
from app.types import ParsedLLMResponse


class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> ParsedLLMResponse:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        self._client = AsyncOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
        )

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> ParsedLLMResponse:
        response = await self._client.chat.completions.parse(
            model=settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ParsedLLMResponse,
        )

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI structured response did not return parsed content")

        return parsed


def create_llm_client() -> LLMClient:
    if settings.LLM_PROVIDER == "openai":
        return OpenAIClient()

    raise NotImplementedError(
        f"LLM provider '{settings.LLM_PROVIDER}' is not implemented yet"
    )

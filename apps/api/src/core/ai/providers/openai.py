"""OpenAI Provider Implementation"""

import time
from typing import AsyncIterator, Optional

import httpx
from openai import AsyncOpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from ..config import ProviderDefaults, ProviderType, TokenConfig
from ..base import (
    BaseAIProvider,
    AIResponse,
    AIRequest,
    TokenUsage,
    CostInfo,
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    TokenLimitError,
    TimeoutError,
)


class OpenAIProvider(BaseAIProvider):
    provider_type = ProviderType.OPENAI
    supported_models = list(ProviderDefaults.OPENAI_MODELS.keys())

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = 'gpt-4o-mini',
        timeout: int = 60,
        max_retries: int = 3,
    ):
        super().__init__(api_key, base_url, model, timeout, max_retries)

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            max_retries=max_retries,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AIResponse:
        start_time = time.time()

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return self._parse_response(response, latency_ms)

        except Exception as e:
            return await self._handle_error(e, start_time, messages)

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise self._convert_error(e)

    async def count_tokens(self, text: str) -> int:
        try:
            encoding = await self._client.models.retrieve('gpt-4o')
            total = sum(len(text.split()) for _ in range(1))
            return int(len(text) / 4)
        except Exception:
            return int(len(text) / 4)

    async def validate_connection(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False

    def _parse_response(
        self,
        response: ChatCompletion,
        latency_ms: int,
    ) -> AIResponse:
        content = response.choices[0].message.content or ''

        usage = response.usage
        token_usage = TokenUsage(
            input_tokens=usage.prompt_tokens or 0,
            output_tokens=usage.completion_tokens or 0,
            total_tokens=usage.total_tokens or 0,
            cached_tokens=getattr(usage, 'prompt_tokens_details', {}).get('cached_tokens', 0) if hasattr(usage, 'prompt_tokens_details') else 0,
        )

        cost = self.calculate_cost(token_usage)

        self._request_count += 1
        self._total_tokens += token_usage.total_tokens
        self._total_cost += cost.total_cost

        return AIResponse(
            content=content,
            provider=self.provider_type.value,
            model=self.model,
            usage=token_usage,
            cost=cost,
            latency_ms=latency_ms,
            request_id=response.id,
            finish_reason=response.choices[0].finish_reason or 'stop',
            metadata={
                'system_fingerprint': getattr(response, 'system_fingerprint', None),
                'object': response.object,
            },
        )

    async def _handle_error(
        self,
        error: Exception,
        start_time: float,
        messages: list[dict[str, str]],
    ) -> AIResponse:
        latency_ms = int((time.time() - start_time) * 1000)
        raise self._convert_error(error)

    def _convert_error(self, error: Exception) -> AIProviderError:
        error_str = str(error).lower()

        if '401' in str(error) or 'authentication' in error_str:
            return AuthenticationError(str(error), self.provider_type.value)
        elif '429' in str(error) or 'rate' in error_str:
            retry_after = None
            if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                retry_after = error.response.headers.get('retry-after')
            return RateLimitError(str(error), self.provider_type.value, retry_after)
        elif '400' in str(error) and 'token' in error_str:
            return TokenLimitError(str(error), self.provider_type.value, self._estimate_max_tokens())
        elif 'timeout' in error_str:
            return TimeoutError(str(error), self.provider_type.value, self.timeout)
        else:
            return AIProviderError(
                message=str(error),
                provider=self.provider_type.value,
                error_type='unknown',
                retryable=True,
            )

    def _estimate_max_tokens(self) -> int:
        return TokenConfig.DEFAULT_MAX_TOKENS.get(self.model, 2048)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
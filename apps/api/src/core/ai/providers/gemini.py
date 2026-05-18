"""Gemini Provider Implementation"""

import time
from typing import AsyncIterator, Optional

import httpx

from ..config import ProviderDefaults
from ..base import (
    BaseAIProvider,
    AIResponse,
    TokenUsage,
    CostInfo,
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
)


class GeminiProvider(BaseAIProvider):
    provider_type = ProviderType.GEMINI
    supported_models = list(ProviderDefaults.GEMINI_MODELS.keys())

    def __init__(
        self,
        api_key: str,
        model: str = 'gemini-1.5-flash',
        timeout: int = 60,
        max_retries: int = 3,
    ):
        base_url = 'https://generativelanguage.googleapis.com/v1beta'
        super().__init__(api_key, base_url, model, timeout, max_retries)

        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            headers={'Content-Type': 'application/json'},
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
            contents = self._convert_messages(messages)

            payload = {
                'contents': contents,
                'generationConfig': {
                    'temperature': temperature,
                    'maxOutputTokens': max_tokens,
                    'topP': kwargs.get('top_p', 0.95),
                    'topK': kwargs.get('top_k', 40),
                },
            }

            if 'system_instruction' in kwargs:
                payload['systemInstruction'] = kwargs['system_instruction']

            url = f'/models/{self.model}:generateContent?key={self.api_key}'

            response = await self._client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            return self._parse_response(data, latency_ms)

        except Exception as e:
            raise self._convert_error(e, start_time)

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        contents = self._convert_messages(messages)

        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
                'topP': kwargs.get('top_p', 0.95),
            },
        }

        url = f'/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse'

        try:
            async with self._client.stream('POST', url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        data = line[5:].strip()
                        if data:
                            import json
                            chunk = json.loads(data)
                            if 'candidates' in chunk:
                                content = chunk['candidates'][0]['content']['parts'][0].get('text', '')
                                if content:
                                    yield content
        except Exception as e:
            raise self._convert_error(e, time.time())

    async def count_tokens(self, text: str) -> int:
        try:
            url = f'/models/{self.model}:countTokens?key={self.api_key}'
            payload = {'contents': [{'parts': [{'text': text}]}]}
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('totalTokens', int(len(text) / 4))
        except Exception:
            return int(len(text) / 4)

    async def validate_connection(self) -> bool:
        try:
            url = f'/v1beta/models?key={self.api_key}'
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[dict]:
        contents = []
        for msg in messages:
            role = msg.get('role', 'user')
            if role == 'system':
                role = 'user'

            contents.append({
                'role': 'user' if role == 'user' else 'model',
                'parts': [{'text': msg.get('content', '')}],
            })
        return contents

    def _parse_response(self, data: dict, latency_ms: int) -> AIResponse:
        candidates = data.get('candidates', [])
        if not candidates:
            raise AIProviderError('No response from Gemini', self.provider_type.value)

        content = candidates[0]['content']['parts'][0].get('text', '')

        usage = data.get('usageMetadata', {})
        token_usage = TokenUsage(
            input_tokens=usage.get('promptTokenCount', 0),
            output_tokens=usage.get('candidatesTokenCount', 0),
            total_tokens=usage.get('totalTokenCount', 0),
            cached_tokens=usage.get('cachedContentTokenCount', 0),
        )

        cost = self.calculate_cost(token_usage)

        self._request_count += 1
        self._total_tokens += token_usage.total_tokens
        self._total_cost += cost.total_cost

        finish_reason = candidates[0].get('finishReason', 'STOP')

        return AIResponse(
            content=content,
            provider=self.provider_type.value,
            model=self.model,
            usage=token_usage,
            cost=cost,
            latency_ms=latency_ms,
            request_id=data.get('modelVersion', f'gemini-{self.model}'),
            finish_reason=finish_reason,
            metadata=data.get('promptFeedback', {}),
        )

    def _convert_error(self, error: Exception, start_time: float = 0) -> AIProviderError:
        error_str = str(error).lower()
        status = getattr(error, 'response', None)

        if status and status.status_code == 401:
            return AuthenticationError(str(error), self.provider_type.value)
        elif status and status.status_code == 429:
            retry_after = status.headers.get('retry-after', 60)
            return RateLimitError(str(error), self.provider_type.value, int(retry_after))
        elif 'timeout' in error_str or status and status.status_code == 504:
            return TimeoutError(str(error), self.provider_type.value, self.timeout)
        else:
            return AIProviderError(
                message=str(error),
                provider=self.provider_type.value,
                error_type='api_error',
                retryable=True,
            )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
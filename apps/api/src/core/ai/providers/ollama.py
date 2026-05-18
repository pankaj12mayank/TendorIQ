"""Ollama Provider for Local LLM Running"""

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
    TimeoutError,
)


class OllamaProvider(BaseAIProvider):
    provider_type = ProviderType.OLLAMA
    supported_models = list(ProviderDefaults.OLLAMA_MODELS.keys())

    def __init__(
        self,
        base_url: str = 'http://localhost:11434',
        model: str = 'llama3',
        timeout: int = 120,
        max_retries: int = 3,
    ):
        super().__init__(api_key=None, base_url=base_url, model=model, timeout=timeout, max_retries=max_retries)

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
            payload = {
                'model': self.model,
                'messages': self._convert_messages(messages),
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens,
                    'top_p': kwargs.get('top_p', 0.9),
                    'top_k': kwargs.get('top_k', 40),
                    'repeat_penalty': kwargs.get('repeat_penalty', 1.1),
                },
                'stream': False,
            }

            if 'system' in kwargs:
                payload['system'] = kwargs['system']

            response = await self._client.post('/api/chat', json=payload)
            response.raise_for_status()

            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            return self._parse_response(data, latency_ms)

        except Exception as e:
            raise self._convert_error(e)

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        payload = {
            'model': self.model,
            'messages': self._convert_messages(messages),
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens,
            },
            'stream': True,
        }

        try:
            async with self._client.stream('POST', '/api/chat', json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                yield chunk['message']['content']
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise self._convert_error(e)

    async def count_tokens(self, text: str) -> int:
        try:
            payload = {
                'model': self.model,
                'prompt': text,
            }
            response = await self._client.post('/api/tokens', json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get('tokens', len(text.split()))
        except Exception:
            return len(text.split())

    async def validate_connection(self) -> bool:
        try:
            response = await self._client.get('/api/tags')
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        try:
            response = await self._client.get('/api/tags')
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except Exception:
            return []

    async def pull_model(self, model: str) -> dict:
        payload = {'name': model}
        try:
            async with self._client.stream('POST', '/api/pull', json=payload) as response:
                status = {'downloading': False, 'progress': 0}
                async for line in response.aiter_lines():
                    if line:
                        import json
                        chunk = json.loads(line)
                        status.update(chunk)
                return status
        except Exception as e:
            raise AIProviderError(f'Failed to pull model: {e}', self.provider_type.value)

    def _convert_messages(self, messages: list[dict[str, str]]) -> list[dict]:
        converted = []
        for msg in messages:
            role = msg.get('role', 'user')
            if role == 'system':
                converted.append({'role': 'system', 'content': msg.get('content', '')})
            elif role in ('user', 'assistant'):
                converted.append({'role': role, 'content': msg.get('content', '')})
            else:
                converted.append({'role': 'user', 'content': msg.get('content', '')})
        return converted

    def _parse_response(self, data: dict, latency_ms: int) -> AIResponse:
        message = data.get('message', {})
        content = message.get('content', '')

        eval_count = data.get('eval_count', 0)
        prompt_count = data.get('prompt_eval_count', 0)

        token_usage = TokenUsage(
            input_tokens=prompt_count,
            output_tokens=eval_count,
            total_tokens=prompt_count + eval_count,
            cached_tokens=0,
        )

        cost = CostInfo(input_cost=0, output_cost=0, total_cost=0, currency='local')

        self._request_count += 1
        self._total_tokens += token_usage.total_tokens

        return AIResponse(
            content=content,
            provider=self.provider_type.value,
            model=self.model,
            usage=token_usage,
            cost=cost,
            latency_ms=latency_ms,
            request_id=data.get('model', self.model),
            finish_reason='stop' if data.get('done', True) else 'length',
            metadata={
                'done_reason': data.get('done_reason'),
                'total_duration': data.get('total_duration'),
                'load_duration': data.get('load_duration'),
            },
        )

    def _convert_error(self, error: Exception) -> AIProviderError:
        error_str = str(error).lower()

        if 'connection' in error_str or 'refused' in error_str:
            return AIProviderError(
                message='Ollama server not running. Please start with: ollama serve',
                provider=self.provider_type.value,
                error_type='connection',
                retryable=False,
            )
        elif 'timeout' in error_str:
            return TimeoutError(str(error), self.provider_type.value, self.timeout)
        elif '404' in str(error):
            return AIProviderError(
                message=f'Model {self.model} not found. Run: ollama pull {self.model}',
                provider=self.provider_type.value,
                error_type='model_not_found',
                retryable=True,
            )
        else:
            return AIProviderError(
                message=str(error),
                provider=self.provider_type.value,
                error_type='unknown',
                retryable=True,
            )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
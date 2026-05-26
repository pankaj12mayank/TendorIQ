"""AI Service - Unified Interface for All Providers"""

import asyncio
import logging
import time
from typing import Optional, TypeVar
from uuid import UUID, uuid4

from .config import ProviderType, ModelCapability
from .base import (
    BaseAIProvider,
    AIResponse,
    AIRequest,
    TokenUsage,
    CostInfo,
    AIProviderError,
)
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider
from .providers.ollama import OllamaProvider
from .accounting import TokenAccountant, CostCalculator, TokenCounter
from .errors import RetryHandler, CircuitBreaker, FallbackManager, with_retry


logger = logging.getLogger(__name__)

T = TypeVar('T')


class AIServiceConfig:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        ollama_base_url: str = 'http://localhost:11434',
        default_provider: ProviderType = ProviderType.OPENAI,
        default_model: str = 'gpt-4o-mini',
        max_retries: int = 3,
        timeout: int = 60,
    ):
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.ollama_base_url = ollama_base_url
        self.default_provider = default_provider
        self.default_model = default_model
        self.max_retries = max_retries
        self.timeout = timeout


class AIService:
    def __init__(self, config: Optional[AIServiceConfig] = None):
        self.config = config or AIServiceConfig()
        self._providers: dict[ProviderType, BaseAIProvider] = {}
        self._token_accountant = TokenAccountant()
        self._retry_handler = RetryHandler(max_retries=self.config.max_retries)
        self._circuit_breakers: dict[ProviderType, CircuitBreaker] = {}
        self._fallback_manager: Optional[FallbackManager] = None

        for ptype in ProviderType:
            self._circuit_breakers[ptype] = CircuitBreaker()

    def _get_provider(self, provider_type: Optional[ProviderType] = None) -> BaseAIProvider:
        ptype = provider_type or self.config.default_provider

        if ptype not in self._providers:
            self._providers[ptype] = self._create_provider(ptype)

        return self._providers[ptype]

    def _create_provider(self, provider_type: ProviderType) -> BaseAIProvider:
        if provider_type == ProviderType.OPENAI:
            if not self.config.openai_api_key:
                raise AIProviderError('OpenAI API key not configured', ProviderType.OPENAI.value)
            return OpenAIProvider(
                api_key=self.config.openai_api_key,
                model=self.config.default_model if 'gpt' in self.config.default_model else 'gpt-4o-mini',
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        elif provider_type == ProviderType.GEMINI:
            if not self.config.gemini_api_key:
                raise AIProviderError('Gemini API key not configured', ProviderType.GEMINI.value)
            return GeminiProvider(
                api_key=self.config.gemini_api_key,
                model='gemini-1.5-flash',
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        elif provider_type == ProviderType.OLLAMA:
            return OllamaProvider(
                base_url=self.config.ollama_base_url,
                model='llama3',
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
        else:
            raise AIProviderError(f'Unknown provider: {provider_type}', 'unknown')

    async def complete(
        self,
        messages: list[dict[str, str]],
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        **kwargs,
    ) -> AIResponse:
        provider_instance = self._get_provider(provider)

        if model:
            provider_instance.model = model

        start_time = time.time()
        request_id = str(uuid4())

        try:
            breaker = self._circuit_breakers.get(provider_instance.provider_type)
            if breaker and not breaker.can_execute():
                if fallback := self._get_fallback_provider(provider_instance.provider_type):
                    provider_instance = fallback
                    logger.info(f'Falling back to {provider_instance.provider_type.value}')
                    breaker = self._circuit_breakers.get(provider_instance.provider_type)

            response = await self._retry_handler.execute_with_retry(
                provider_instance.complete,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                error_context=f'request:{request_id}',
                **kwargs,
            )

            if breaker:
                breaker.record_success()

            await self._token_accountant.track_usage(
                user_id=user_id,
                tenant_id=tenant_id,
                provider=response.provider,
                model=response.model,
                usage=response.usage,
                cost=response.cost,
                request_id=request_id,
            )

            logger.info(
                f'AI completion successful',
                extra={
                    'request_id': request_id,
                    'provider': response.provider,
                    'model': response.model,
                    'latency_ms': response.latency_ms,
                    'cost': response.cost.total_cost,
                }
            )

            return response

        except Exception as e:
            if breaker:
                breaker.record_failure()
            logger.error(f'AI completion failed: {e}', extra={'request_id': request_id})
            raise

    async def complete_with_fallback(
        self,
        messages: list[dict[str, str]],
        primary_provider: ProviderType,
        fallback_provider: ProviderType,
        **kwargs,
    ) -> AIResponse:
        primary = self._get_provider(primary_provider)

        try:
            return await self.complete(messages, provider=primary_provider, **kwargs)
        except Exception as e:
            logger.warning(f'Primary provider {primary_provider.value} failed: {e}')

            fallback = self._get_provider(fallback_provider)
            logger.info(f'Falling back to {fallback_provider.value}')

            return await self.complete(messages, provider=fallback_provider, **kwargs)

    async def stream(
        self,
        messages: list[dict[str, str]],
        provider: Optional[ProviderType] = None,
        **kwargs,
    ):
        provider_instance = self._get_provider(provider)
        return provider_instance.stream(messages, **kwargs)

    async def validate_provider(self, provider: ProviderType) -> dict:
        provider_instance = self._get_provider(provider)
        is_valid = await provider_instance.validate_connection()

        return {
            'provider': provider.value,
            'available': is_valid,
            'model': provider_instance.model,
            'stats': provider_instance.get_stats(),
        }

    async def get_available_providers(self) -> list[dict]:
        providers = []
        for ptype in ProviderType:
            try:
                status = await self.validate_provider(ptype)
                providers.append(status)
            except Exception as e:
                providers.append({
                    'provider': ptype.value,
                    'available': False,
                    'error': str(e),
                })
        return providers

    def _get_fallback_provider(self, failed_provider: ProviderType) -> Optional[BaseAIProvider]:
        fallback_order = {
            ProviderType.OPENAI: [ProviderType.GEMINI, ProviderType.OLLAMA],
            ProviderType.GEMINI: [ProviderType.OPENAI, ProviderType.OLLAMA],
            ProviderType.OLLAMA: [ProviderType.OPENAI, ProviderType.GEMINI],
        }

        candidates = fallback_order.get(failed_provider, [])
        for candidate in candidates:
            breaker = self._circuit_breakers.get(candidate)
            if breaker and breaker.can_execute():
                return self._get_provider(candidate)

        return None

    async def estimate_cost(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[ProviderType] = None,
    ) -> CostInfo:
        model = model or self.config.default_model
        tokens = TokenCounter.estimate_tokens(text, model)
        return CostCalculator.calculate(model, tokens, tokens)

    async def get_usage_stats(
        self,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
    ) -> dict:
        if user_id and tenant_id:
            return await self._token_accountant.get_user_usage(user_id, tenant_id)
        elif tenant_id:
            return await self._token_accountant.get_tenant_usage(tenant_id)
        else:
            stats = {'providers': {}}
            for ptype, provider in self._providers.items():
                stats['providers'][ptype.value] = provider.get_stats()
            return stats

    async def set_spending_limit(self, tenant_id: UUID, monthly_limit: float) -> None:
        await self._token_accountant.set_spending_limit(tenant_id, monthly_limit)

    async def check_spending_limit(self, tenant_id: UUID, user_id: Optional[UUID] = None) -> dict:
        return await self._token_accountant.check_spending_limit(tenant_id, user_id)


ai_service = AIService()


def get_ai_service() -> AIService:
    return ai_service


async def init_ai_service(
    openai_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    ollama_base_url: str = 'http://localhost:11434',
) -> AIService:
    global ai_service
    ai_service = AIService(AIServiceConfig(
        openai_api_key=openai_api_key,
        gemini_api_key=gemini_api_key,
        ollama_base_url=ollama_base_url,
    ))
    return ai_service
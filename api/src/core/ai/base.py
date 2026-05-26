"""Base AI Provider Interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from .config import ProviderType, ModelCapability


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'cached_tokens': self.cached_tokens,
        }


@dataclass
class CostInfo:
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = 'USD'

    def to_dict(self) -> dict:
        return {
            'input_cost': round(self.input_cost, 6),
            'output_cost': round(self.output_cost, 6),
            'total_cost': round(self.total_cost, 6),
            'currency': self.currency,
        }


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    usage: TokenUsage
    cost: CostInfo
    latency_ms: int
    request_id: str
    finish_reason: str = 'stop'
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'content': self.content,
            'provider': self.provider,
            'model': self.model,
            'usage': self.usage.to_dict(),
            'cost': self.cost.to_dict(),
            'latency_ms': self.latency_ms,
            'request_id': self.request_id,
            'finish_reason': self.finish_reason,
            'metadata': self.metadata,
        }


@dataclass
class AIRequest:
    messages: list[dict[str, str]]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: Optional[float] = None
    stop: Optional[list[str]] = None
    stream: bool = False
    timeout: int = 60
    capabilities_required: list[ModelCapability] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProviderError(Exception):
    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str = 'unknown',
        retryable: bool = True,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.provider = provider
        self.error_type = error_type
        self.retryable = retryable
        self.details = details or {}
        super().__init__(self.message)


class RateLimitError(AIProviderError):
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type='rate_limit',
            retryable=True,
            details={'retry_after': retry_after},
        )


class AuthenticationError(AIProviderError):
    def __init__(self, message: str, provider: str):
        super().__init__(
            message=message,
            provider=provider,
            error_type='authentication',
            retryable=False,
        )


class TokenLimitError(AIProviderError):
    def __init__(self, message: str, provider: str, max_tokens: int):
        super().__init__(
            message=message,
            provider=provider,
            error_type='token_limit',
            retryable=False,
            details={'max_tokens': max_tokens},
        )


class TimeoutError(AIProviderError):
    def __init__(self, message: str, provider: str, timeout: int):
        super().__init__(
            message=message,
            provider=provider,
            error_type='timeout',
            retryable=True,
            details={'timeout': timeout},
        )


class BaseAIProvider(ABC):
    provider_type: ProviderType = ProviderType.OPENAI
    supported_models: list[str] = []

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = 'gpt-4o',
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AIResponse:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ):
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        pass

    def calculate_cost(self, usage: TokenUsage) -> CostInfo:
        from .config import TokenConfig
        costs = TokenConfig.COST_PER_1K_TOKENS.get(self.model, {'input': 0.0, 'output': 0.0})
        input_cost = (usage.input_tokens / 1000) * costs.get('input', 0)
        output_cost = (usage.output_tokens / 1000) * costs.get('output', 0)
        return CostInfo(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
        )

    def get_stats(self) -> dict:
        return {
            'provider': self.provider_type.value,
            'model': self.model,
            'request_count': self._request_count,
            'total_tokens': self._total_tokens,
            'total_cost': round(self._total_cost, 6),
        }

    def reset_stats(self) -> None:
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0
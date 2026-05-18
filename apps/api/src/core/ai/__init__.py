"""AI Module - Provider Abstraction Layer

Provides unified interface for:
- OpenAI
- Gemini
- Ollama (local)

Features:
- Provider switching
- Fallback support
- Token tracking
- Cost tracking
- Circuit breakers
- Retry logic
"""

from .config import (
    ProviderType,
    ModelCapability,
    AIProviderConfig,
    ProviderDefaults,
    ProviderSelection,
    TokenConfig,
)
from .base import (
    TokenUsage,
    CostInfo,
    AIResponse,
    AIRequest,
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    TokenLimitError,
    TimeoutError,
)
from .service import (
    AIService,
    AIServiceConfig,
    ai_service,
    get_ai_service,
    init_ai_service,
)
from .accounting import (
    TokenAccountant,
    CostCalculator,
    TokenCounter,
)
from .errors import (
    RetryHandler,
    RetryConfig,
    CircuitBreaker,
    FallbackManager,
    with_retry,
    ErrorClassifier,
)
from .providers import (
    OpenAIProvider,
    GeminiProvider,
    OllamaProvider,
)


__all__ = [
    'ProviderType',
    'ModelCapability',
    'AIProviderConfig',
    'ProviderDefaults',
    'ProviderSelection',
    'TokenConfig',
    'TokenUsage',
    'CostInfo',
    'AIResponse',
    'AIRequest',
    'AIProviderError',
    'RateLimitError',
    'AuthenticationError',
    'TokenLimitError',
    'TimeoutError',
    'AIService',
    'AIServiceConfig',
    'ai_service',
    'get_ai_service',
    'init_ai_service',
    'TokenAccountant',
    'CostCalculator',
    'TokenCounter',
    'RetryHandler',
    'RetryConfig',
    'CircuitBreaker',
    'FallbackManager',
    'with_retry',
    'ErrorClassifier',
    'OpenAIProvider',
    'GeminiProvider',
    'OllamaProvider',
]
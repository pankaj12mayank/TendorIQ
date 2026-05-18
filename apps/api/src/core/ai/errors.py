"""Error Handling and Retry Logic"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Optional, TypeVar, Any

from .base import AIProviderError, RateLimitError, TimeoutError, AuthenticationError, TokenLimitError
from .config import ProviderType

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    DEFAULT_DELAYS = {
        'rate_limit': [1, 2, 5, 10, 30],
        'timeout': [1, 2, 5, 10],
        'server_error': [1, 2, 5, 15, 30],
        'connection': [1, 2, 5, 10, 30],
        'default': [1, 2, 5, 15, 30, 60],
    }

    @classmethod
    def get_delays(cls, error_type: str) -> list[int]:
        return cls.DEFAULT_DELAYS.get(error_type, cls.DEFAULT_DELAYS['default'])


class RetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def calculate_delay(self, attempt: int, error_type: str = 'default') -> float:
        delays = RetryConfig.get_delays(error_type)
        if attempt < len(delays):
            delay = delays[attempt]
        else:
            delay = delays[-1] * (self.exponential_base ** (attempt - len(delays)))

        jitter = delay * 0.1 * (0.5 + (time.time() % 1))
        return min(delay + jitter, self.max_delay)

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        error_context: Optional[str] = None,
        **kwargs,
    ) -> T:
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except RateLimitError as e:
                last_error = e
                error_type = 'rate_limit'
                if not e.retryable or attempt >= self.max_retries:
                    raise

                delay = self.calculate_delay(attempt, error_type)
                retry_after = e.details.get('retry_after')
                if retry_after:
                    delay = max(delay, retry_after)

                logger.warning(
                    f'Rate limit hit (attempt {attempt + 1}/{self.max_retries + 1}). '
                    f'Retrying in {delay:.1f}s. Context: {error_context}'
                )
                await asyncio.sleep(delay)

            except TimeoutError as e:
                last_error = e
                error_type = 'timeout'
                if not e.retryable or attempt >= self.max_retries:
                    raise

                delay = self.calculate_delay(attempt, error_type)
                logger.warning(
                    f'Timeout (attempt {attempt + 1}/{self.max_retries + 1}). '
                    f'Retrying in {delay:.1f}s. Context: {error_context}'
                )
                await asyncio.sleep(delay)

            except AuthenticationError:
                raise last_error or AuthenticationError('Authentication failed', 'unknown')

            except TokenLimitError:
                raise last_error or TokenLimitError('Token limit exceeded', 'unknown', 0)

            except AIProviderError as e:
                last_error = e
                if not e.retryable or attempt >= self.max_retries:
                    raise

                error_type = e.error_type
                delay = self.calculate_delay(attempt, error_type)
                logger.warning(
                    f'Provider error: {e.message} (attempt {attempt + 1}/{self.max_retries + 1}). '
                    f'Retrying in {delay:.1f}s. Context: {error_context}'
                )
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f'Unexpected error: {e}. Context: {error_context}')
                raise

        if last_error:
            raise last_error
        raise AIProviderError('Max retries exceeded', 'unknown')


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    error_context: Optional[str] = None,
):
    handler = RetryHandler(max_retries=max_retries, base_delay=base_delay)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await handler.execute_with_retry(
                func, *args, error_context=error_context or func.__name__, **kwargs
            )
        return wrapper
    return decorator


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = 'closed'
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        if self._state == 'half_open':
            return 'half_open'

        if self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed > self.recovery_timeout:
                self._state = 'half_open'
                self._half_open_calls = 0

        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = 'closed'

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._state = 'open'
            logger.warning(f'Circuit breaker opened after {self._failure_count} failures')

    def can_execute(self) -> bool:
        current_state = self.state

        if current_state == 'closed':
            return True
        elif current_state == 'open':
            return False
        elif current_state == 'half_open':
            return self._half_open_calls < self.half_open_max_calls

        return False

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        if not self.can_execute():
            raise AIProviderError(
                'Circuit breaker is open',
                'unknown',
                error_type='circuit_breaker',
                retryable=True,
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class ErrorClassifier:
    @staticmethod
    def classify(error: Exception) -> str:
        error_str = str(error).lower()

        if '429' in str(error) or 'rate' in error_str or 'quota' in error_str:
            return 'rate_limit'
        elif '401' in str(error) or 'auth' in error_str or 'api key' in error_str:
            return 'authentication'
        elif '400' in str(error) and ('token' in error_str or 'limit' in error_str):
            return 'token_limit'
        elif 'timeout' in error_str or '504' in str(error):
            return 'timeout'
        elif '500' in str(error) or '502' in str(error) or '503' in str(error):
            return 'server_error'
        elif 'connection' in error_str or 'network' in error_str:
            return 'connection'
        else:
            return 'unknown'


class FallbackManager:
    def __init__(self, providers: list[dict]):
        self.providers = providers
        self._circuit_breakers: dict[str, CircuitBreaker] = {}

        for provider in providers:
            self._circuit_breakers[provider['type']] = CircuitBreaker()

    async def execute_with_fallback(
        self,
        func: Callable,
        *args,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> Any:
        providers = self._get_ordered_providers(preferred_provider)
        last_error: Optional[Exception] = None

        for provider in providers:
            provider_type = provider['type']
            breaker = self._circuit_breakers.get(provider_type)

            if breaker and not breaker.can_execute():
                logger.warning(f'Skipping provider {provider_type}: circuit breaker open')
                continue

            try:
                result = await func(provider, *args, **kwargs)
                if breaker:
                    breaker.record_success()
                return result
            except RateLimitError as e:
                logger.warning(f'Rate limit on {provider_type}, trying next provider')
                if breaker:
                    breaker.record_failure()
                last_error = e
                continue
            except TimeoutError as e:
                logger.warning(f'Timeout on {provider_type}, trying next provider')
                if breaker:
                    breaker.record_failure()
                last_error = e
                continue
            except AuthenticationError as e:
                logger.error(f'Authentication error on {provider_type}: {e}')
                last_error = e
                break
            except Exception as e:
                logger.error(f'Error on {provider_type}: {e}')
                if breaker:
                    breaker.record_failure()
                last_error = e
                continue

        if last_error:
            raise last_error
        raise AIProviderError('All providers failed', 'unknown')

    def _get_ordered_providers(self, preferred: Optional[str] = None) -> list[dict]:
        if not preferred:
            return self.providers

        sorted_providers = []
        for p in self.providers:
            if p['type'] == preferred:
                sorted_providers.insert(0, p)
            else:
                sorted_providers.append(p)
        return sorted_providers
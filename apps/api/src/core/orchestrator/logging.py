"""AI Observability and Logging System"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class AIObservationType(str, Enum):
    REQUEST = 'request'
    RESPONSE = 'response'
    CHAIN_STEP = 'chain_step'
    ERROR = 'error'
    RETRY = 'retry'
    FALLBACK = 'fallback'
    VALIDATION = 'validation'
    HALLUCINATION = 'hallucination'


class AIObservation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observation_type: str
    trace_id: str
    span_id: Optional[str] = None

    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None

    provider: Optional[str] = None
    model: Optional[str] = None

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    latency_ms: int = 0
    cost: float = 0.0

    request_data: Optional[dict] = None
    response_data: Optional[dict] = None
    metadata: dict = Field(default_factory=dict)

    error: Optional[str] = None
    error_type: Optional[str] = None

    tags: list[str] = Field(default_factory=list)


class TraceContext:
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid4())
        self.spans: list[dict] = []
        self._start_time = datetime.now(timezone.utc)

    def start_span(self, name: str) -> str:
        span_id = str(uuid4())
        self.spans.append({
            'span_id': span_id,
            'name': name,
            'start_time': datetime.now(timezone.utc).isoformat(),
            'events': [],
        })
        return span_id

    def end_span(self, span_id: str, metadata: Optional[dict] = None) -> None:
        for span in self.spans:
            if span['span_id'] == span_id:
                span['end_time'] = datetime.now(timezone.utc).isoformat()
                if metadata:
                    span['metadata'] = metadata
                break

    def add_event(self, span_id: str, event_name: str, data: Optional[dict] = None) -> None:
        for span in self.spans:
            if span['span_id'] == span_id:
                span['events'].append({
                    'name': event_name,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data,
                })
                break

    def to_dict(self) -> dict:
        return {
            'trace_id': self.trace_id,
            'duration_ms': int((datetime.now(timezone.utc) - self._start_time).total_seconds() * 1000),
            'spans': self.spans,
        }


class AILogger:
    def __init__(self, redis_pool=None):
        self._redis = redis_pool
        self._observations: list[AIObservation] = []
        self._traces: dict[str, TraceContext] = {}

    async def log_request(
        self,
        messages: list[dict],
        provider: str,
        model: str,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        request_id = str(uuid4())
        trace_id = trace_id or str(uuid4())

        observation = AIObservation(
            observation_type=AIObservationType.REQUEST.value,
            trace_id=trace_id,
            user_id=str(user_id) if user_id else None,
            tenant_id=str(tenant_id) if tenant_id else None,
            provider=provider,
            model=model,
            request_data={'messages': messages, **kwargs},
            metadata={'request_id': request_id},
        )

        await self._save_observation(observation)
        return request_id

    async def log_response(
        self,
        request_id: str,
        content: str,
        provider: str,
        model: str,
        usage: dict,
        cost: float,
        latency_ms: int,
        trace_id: Optional[str] = None,
        validation: Optional[dict] = None,
        hallucination: Optional[dict] = None,
        **kwargs,
    ) -> None:
        observation = AIObservation(
            observation_type=AIObservationType.RESPONSE.value,
            trace_id=trace_id or 'unknown',
            provider=provider,
            model=model,
            prompt_tokens=usage.get('input_tokens', 0),
            completion_tokens=usage.get('output_tokens', 0),
            total_tokens=usage.get('total_tokens', 0),
            latency_ms=latency_ms,
            cost=cost,
            response_data={'content': content, **kwargs},
            metadata={
                'validation': validation,
                'hallucination': hallucination,
            },
        )

        await self._save_observation(observation)

    async def log_chain_step(
        self,
        chain_id: str,
        step_name: str,
        step_type: str,
        input_data: Any,
        output_data: Any,
        latency_ms: int,
        success: bool,
        error: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        observation = AIObservation(
            observation_type=AIObservationType.CHAIN_STEP.value,
            trace_id=trace_id or chain_id,
            request_data={'step_name': step_name, 'step_type': step_type, 'input': input_data},
            response_data={'output': output_data},
            latency_ms=latency_ms,
            metadata={'chain_id': chain_id, 'success': success, **kwargs},
            error=error,
        )

        await self._save_observation(observation)

    async def log_error(
        self,
        error: Exception,
        provider: str,
        context: dict,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        error_type = type(error).__name__

        observation = AIObservation(
            observation_type=AIObservationType.ERROR.value,
            trace_id=trace_id or 'unknown',
            provider=provider,
            error=str(error),
            error_type=error_type,
            metadata={'context': context, **kwargs},
        )

        await self._save_observation(observation)

    async def log_retry(
        self,
        attempt: int,
        max_retries: int,
        error: str,
        provider: str,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        observation = AIObservation(
            observation_type=AIObservationType.RETRY.value,
            trace_id=trace_id or 'unknown',
            provider=provider,
            error=error,
            metadata={'attempt': attempt, 'max_retries': max_retries, **kwargs},
        )

        await self._save_observation(observation)

    async def log_fallback(
        self,
        from_provider: str,
        to_provider: str,
        reason: str,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        observation = AIObservation(
            observation_type=AIObservationType.FALLBACK.value,
            trace_id=trace_id or 'unknown',
            provider=from_provider,
            metadata={
                'fallback_from': from_provider,
                'fallback_to': to_provider,
                'reason': reason,
                **kwargs,
            },
        )

        await self._save_observation(observation)

    async def _save_observation(self, observation: AIObservation) -> None:
        self._observations.append(observation)

        if len(self._observations) > 1000:
            self._observations = self._observations[-500:]

        if self._redis:
            key = f'ai:logs:{observation.tenant_id or "global"}:{datetime.now(timezone.utc).strftime("%Y-%m-%d")}'
            await self._redis.lpush(key, observation.model_dump_json(), default=str)
            await self._redis.expire(key, 86400 * 30)

        logger.debug(f'AI Observation logged: {observation.observation_type}', extra={
            'trace_id': observation.trace_id,
            'provider': observation.provider,
        })

    async def get_trace(self, trace_id: str) -> Optional[dict]:
        if self._redis:
            pattern = f'ai:logs:*:{trace_id}*'
            cursor = 0
            observations = []
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    items = await self._redis.lrange(key, 0, -1)
                    for item in items:
                        obs = json.loads(item)
                        if obs.get('trace_id') == trace_id:
                            observations.append(obs)
                if cursor == 0:
                    break

            return {
                'trace_id': trace_id,
                'observations': sorted(observations, key=lambda x: x['timestamp']),
            }

        return None

    async def get_recent_observations(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        if self._redis:
            key = f'ai:logs:{tenant_id or "global"}:{datetime.now(timezone.utc).strftime("%Y-%m-%d")}'
            items = await self._redis.lrange(key, 0, limit - 1)
            return [json.loads(item) for item in items]

        return [obs.model_dump() for obs in self._observations[-limit:]]

    async def get_analytics(
        self,
        tenant_id: Optional[str] = None,
        hours: int = 24,
    ) -> dict:
        observations = await self.get_recent_observations(tenant_id, 10000)

        total_requests = 0
        total_cost = 0.0
        total_tokens = 0
        errors = 0
        by_provider = {}

        for obs in observations:
            if obs.get('observation_type') == AIObservationType.REQUEST.value:
                total_requests += 1
                provider = obs.get('provider', 'unknown')
                if provider not in by_provider:
                    by_provider[provider] = {'requests': 0, 'cost': 0, 'tokens': 0}
                by_provider[provider]['requests'] += 1

            if obs.get('cost'):
                total_cost += obs['cost']
            if obs.get('total_tokens'):
                total_tokens += obs['total_tokens']
            if obs.get('error'):
                errors += 1

            if obs.get('provider'):
                if obs['provider'] not in by_provider:
                    by_provider[obs['provider']] = {'requests': 0, 'cost': 0, 'tokens': 0, 'errors': 0}
                if obs.get('cost'):
                    by_provider[obs['provider']]['cost'] += obs['cost']
                if obs.get('total_tokens'):
                    by_provider[obs['provider']]['tokens'] += obs['total_tokens']
                if obs.get('error'):
                    by_provider[obs['provider']]['errors'] = by_provider[obs['provider']].get('errors', 0) + 1

        return {
            'period_hours': hours,
            'total_requests': total_requests,
            'total_cost': round(total_cost, 6),
            'total_tokens': total_tokens,
            'error_rate': round(errors / max(1, total_requests) * 100, 2),
            'by_provider': by_provider,
            'avg_cost_per_request': round(total_cost / max(1, total_requests), 6),
        }

    def create_trace(self) -> TraceContext:
        trace = TraceContext()
        self._traces[trace.trace_id] = trace
        return trace


class MetricsCollector:
    @staticmethod
    def collect(
        provider: str,
        model: str,
        usage: dict,
        cost: float,
        latency_ms: int,
    ) -> dict:
        return {
            'provider': provider,
            'model': model,
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0),
            'cost': cost,
            'latency_ms': latency_ms,
            'tokens_per_second': (usage.get('output_tokens', 0) / max(1, latency_ms / 1000)),
            'cost_per_token': cost / max(1, usage.get('total_tokens', 1)),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def aggregate(metrics: list[dict]) -> dict:
        if not metrics:
            return {}

        total_input = sum(m.get('input_tokens', 0) for m in metrics)
        total_output = sum(m.get('output_tokens', 0) for m in metrics)
        total_cost = sum(m.get('cost', 0) for m in metrics)
        total_latency = sum(m.get('latency_ms', 0) for m in metrics)

        return {
            'count': len(metrics),
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'total_tokens': total_input + total_output,
            'total_cost': round(total_cost, 6),
            'avg_latency_ms': total_latency // len(metrics),
            'avg_cost': round(total_cost / len(metrics), 6),
            'avg_tokens_per_request': (total_input + total_output) // len(metrics),
        }
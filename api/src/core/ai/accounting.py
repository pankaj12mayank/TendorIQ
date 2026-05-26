"""Token accounting and cost tracking (in-memory; no Redis)."""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from .config import TokenConfig, ProviderType
from .base import TokenUsage, CostInfo


class TokenAccountant:
    def __init__(self, redis_pool=None):
        self._local_cache: dict[str, dict] = {}

    async def track_usage(
        self,
        user_id: Optional[UUID],
        tenant_id: Optional[UUID],
        provider: str,
        model: str,
        usage: TokenUsage,
        cost: CostInfo,
        request_id: str,
    ) -> dict:
        record = {
            'id': str(uuid4()),
            'user_id': str(user_id) if user_id else None,
            'tenant_id': str(tenant_id) if tenant_id else None,
            'provider': provider,
            'model': model,
            'input_tokens': usage.input_tokens,
            'output_tokens': usage.output_tokens,
            'total_tokens': usage.total_tokens,
            'cost': cost.total_cost,
            'currency': cost.currency,
            'request_id': request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        self._local_cache[record['id']] = record
        return record

    async def get_user_usage(
        self,
        user_id: UUID,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        return self._get_usage_from_cache(user_id, tenant_id, start_date, end_date)

    def _get_usage_from_cache(
        self,
        user_id: UUID,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        filtered = [
            r
            for r in self._local_cache.values()
            if r.get('user_id') == str(user_id)
            and r.get('tenant_id') == str(tenant_id)
            and start_date <= datetime.fromisoformat(r['timestamp']) <= end_date
        ]

        total_input = sum(r['input_tokens'] for r in filtered)
        total_output = sum(r['output_tokens'] for r in filtered)
        total_cost = sum(r['cost'] for r in filtered)

        return {
            'user_id': str(user_id),
            'tenant_id': str(tenant_id),
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'total_requests': len(filtered),
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'total_tokens': total_input + total_output,
            'total_cost': round(total_cost, 6),
            'currency': 'USD',
        }

    async def get_tenant_usage(
        self,
        tenant_id: UUID,
        period: str = 'month',
    ) -> dict:
        return self._get_tenant_from_cache(tenant_id, period)

    def _get_tenant_from_cache(self, tenant_id: UUID, period: str) -> dict:
        records = [r for r in self._local_cache.values() if r.get('tenant_id') == str(tenant_id)]

        return {
            'tenant_id': str(tenant_id),
            'period': period,
            'total_requests': len(records),
            'total_cost': round(sum(r['cost'] for r in records), 6),
            'total_input_tokens': sum(r['input_tokens'] for r in records),
            'total_output_tokens': sum(r['output_tokens'] for r in records),
            'currency': 'USD',
        }

    async def set_spending_limit(
        self,
        tenant_id: UUID,
        monthly_limit: float,
        user_limit: Optional[float] = None,
    ) -> None:
        return

    async def check_spending_limit(self, tenant_id: UUID, user_id: Optional[UUID] = None) -> dict:
        usage = await self.get_tenant_usage(tenant_id, 'month')
        return {
            'allowed': True,
            'spent': round(usage['total_cost'], 6),
            'limit': 0,
            'remaining': 0,
            'user_limit': 0,
        }


class CostCalculator:
    @staticmethod
    def calculate(
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
    ) -> CostInfo:
        costs = TokenConfig.COST_PER_1K_TOKENS.get(model, {'input': 0, 'output': 0})

        if provider == ProviderType.OLLAMA.value:
            return CostInfo(input_cost=0, output_cost=0, total_cost=0)

        input_cost = (input_tokens / 1000) * costs.get('input', 0)
        output_cost = (output_tokens / 1000) * costs.get('output', 0)

        return CostInfo(
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(input_cost + output_cost, 6),
        )

    @staticmethod
    def estimate_cost(
        model: str,
        prompt_tokens: int,
        max_output_tokens: int,
    ) -> CostInfo:
        return CostCalculator.calculate(model, prompt_tokens, max_output_tokens)

    @staticmethod
    def compare_models(models: list[str], input_tokens: int, output_tokens: int) -> list[dict]:
        results = []
        for model in models:
            cost = CostCalculator.calculate(model, input_tokens, output_tokens)
            results.append({
                'model': model,
                'input_cost': cost.input_cost,
                'output_cost': cost.output_cost,
                'total_cost': cost.total_cost,
            })
        return sorted(results, key=lambda x: x['total_cost'])


class TokenCounter:
    @staticmethod
    def estimate_tokens(text: str, model: str = 'gpt-4') -> int:
        if 'gpt-4' in model.lower():
            return int(len(text) / 4.5)
        if 'gemini' in model.lower():
            return int(len(text) / 4)
        if 'llama' in model.lower():
            return len(text.split())
        return int(len(text) / 4)

    @staticmethod
    async def count_tokens_async(text: str, provider: str, model: str) -> int:
        if provider == ProviderType.OPENAI.value:
            from ..providers.openai import OpenAIProvider

            provider_instance = OpenAIProvider(api_key='')
            return await provider_instance.count_tokens(text)
        if provider == ProviderType.GEMINI.value:
            from ..providers.gemini import GeminiProvider

            provider_instance = GeminiProvider(api_key='')
            return await provider_instance.count_tokens(text)
        if provider == ProviderType.OLLAMA.value:
            from ..providers.ollama import OllamaProvider

            provider_instance = OllamaProvider()
            return await provider_instance.count_tokens(text)
        return TokenCounter.estimate_tokens(text, model)

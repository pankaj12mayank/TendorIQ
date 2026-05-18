"""AI Orchestration Layer"""

import json
from typing import Any, Optional
from abc import ABC, abstractmethod

import httpx

from .config import settings
from .logging import get_logger

logger = get_logger('ai')


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, model: str = 'gpt-4'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.openai.com/v1'

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature or settings.AI_TEMPERATURE,
            'max_tokens': max_tokens or settings.AI_MAX_TOKENS,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']


class AnthropicProvider(BaseAIProvider):
    """Anthropic API provider"""

    def __init__(self, api_key: str, model: str = 'claude-3-opus-20240229'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.anthropic.com/v1'

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature or settings.AI_TEMPERATURE,
            'max_tokens': max_tokens or settings.AI_MAX_TOKENS,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/messages',
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data['content'][0]['text']


class AIFactory:
    """Factory for creating AI providers"""

    _provider: Optional[BaseAIProvider] = None

    @classmethod
    def get_provider(cls) -> BaseAIProvider:
        if cls._provider is None:
            if settings.AI_PROVIDER == 'openai':
                cls._provider = OpenAIProvider(
                    api_key=settings.AI_API_KEY,
                    model=settings.AI_MODEL,
                )
            elif settings.AI_PROVIDER == 'anthropic':
                cls._provider = AnthropicProvider(
                    api_key=settings.AI_API_KEY,
                    model=settings.AI_MODEL,
                )
            else:
                raise ValueError(f'Unknown AI provider: {settings.AI_PROVIDER}')
        return cls._provider

    @classmethod
    async def generate(
        cls,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> str:
        provider = cls.get_provider()
        logger.info('AI generation request', provider=settings.AI_PROVIDER, model=settings.AI_MODEL)
        return await provider.generate(prompt, max_tokens, temperature, **kwargs)


async def generate_tender_summary(tender_description: str) -> str:
    """Generate a summary for a tender using AI"""
    prompt = f"""Summarize the following tender in a concise way:

{tender_description}

Provide a brief summary (2-3 sentences) capturing the key requirements."""

    return await AIFactory.generate(prompt, max_tokens=200)


async def analyze_bid_proposal(proposal_text: str, requirements: str) -> dict[str, Any]:
    """Analyze a bid proposal against requirements"""
    prompt = f"""Analyze this bid proposal against the requirements and provide feedback.

Requirements:
{requirements}

Proposal:
{proposal_text}

Provide a JSON response with the following structure:
{{
  "score": <0-100>,
  "strengths": [<list of strengths>],
  "weaknesses": [<list of weaknesses>],
  "recommendation": "<accept/reject/needs_revision>",
  "summary": "<brief summary>"
}}"""

    result = await AIFactory.generate(prompt, max_tokens=500)

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            'score': 0,
            'strengths': [],
            'weaknesses': ['Failed to parse AI response'],
            'recommendation': 'needs_revision',
            'summary': result,
        }
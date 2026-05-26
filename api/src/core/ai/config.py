"""AI Provider Configuration"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    OPENAI = 'openai'
    GEMINI = 'gemini'
    OLLAMA = 'ollama'


class ModelCapability(str, Enum):
    TEXT = 'text'
    VISION = 'vision'
    FUNCTION_CALLING = 'function_calling'
    JSON_MODE = 'json_mode'
    STREAMING = 'streaming'


class AIProviderConfig(BaseModel):
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 60
    max_retries: int = 3
    capabilities: list[ModelCapability] = Field(default_factory=list)


class ProviderDefaults:
    OPENAI_MODELS = {
        'gpt-4o': {'context': 128000, 'cost_per_1k_input': 0.0025, 'cost_per_1k_output': 0.01},
        'gpt-4o-mini': {'context': 128000, 'cost_per_1k_input': 0.00015, 'cost_per_1k_output': 0.0006},
        'gpt-4-turbo': {'context': 128000, 'cost_per_1k_input': 0.01, 'cost_per_1k_output': 0.03},
        'gpt-4': {'context': 8192, 'cost_per_1k_input': 0.03, 'cost_per_1k_output': 0.06},
        'gpt-3.5-turbo': {'context': 16385, 'cost_per_1k_input': 0.0005, 'cost_per_1k_output': 0.0015},
    }

    GEMINI_MODELS = {
        'gemini-1.5-pro': {'context': 1000000, 'cost_per_1k_input': 0.00125, 'cost_per_1k_output': 0.005},
        'gemini-1.5-flash': {'context': 1000000, 'cost_per_1k_input': 0.000075, 'cost_per_1k_output': 0.0003},
        'gemini-1.5-pro-latest': {'context': 1000000, 'cost_per_1k_input': 0.00125, 'cost_per_1k_output': 0.005},
        'gemini-pro': {'context': 32000, 'cost_per_1k_input': 0.00125, 'cost_per_1k_output': 0.00375},
    }

    OLLAMA_MODELS = {
        'llama3': {'context': 8192},
        'llama3.1': {'context': 128000},
        'mistral': {'context': 8192},
        'codellama': {'context': 16384},
        'phi3': {'context': 4096},
        'qwen2': {'context': 32768},
        'mixtral': {'context': 32768},
    }


class ProviderSelection:
    STRATEGIES = {
        'cheapest': 'Select lowest cost provider',
        'fastest': 'Select lowest latency provider',
        'balanced': 'Balance cost and latency',
        'capability': 'Select based on required capabilities',
        'fallback': 'Try primary, fallback to secondary',
    }

    @staticmethod
    def select_by_capability(required: list[ModelCapability]) -> list[ProviderType]:
        mapping = {
            ModelCapability.VISION: [ProviderType.OPENAI, ProviderType.GEMINI],
            ModelCapability.FUNCTION_CALLING: [ProviderType.OPENAI, ProviderType.GEMINI],
            ModelCapability.JSON_MODE: [ProviderType.OPENAI, ProviderType.GEMINI],
            ModelCapability.STREAMING: [ProviderType.OPENAI, ProviderType.OLLAMA],
        }
        candidates = set(ProviderType)
        for cap in required:
            if cap in mapping:
                candidates &= set(mapping[cap])
        return list(candidates) if candidates else [ProviderType.OPENAI]  # type: ignore


class TokenConfig:
    DEFAULT_MAX_TOKENS = {
        'gpt-4o': 4096,
        'gpt-4o-mini': 4096,
        'gpt-4-turbo': 4096,
        'gemini-1.5-pro': 8192,
        'gemini-1.5-flash': 8192,
        'llama3': 2048,
    }

    COST_PER_1K_TOKENS = {
        'gpt-4o': {'input': 0.0025, 'output': 0.01},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
        'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003},
    }
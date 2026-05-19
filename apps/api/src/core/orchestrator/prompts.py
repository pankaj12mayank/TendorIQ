"""Prompt Templates and Versioning System"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PromptType(str, Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    CHAIN_OF_THOUGHT = 'chain_of_thought'
    FEW_SHOT = 'few_shot'
    TEMPLATE = 'template'


class PromptVersion(BaseModel):
    version: str
    prompt_id: str
    content: str
    variables: list[str]
    created_at: str
    created_by: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True
    metrics: dict[str, Any] = Field(
        default_factory=lambda: {
            'usage_count': 0,
            'success_rate': 0.0,
            'avg_latency_ms': 0,
            'avg_cost': 0.0,
        }
    )


class PromptTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    prompt_type: PromptType
    content: str
    variables: list[str] = Field(default_factory=list)
    output_schema: Optional[dict] = None
    version: str = '1.0.0'
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=str)
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True

    def render(self, **kwargs) -> str:
        content = self.content
        for var in self.variables:
            value = kwargs.get(var, f'{{{{{var}}}}}')
            content = content.replace(f'{{{{{var}}}}}', str(value))
        return content

    def get_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


class PromptRegistry:
    def __init__(self, redis_pool=None):
        self._redis = redis_pool
        self._templates: dict[str, PromptTemplate] = {}
        self._versions: dict[str, list[PromptVersion]] = {}

    def register(self, template: PromptTemplate) -> str:
        template_id = template.id

        self._templates[template_id] = template

        version_key = f'prompt:version:{template_id}'
        version_list = self._versions.get(template_id, [])

        version_record = PromptVersion(
            version=template.version,
            prompt_id=template_id,
            content=template.content,
            variables=template.variables,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        version_list.append(version_record)
        self._versions[template_id] = version_list

        if self._redis:
            import asyncio
            asyncio.create_task(self._save_to_redis(template, version_record))

        return template_id

    async def _save_to_redis(self, template: PromptTemplate, version: PromptVersion) -> None:
        if not self._redis:
            return

        key = f'prompt:template:{template.id}'
        await self._redis.set(key, json.dumps(template.model_dump(), default=str), ex=86400 * 30)

        vkey = f'prompt:version:{template.id}:{version.version}'
        await self._redis.set(vkey, json.dumps(version.model_dump(), default=str), ex=86400 * 30)

    def get(self, template_id: str, version: Optional[str] = None) -> Optional[PromptTemplate]:
        if version:
            version_key = f'prompt:version:{template_id}:{version}'
            versions = self._versions.get(template_id, [])
            for v in versions:
                if v.version == version:
                    return PromptTemplate(
                        id=template_id,
                        name=self._templates[template_id].name,
                        content=v.content,
                        variables=v.variables,
                        version=v.version,
                    )

        return self._templates.get(template_id)

    def list_templates(self, tag_filter: Optional[list[str]] = None) -> list[PromptTemplate]:
        templates = list(self._templates.values())
        if tag_filter:
            templates = [t for t in templates if any(tag in t.tags for tag in tag_filter)]
        return templates

    def get_versions(self, template_id: str) -> list[PromptVersion]:
        return self._versions.get(template_id, [])

    def update_metrics(self, template_id: str, version: str, metrics: dict) -> None:
        versions = self._versions.get(template_id, [])
        for v in versions:
            if v.version == version:
                current = v.metrics
                usage = current.get('usage_count', 0) + 1
                success = metrics.get('success', False)
                current['usage_count'] = usage
                current['success_rate'] = (
                    (current.get('success_rate', 0) * (usage - 1) + (1 if success else 0)) / usage
                )
                current['avg_latency_ms'] = (
                    (current.get('avg_latency_ms', 0) * (usage - 1) + metrics.get('latency_ms', 0)) / usage
                )
                current['avg_cost'] = (
                    (current.get('avg_cost', 0) * (usage - 1) + metrics.get('cost', 0)) / usage
                )
                v.metrics = current
                break


class PromptBuilder:
    @staticmethod
    def system_prompt(
        role: str,
        constraints: list[str],
        context: Optional[dict] = None,
    ) -> str:
        parts = [f'You are a {role}.']
        if constraints:
            parts.append('\nConstraints:')
            for c in constraints:
                parts.append(f'- {c}')
        if context:
            parts.append('\nContext:')
            for k, v in context.items():
                parts.append(f'{k}: {v}')
        return '\n'.join(parts)

    @staticmethod
    def chain_of_thought(
        problem: str,
        steps: list[str],
        format_hint: Optional[str] = None,
    ) -> str:
        prompt = f'Problem: {problem}\n\nLet me think through this step by step:\n'
        for i, step in enumerate(steps, 1):
            prompt += f'{i}. {step}\n'
        if format_hint:
            prompt += f'\n{format_hint}'
        return prompt

    @staticmethod
    def few_shot(
        instruction: str,
        examples: list[dict[str, str]],
        query: str,
    ) -> list[dict[str, str]]:
        messages = [{'role': 'system', 'content': instruction}]
        for ex in examples:
            messages.append({'role': 'user', 'content': ex['input']})
            messages.append({'role': 'assistant', 'content': ex['output']})
        messages.append({'role': 'user', 'content': query})
        return messages

    @staticmethod
    def structured_output(
        instruction: str,
        schema: dict,
        include_examples: bool = True,
    ) -> str:
        schema_str = json.dumps(schema, indent=2)
        prompt = f'{instruction}\n\n'
        prompt += f'Respond ONLY with valid JSON matching this schema:\n```json\n{schema_str}\n```\n'
        prompt += 'Do not include any explanation, only the JSON output.'
        return prompt

    @staticmethod
    def guardrails(
        base_prompt: str,
        rules: list[str],
        forbidden_content: list[str],
    ) -> str:
        prompt = base_prompt + '\n\n--- GUARDRAILS ---\n'
        prompt += 'You MUST follow these rules:\n'
        for rule in rules:
            prompt += f'- {rule}\n'
        prompt += '\nYou MUST NOT include:\n'
        for forbidden in forbidden_content:
            prompt += f'- {forbidden}\n'
        prompt += '---\n'
        return prompt
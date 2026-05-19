"""Prompt Management Service with Versioning and Rollback"""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..database import AsyncSession
from .models import PromptTemplate, PromptTemplateVersion, PromptAuditLog, AuditAction
from .repository import (
    PromptRepository,
    PromptTemplateVersionRepository,
    PromptAnalyticsRepository,
    PromptAuditRepository,
)


class VersionInfo(BaseModel):
    version: str
    id: UUID
    created_at: datetime
    created_by: Optional[str] = None
    change_summary: Optional[str] = None
    is_active: bool


class PromptConfig(BaseModel):
    model: str = 'gpt-4o-mini'
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


class CreatePromptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_type: str
    category: Optional[str] = None
    content: str
    system_message: Optional[str] = None
    variables: list[str] = []
    output_schema: Optional[dict] = None
    guardrails: Optional[list[str]] = None
    examples: Optional[list[dict]] = None
    config: PromptConfig = PromptConfig()
    tags: list[str] = []
    is_active: bool = True
    is_system: bool = False


class UpdatePromptRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[list[str]] = None
    output_schema: Optional[dict] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class CreateVersionRequest(BaseModel):
    content: str
    system_message: Optional[str] = None
    variables: Optional[list[str]] = None
    guardrails: Optional[list[str]] = None
    examples: Optional[list[dict]] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    change_summary: Optional[str] = None


class RollbackRequest(BaseModel):
    target_version: str


class PromptMetrics(BaseModel):
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    avg_latency_ms: int = 0
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_confidence: float = 0.0


class PromptManagementService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._prompt_repo = PromptRepository(session)
        self._version_repo = PromptTemplateVersionRepository(session)
        self._analytics_repo = PromptAnalyticsRepository(session)
        self._audit_repo = PromptAuditRepository(session)

    async def create_prompt(
        self,
        request: CreatePromptRequest,
        tenant_id: Optional[UUID] = None,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> dict:
        template = await self._prompt_repo.create({
            'name': request.name,
            'description': request.description,
            'prompt_type': request.prompt_type,
            'category': request.category,
            'variables': request.variables,
            'output_schema': request.output_schema,
            'is_active': request.is_active,
            'is_system': request.is_system,
            'tags': request.tags,
            'tenant_id': tenant_id,
            'created_by': actor,
        })

        version = await self._create_version(
            prompt_id=template.id,
            request=request,
            actor=actor,
        )

        await self._audit_repo.log(
            action=AuditAction.CREATED,
            prompt_id=template.id,
            version_id=version.id,
            tenant_id=tenant_id,
            actor=actor,
            new_values={'name': request.name, 'prompt_type': request.prompt_type},
            ip_address=ip_address,
        )

        return {
            'template': self._serialize_template(template),
            'active_version': self._serialize_version(version),
        }

    async def _create_version(
        self,
        prompt_id: UUID,
        request: CreateVersionRequest | CreatePromptRequest,
        actor: Optional[str] = None,
        set_active: bool = True,
    ) -> PromptTemplateVersion:
        existing_versions = await self._version_repo.get_by_prompt(prompt_id)
        version_number = len(existing_versions) + 1
        version_str = f'{version_number}.0.0'

        if set_active:
            await self._version_repo.deactivate_all(prompt_id)

        version = await self._version_repo.create({
            'prompt_id': prompt_id,
            'version': version_str,
            'content': request.content,
            'system_message': getattr(request, 'system_message', None),
            'variables': getattr(request, 'variables', None),
            'guardrails': getattr(request, 'guardrails', None),
            'examples': getattr(request, 'examples', None),
            'model': request.config.model if hasattr(request, 'config') else (request.model or 'gpt-4o-mini'),
            'temperature': request.config.temperature if hasattr(request, 'config') else (request.temperature or 0.7),
            'max_tokens': request.config.max_tokens if hasattr(request, 'config') else (request.max_tokens or 2048),
            'top_p': request.config.top_p if hasattr(request, 'config') else getattr(request, 'top_p', None),
            'frequency_penalty': request.config.frequency_penalty if hasattr(request, 'config') else getattr(request, 'frequency_penalty', None),
            'presence_penalty': request.config.presence_penalty if hasattr(request, 'config') else getattr(request, 'presence_penalty', None),
            'is_active': set_active,
            'change_summary': getattr(request, 'change_summary', f'Initial version {version_str}'),
            'created_by': actor,
        })

        return version

    async def get_prompt(
        self,
        prompt_id: UUID,
        include_active_version: bool = True,
        include_analytics: bool = False,
    ) -> dict:
        template = await self._prompt_repo.get_by_id(prompt_id)
        if not template:
            return None

        result = {'template': self._serialize_template(template)}

        if include_active_version:
            active = await self._version_repo.get_active_version(prompt_id)
            if active:
                result['active_version'] = self._serialize_version(active)

        if include_analytics:
            stats = await self._analytics_repo.get_stats(prompt_id)
            result['analytics'] = stats

        return result

    async def get_prompt_by_name(self, name: str, tenant_id: Optional[UUID] = None) -> dict:
        template = await self._prompt_repo.get_by_name(name, tenant_id)
        if not template:
            return None
        return await self.get_prompt(template.id)

    async def list_prompts(
        self,
        tenant_id: Optional[UUID] = None,
        prompt_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        templates = await self._prompt_repo.list(
            tenant_id=tenant_id,
            prompt_type=prompt_type,
            category=category,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

        total = await self._prompt_repo.count(tenant_id)

        return {
            'prompts': [self._serialize_template(t) for t in templates],
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    async def update_prompt(
        self,
        prompt_id: UUID,
        request: UpdatePromptRequest,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[dict]:
        template = await self._prompt_repo.get_by_id(prompt_id)
        if not template:
            return None

        old_values = self._serialize_template(template)
        update_data = request.model_dump(exclude_unset=True)

        template = await self._prompt_repo.update(prompt_id, update_data)

        await self._audit_repo.log(
            action=AuditAction.UPDATED,
            prompt_id=prompt_id,
            tenant_id=template.tenant_id,
            actor=actor,
            old_values=old_values,
            new_values=update_data,
            ip_address=ip_address,
        )

        return {'template': self._serialize_template(template)}

    async def create_version(
        self,
        prompt_id: UUID,
        request: CreateVersionRequest,
        actor: Optional[str] = None,
        set_active: bool = True,
        ip_address: Optional[str] = None,
    ) -> Optional[dict]:
        template = await self._prompt_repo.get_by_id(prompt_id)
        if not template:
            return None

        version = await self._create_version(prompt_id, request, actor, set_active)

        await self._audit_repo.log(
            action=AuditAction.CREATED,
            prompt_id=prompt_id,
            version_id=version.id,
            tenant_id=template.tenant_id,
            actor=actor,
            new_values={'version': version.version, 'change_summary': request.change_summary},
            ip_address=ip_address,
        )

        return {
            'version': self._serialize_version(version),
            'prompt_id': str(prompt_id),
        }

    async def get_versions(self, prompt_id: UUID) -> list[dict]:
        versions = await self._version_repo.get_by_prompt(prompt_id)
        return [self._serialize_version(v) for v in versions]

    async def get_version(self, prompt_id: UUID, version: str) -> Optional[dict]:
        version_obj = await self._version_repo.get_by_version(prompt_id, version)
        if not version_obj:
            return None
        return self._serialize_version(version_obj)

    async def activate_version(
        self,
        version_id: UUID,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[dict]:
        version = await self._version_repo.activate_version(version_id)
        if not version:
            return None

        template = await self._prompt_repo.get_by_id(version.prompt_id)

        await self._audit_repo.log(
            action=AuditAction.ACTIVATED,
            prompt_id=version.prompt_id,
            version_id=version_id,
            tenant_id=template.tenant_id if template else None,
            actor=actor,
            new_values={'version': version.version},
            ip_address=ip_address,
        )

        return {
            'version': self._serialize_version(version),
            'prompt_id': str(version.prompt_id),
        }

    async def rollback_to_version(
        self,
        prompt_id: UUID,
        target_version: str,
        actor: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[dict]:
        current_active = await self._version_repo.get_active_version(prompt_id)
        target = await self._version_repo.get_by_version(prompt_id, target_version)

        if not target:
            return None

        await self._version_repo.deactivate_all(prompt_id)
        target.is_active = True
        await self._session.flush()

        template = await self._prompt_repo.get_by_id(prompt_id)

        await self._audit_repo.log(
            action=AuditAction.ROLLED_BACK,
            prompt_id=prompt_id,
            version_id=target.id,
            tenant_id=template.tenant_id if template else None,
            actor=actor,
            old_values={'version': current_active.version if current_active else None},
            new_values={'version': target_version, 'action': 'rolled_back'},
            ip_address=ip_address,
        )

        return {
            'rolled_back_to': self._serialize_version(target),
            'previous_version': current_active.version if current_active else None,
        }

    async def get_version_diff(self, version_id1: UUID, version_id2: UUID) -> dict:
        return await self._version_repo.compare_versions(version_id1, version_id2)

    async def record_usage(
        self,
        prompt_id: UUID,
        version_id: UUID,
        tenant_id: Optional[UUID],
        success: bool,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        confidence: float = 1.0,
    ) -> PromptMetrics:
        analytics = await self._analytics_repo.update_metrics(
            prompt_id=prompt_id,
            version_id=version_id,
            tenant_id=tenant_id,
            success=success,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            confidence=confidence,
        )

        return PromptMetrics(
            total_requests=analytics.request_count,
            success_count=analytics.success_count,
            failure_count=analytics.failure_count,
            success_rate=round(analytics.success_count / analytics.request_count * 100, 2) if analytics.request_count > 0 else 0,
            avg_latency_ms=analytics.avg_latency_ms,
            total_cost=round(analytics.total_cost, 6),
            total_input_tokens=analytics.total_input_tokens,
            total_output_tokens=analytics.total_output_tokens,
            avg_confidence=round(analytics.avg_confidence, 2),
        )

    async def get_prompt_analytics(self, prompt_id: UUID, tenant_id: Optional[UUID] = None) -> dict:
        return await self._analytics_repo.get_stats(prompt_id, tenant_id)

    async def get_audit_history(
        self,
        prompt_id: Optional[UUID] = None,
        version_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> list[dict]:
        if prompt_id:
            logs = await self._audit_repo.get_prompt_history(prompt_id, limit)
        elif version_id:
            logs = await self._audit_repo.get_version_history(version_id, limit)
        elif tenant_id:
            logs = await self._audit_repo.get_tenant_history(tenant_id, limit=limit)
        else:
            logs = await self._audit_repo.get_recent_actions(limit=limit)

        return [self._serialize_audit_log(log) for log in logs]

    def _serialize_template(self, template: PromptTemplate) -> dict:
        return {
            'id': str(template.id),
            'name': template.name,
            'description': template.description,
            'prompt_type': template.prompt_type,
            'category': template.category,
            'variables': template.variables or [],
            'output_schema': template.output_schema,
            'is_active': template.is_active,
            'is_system': template.is_system,
            'tags': template.tags or [],
            'created_by': template.created_by,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None,
        }

    def _serialize_version(self, version: PromptTemplateVersion) -> dict:
        return {
            'id': str(version.id),
            'prompt_id': str(version.prompt_id),
            'version': version.version,
            'content': version.content,
            'system_message': version.system_message,
            'variables': version.variables or [],
            'guardrails': version.guardrails or [],
            'examples': version.examples or [],
            'model': version.model,
            'temperature': version.temperature,
            'max_tokens': version.max_tokens,
            'top_p': version.top_p,
            'frequency_penalty': version.frequency_penalty,
            'presence_penalty': version.presence_penalty,
            'is_active': version.is_active,
            'change_summary': version.change_summary,
            'created_by': version.created_by,
            'created_at': version.created_at.isoformat() if version.created_at else None,
        }

    def _serialize_audit_log(self, log: PromptAuditLog) -> dict:
        return {
            'id': str(log.id),
            'prompt_id': str(log.prompt_id) if log.prompt_id else None,
            'version_id': str(log.version_id) if log.version_id else None,
            'tenant_id': str(log.tenant_id) if log.tenant_id else None,
            'action': log.action,
            'actor': log.actor,
            'changes': log.changes,
            'old_values': log.old_values,
            'new_values': log.new_values,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        }
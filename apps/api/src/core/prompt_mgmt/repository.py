"""Prompt Management Repository"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    PromptTemplate,
    PromptVersion,
    PromptAnalytics,
    PromptAuditLog,
    AuditAction,
)


class PromptRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> PromptTemplate:
        template = PromptTemplate(**data)
        self._session.add(template)
        await self._session.flush()
        return template

    async def get_by_id(self, prompt_id: UUID, tenant_id: Optional[UUID] = None) -> Optional[PromptTemplate]:
        query = select(PromptTemplate).where(PromptTemplate.id == prompt_id)
        if tenant_id:
            query = query.where(PromptTemplate.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, tenant_id: Optional[UUID] = None) -> Optional[PromptTemplate]:
        query = select(PromptTemplate).where(PromptTemplate.name == name)
        if tenant_id:
            query = query.where(PromptTemplate.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: Optional[UUID] = None,
        prompt_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PromptTemplate]:
        query = select(PromptTemplate)

        if tenant_id:
            query = query.where(PromptTemplate.tenant_id == tenant_id)
        if prompt_type:
            query = query.where(PromptTemplate.prompt_type == prompt_type)
        if category:
            query = query.where(PromptTemplate.category == category)
        if is_active is not None:
            query = query.where(PromptTemplate.is_active == is_active)
        if tags:
            pass

        query = query.order_by(PromptTemplate.updated_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, prompt_id: UUID, data: dict) -> Optional[PromptTemplate]:
        data['updated_at'] = datetime.now(timezone.utc)
        stmt = update(PromptTemplate).where(PromptTemplate.id == prompt_id).values(**data)
        await self._session.execute(stmt)
        await self._session.flush()
        return await self.get_by_id(prompt_id)

    async def delete(self, prompt_id: UUID) -> bool:
        stmt = delete(PromptTemplate).where(PromptTemplate.id == prompt_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def count(self, tenant_id: Optional[UUID] = None) -> int:
        query = select(func.count(PromptTemplate.id))
        if tenant_id:
            query = query.where(PromptTemplate.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return result.scalar() or 0


class PromptVersionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> PromptVersion:
        version = PromptVersion(**data)
        self._session.add(version)
        await self._session.flush()
        return version

    async def get_by_id(self, version_id: UUID) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(PromptVersion.id == version_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_version(self, prompt_id: UUID) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(
            and_(PromptVersion.prompt_id == prompt_id, PromptVersion.is_active == True)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_prompt(self, prompt_id: UUID, limit: int = 100) -> list[PromptVersion]:
        query = select(PromptVersion).where(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.created_at.desc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_version(self, prompt_id: UUID, version: str) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(
            and_(PromptVersion.prompt_id == prompt_id, PromptVersion.version == version)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def deactivate_all(self, prompt_id: UUID) -> None:
        stmt = update(PromptVersion).where(
            and_(PromptVersion.prompt_id == prompt_id, PromptVersion.is_active == True)
        ).values(is_active=False)
        await self._session.execute(stmt)

    async def activate_version(self, version_id: UUID) -> Optional[PromptVersion]:
        version = await self.get_by_id(version_id)
        if version:
            await self.deactivate_all(version.prompt_id)
            stmt = update(PromptVersion).where(PromptVersion.id == version_id).values(is_active=True)
            await self._session.execute(stmt)
            await self._session.flush()
        return await self.get_by_id(version_id)

    async def set_as_active(self, version_id: UUID) -> None:
        version = await self.get_by_id(version_id)
        if version:
            await self.deactivate_all(version.prompt_id)
            stmt = update(PromptVersion).where(PromptVersion.id == version_id).values(is_active=True)
            await self._session.execute(stmt)
            await self._session.flush()

    async def get_latest_version(self, prompt_id: UUID) -> Optional[PromptVersion]:
        query = select(PromptVersion).where(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.created_at.desc()).limit(1)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def compare_versions(self, version_id1: UUID, version_id2: UUID) -> dict:
        v1 = await self.get_by_id(version_id1)
        v2 = await self.get_by_id(version_id2)
        if not v1 or not v2:
            return {}

        return {
            'version1': {
                'id': str(v1.id),
                'version': v1.version,
                'content': v1.content,
                'model': v1.model,
                'temperature': v1.temperature,
            },
            'version2': {
                'id': str(v2.id),
                'version': v2.version,
                'content': v2.content,
                'model': v2.model,
                'temperature': v2.temperature,
            },
            'differences': self._find_differences(v1, v2),
        }

    def _find_differences(self, v1: PromptVersion, v2: PromptVersion) -> list[dict]:
        diffs = []
        if v1.content != v2.content:
            diffs.append({'field': 'content', 'type': 'modified'})
        if v1.model != v2.model:
            diffs.append({'field': 'model', 'from': v1.model, 'to': v2.model})
        if v1.temperature != v2.temperature:
            diffs.append({'field': 'temperature', 'from': v1.temperature, 'to': v2.temperature})
        if v1.max_tokens != v2.max_tokens:
            diffs.append({'field': 'max_tokens', 'from': v1.max_tokens, 'to': v2.max_tokens})
        return diffs


class PromptAnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create(self, prompt_id: UUID, version_id: UUID, tenant_id: Optional[UUID] = None) -> PromptAnalytics:
        query = select(PromptAnalytics).where(
            and_(
                PromptAnalytics.prompt_id == prompt_id,
                PromptAnalytics.version_id == version_id,
                PromptAnalytics.tenant_id == tenant_id,
            )
        )
        result = await self._session.execute(query)
        analytics = result.scalar_one_or_none()

        if not analytics:
            analytics = PromptAnalytics(
                prompt_id=prompt_id,
                version_id=version_id,
                tenant_id=tenant_id,
            )
            self._session.add(analytics)
            await self._session.flush()

        return analytics

    async def update_metrics(
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
    ) -> PromptAnalytics:
        analytics = await self.get_or_create(prompt_id, version_id, tenant_id)

        analytics.request_count += 1
        analytics.total_input_tokens += input_tokens
        analytics.total_output_tokens += output_tokens
        analytics.total_cost += cost

        n = analytics.request_count
        analytics.avg_latency_ms = int((analytics.avg_latency_ms * (n - 1) + latency_ms) / n)
        analytics.avg_confidence = (analytics.avg_confidence * (n - 1) + confidence) / n

        if success:
            analytics.success_count += 1
        else:
            analytics.failure_count += 1

        analytics.last_used_at = datetime.now(timezone.utc)
        await self._session.flush()

        return analytics

    async def get_stats(self, prompt_id: UUID, tenant_id: Optional[UUID] = None) -> dict:
        query = select(PromptAnalytics).where(PromptAnalytics.prompt_id == prompt_id)
        if tenant_id:
            query = query.where(PromptAnalytics.tenant_id == tenant_id)

        result = await self._session.execute(query)
        analytics_list = list(result.scalars().all())

        if not analytics_list:
            return {
                'total_requests': 0,
                'success_rate': 0,
                'avg_latency_ms': 0,
                'total_cost': 0,
                'total_tokens': 0,
            }

        total_requests = sum(a.request_count for a in analytics_list)
        total_success = sum(a.success_count for a in analytics_list)
        total_failure = sum(a.failure_count for a in analytics_list)

        return {
            'total_requests': total_requests,
            'success_count': total_success,
            'failure_count': total_failure,
            'success_rate': round(total_success / total_requests * 100, 2) if total_requests > 0 else 0,
            'avg_latency_ms': sum(a.avg_latency_ms for a in analytics_list) // len(analytics_list),
            'total_cost': round(sum(a.total_cost for a in analytics_list), 6),
            'total_input_tokens': sum(a.total_input_tokens for a in analytics_list),
            'total_output_tokens': sum(a.total_output_tokens for a in analytics_list),
            'avg_confidence': round(sum(a.avg_confidence for a in analytics_list) / len(analytics_list), 2),
        }


class PromptAuditRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def log(
        self,
        action: str,
        prompt_id: Optional[UUID] = None,
        version_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        actor: Optional[str] = None,
        changes: Optional[dict] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> PromptAuditLog:
        log_entry = PromptAuditLog(
            prompt_id=prompt_id,
            version_id=version_id,
            tenant_id=tenant_id,
            action=action,
            actor=actor,
            changes=changes,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(log_entry)
        await self._session.flush()
        return log_entry

    async def get_prompt_history(
        self,
        prompt_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PromptAuditLog]:
        query = select(PromptAuditLog).where(
            PromptAuditLog.prompt_id == prompt_id
        ).order_by(PromptAuditLog.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_version_history(
        self,
        version_id: UUID,
        limit: int = 50,
    ) -> list[PromptAuditLog]:
        query = select(PromptAuditLog).where(
            PromptAuditLog.version_id == version_id
        ).order_by(PromptAuditLog.created_at.desc()).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_tenant_history(
        self,
        tenant_id: UUID,
        action_filter: Optional[str] = None,
        actor_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PromptAuditLog]:
        query = select(PromptAuditLog).where(PromptAuditLog.tenant_id == tenant_id)

        if action_filter:
            query = query.where(PromptAuditLog.action == action_filter)
        if actor_filter:
            query = query.where(PromptAuditLog.actor == actor_filter)

        query = query.order_by(PromptAuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_recent_actions(
        self,
        limit: int = 50,
        hours: int = 24,
    ) -> list[PromptAuditLog]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(PromptAuditLog).where(
            PromptAuditLog.created_at >= cutoff
        ).order_by(PromptAuditLog.created_at.desc()).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())
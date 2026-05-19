"""Base job types for in-process background work."""

import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from .config import QueueConfig

logger = logging.getLogger(__name__)


class JobPriority(int, Enum):
    HIGH = 10
    NORMAL = 5
    LOW = 1


class JobState(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    RETRY = 'retry'
    DEAD = 'dead'
    CANCELLED = 'cancelled'


class BaseJob(ABC):
    queue_name: str = QueueConfig.PREFIX
    job_name: str = 'base'
    job_timeout: int = QueueConfig.DEFAULT_TIMEOUT
    max_retries: int = QueueConfig.MAX_RETRIES

    def __init__(
        self,
        ctx: dict,
        job_id: Optional[str] = None,
        document_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        priority: int = JobPriority.NORMAL,
        metadata: Optional[dict] = None,
    ):
        self.ctx = ctx
        self.job_id = job_id
        self.document_id = document_id
        self.tenant_id = tenant_id
        self.priority = priority
        self.metadata = metadata or {}
        self._started_at: Optional[datetime] = None
        self._ended_at: Optional[datetime] = None
        self._error: Optional[str] = None
        self._attempts: int = 0

    @abstractmethod
    async def run(self, *args, **kwargs) -> dict:
        pass

    async def update_status(
        self,
        status: JobState,
        error: Optional[str] = None,
        result: Optional[dict] = None,
    ) -> None:
        if status == JobState.RUNNING and not self._started_at:
            self._started_at = datetime.now(timezone.utc)
        elif status in (JobState.SUCCESS, JobState.FAILED, JobState.DEAD):
            self._ended_at = datetime.now(timezone.utc)
        if error:
            self._error = error
        logger.debug('Job %s %s', self.job_name, status.value)

    async def on_start(self) -> None:
        self._attempts += 1
        await self.update_status(JobState.RUNNING)

    async def on_success(self, result: dict) -> None:
        await self.update_status(JobState.SUCCESS, result=result)

    async def on_failure(self, error: Exception) -> None:
        self._error = f'{error}\n{traceback.format_exc()}'
        await self.update_status(JobState.FAILED, error=self._error)


class RetryHandler:
    @staticmethod
    def get_retry_delay(attempts: int) -> int:
        return QueueConfig.RETRY_DELAYS.get(attempts, 600)


class JobTracker:
    @staticmethod
    async def get_job_status(_pool: Any, job_id: str) -> Optional[dict]:
        return {'job_id': job_id, 'status': 'unknown'}

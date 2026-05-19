"""Enqueue background work via in-process asyncio tasks."""

import logging
from typing import Any, Optional
from uuid import UUID, uuid4

from ..tasks.inline import schedule_job
from .config import (
    QUEUE_ANALYSIS,
    QUEUE_EMAIL,
    QUEUE_NOTIFICATIONS,
    QUEUE_OCR,
    QUEUE_PARSING,
    JobPriority,
    QueueConfig,
)

logger = logging.getLogger(__name__)


class Enqueue:
    async def enqueue(
        self,
        function: str,
        _queue: str = QUEUE_OCR,
        _job_id: Optional[str] = None,
        _timeout: Optional[int] = None,
        _max_tries: Optional[int] = None,
        _retry_delay: Optional[int] = None,
        _priority: int = JobPriority.NORMAL,
        _keep_result: int = QueueConfig.KEEP_RESULT,
        _dedup: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        job_id = _job_id or str(uuid4())
        schedule_job(function, _job_id=job_id, **kwargs)
        logger.info('Scheduled in-process job %s: %s', job_id, function)
        return job_id

    async def enqueue_ocr(
        self,
        document_id: UUID,
        tenant_id: UUID,
        file_path: str,
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'ocr_process',
            _queue=QUEUE_OCR,
            document_id=str(document_id),
            tenant_id=str(tenant_id),
            file_path=file_path,
            options=options or {},
            **kwargs,
        )

    async def enqueue_ocr_batch(
        self,
        document_ids: list[UUID],
        tenant_id: UUID,
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'ocr_batch',
            _queue=QUEUE_OCR,
            document_ids=[str(d) for d in document_ids],
            tenant_id=str(tenant_id),
            options=options or {},
            **kwargs,
        )

    async def enqueue_parsing(
        self,
        document_id: UUID,
        tenant_id: UUID,
        parsed_document_id: UUID,
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'parsing_process',
            _queue=QUEUE_PARSING,
            document_id=str(document_id),
            tenant_id=str(tenant_id),
            parsed_document_id=str(parsed_document_id),
            options=options or {},
            **kwargs,
        )

    async def enqueue_parsing_batch(
        self,
        parsed_document_ids: list[UUID],
        tenant_id: UUID,
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'parsing_batch',
            _queue=QUEUE_PARSING,
            parsed_document_ids=[str(d) for d in parsed_document_ids],
            tenant_id=str(tenant_id),
            options=options or {},
            **kwargs,
        )

    async def enqueue_chunking(
        self,
        parsed_document_id: UUID,
        tenant_id: UUID,
        strategy: str = 'hybrid',
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'chunking_process',
            _queue=QUEUE_PARSING,
            parsed_document_id=str(parsed_document_id),
            tenant_id=str(tenant_id),
            strategy=strategy,
            options=options or {},
            **kwargs,
        )

    async def enqueue_analysis(
        self,
        document_id: UUID,
        tenant_id: UUID,
        analysis_type: str = 'full',
        options: Optional[dict] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'document_analysis',
            _queue=QUEUE_ANALYSIS,
            document_id=str(document_id),
            tenant_id=str(tenant_id),
            analysis_type=analysis_type,
            options=options or {},
            **kwargs,
        )

    async def enqueue_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: Optional[str] = None,
        attachments: Optional[list[str]] = None,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'email_send',
            _queue=QUEUE_EMAIL,
            to_email=to_email,
            subject=subject,
            body=body,
            template=template,
            attachments=attachments or [],
            **kwargs,
        )

    async def enqueue_notification(
        self,
        user_id: UUID,
        tenant_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
        channel: str = 'in_app',
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'notification_send',
            _queue=QUEUE_NOTIFICATIONS,
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            channel=channel,
            **kwargs,
        )

    async def enqueue_webhook(
        self,
        url: str,
        method: str = 'POST',
        headers: Optional[dict] = None,
        payload: Optional[dict] = None,
        timeout: int = 30,
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'webhook_call',
            _queue=QUEUE_NOTIFICATIONS,
            url=url,
            method=method,
            headers=headers or {},
            payload=payload or {},
            timeout=timeout,
            **kwargs,
        )

    async def enqueue_scheduled_report(
        self,
        report_id: UUID,
        tenant_id: UUID,
        recipients: list[str],
        format: str = 'pdf',
        **kwargs,
    ) -> str:
        return await self.enqueue(
            'scheduled_report',
            _queue=QUEUE_NOTIFICATIONS,
            report_id=str(report_id),
            tenant_id=str(tenant_id),
            recipients=recipients,
            format=format,
            **kwargs,
        )


enqueue = Enqueue()

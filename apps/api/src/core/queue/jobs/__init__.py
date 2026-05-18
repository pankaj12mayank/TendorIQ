"""Job Registry and Functions"""

from typing import Any, Callable

from .base_job import (
    BaseJob,
    JobState,
    JobPriority,
    RetryHandler,
    JobTracker,
)
from .config import QueueConfig, REDIS_POOL_MAIN, REDIS_POOL_QUEUE

__all__ = [
    'BaseJob',
    'JobState',
    'JobPriority',
    'RetryHandler',
    'JobTracker',
    'QueueConfig',
    'REDIS_POOL_MAIN',
    'REDIS_POOL_QUEUE',
]


async def ocr_process(ctx: dict, document_id: str, tenant_id: str, file_path: str, **kwargs) -> dict:
    from .jobs.ocr_jobs import OCRJob

    job = OCRJob(ctx, document_id=document_id, tenant_id=tenant_id)
    return await job.run(document_id, tenant_id, file_path, kwargs)


async def ocr_batch(ctx: dict, document_ids: list[str], tenant_id: str, **kwargs) -> dict:
    from .jobs.ocr_jobs import OCRBatchJob

    job = OCRBatchJob(ctx, tenant_id=tenant_id)
    return await job.run(document_ids, tenant_id, kwargs)


async def parsing_process(ctx: dict, document_id: str, tenant_id: str, parsed_document_id: str, **kwargs) -> dict:
    from .jobs.parsing_jobs import ParsingJob

    job = ParsingJob(ctx, document_id=document_id, tenant_id=tenant_id)
    return await job.run(document_id, tenant_id, parsed_document_id, kwargs)


async def parsing_batch(ctx: dict, parsed_document_ids: list[str], tenant_id: str, **kwargs) -> dict:
    from .jobs.parsing_jobs import ParsingBatchJob

    job = ParsingBatchJob(ctx, tenant_id=tenant_id)
    return await job.run(parsed_document_ids, tenant_id, kwargs)


async def chunking_process(ctx: dict, parsed_document_id: str, tenant_id: str, strategy: str = 'hybrid', **kwargs) -> dict:
    from .jobs.parsing_jobs import ChunkingJob

    job = ChunkingJob(ctx, tenant_id=tenant_id)
    return await job.run(parsed_document_id, tenant_id, strategy, kwargs)


async def document_analysis(ctx: dict, document_id: str, tenant_id: str, analysis_type: str = 'full', **kwargs) -> dict:
    from .jobs.analysis_jobs import AnalysisJob

    job = AnalysisJob(ctx, document_id=document_id, tenant_id=tenant_id)
    return await job.run(document_id, tenant_id, analysis_type, kwargs)


async def batch_analysis(ctx: dict, document_ids: list[str], tenant_id: str, analysis_type: str = 'full', **kwargs) -> dict:
    from .jobs.analysis_jobs import BatchAnalysisJob

    job = BatchAnalysisJob(ctx, tenant_id=tenant_id)
    return await job.run(document_ids, tenant_id, analysis_type, kwargs)


async def email_send(ctx: dict, to_email: str, subject: str, body: str, **kwargs) -> dict:
    from .jobs.notification_jobs import EmailJob

    job = EmailJob(ctx)
    return await job.run(to_email, subject, body, **kwargs)


async def notification_send(ctx: dict, user_id: str, tenant_id: str, notification_type: str, title: str, message: str, **kwargs) -> dict:
    from .jobs.notification_jobs import NotificationJob

    job = NotificationJob(ctx, user_id=user_id, tenant_id=tenant_id)
    return await job.run(user_id, tenant_id, notification_type, title, message, **kwargs)


async def webhook_call(ctx: dict, url: str, method: str = 'POST', **kwargs) -> dict:
    from .jobs.notification_jobs import WebhookJob

    job = WebhookJob(ctx)
    return await job.run(url, method, **kwargs)


async def scheduled_report(ctx: dict, report_id: str, tenant_id: str, recipients: list[str], format: str = 'pdf') -> dict:
    from .jobs.notification_jobs import ScheduledReportJob

    job = ScheduledReportJob(ctx, tenant_id=tenant_id)
    return await job.run(report_id, tenant_id, recipients, format)


async def export_document(ctx: dict, export_id: str, export_type: str, format: str, source_id: str, source_type: str, user_id: str, organization_id: str, **kwargs) -> dict:
    from .jobs.export_jobs import ExportJob

    job = ExportJob(ctx, tenant_id=organization_id)
    return await job.run(export_id, export_type, format, source_id, source_type, user_id, organization_id, **kwargs)


async def batch_export(ctx: dict, batch_id: str, exports: list[dict], user_id: str, organization_id: str, **kwargs) -> dict:
    from .jobs.export_jobs import BatchExportJob

    job = BatchExportJob(ctx, tenant_id=organization_id)
    return await job.run(batch_id, exports, user_id, organization_id, **kwargs)


async def scheduled_export(ctx: dict, schedule_id: str, export_type: str, format: str, source_ids: list[str], recipients: list[str], user_id: str, organization_id: str, **kwargs) -> dict:
    from .jobs.export_jobs import ScheduledExportJob

    job = ScheduledExportJob(ctx, tenant_id=organization_id)
    return await job.run(schedule_id, export_type, format, source_ids, recipients, user_id, organization_id, **kwargs)


async def export_cleanup(ctx: dict, older_than_hours: int = 24, **kwargs) -> dict:
    from .jobs.export_jobs import ExportCleanupJob

    job = ExportCleanupJob(ctx)
    return await job.run(older_than_hours=older_than_hours, **kwargs)


JOB_FUNCTIONS: dict[str, Callable] = {
    'ocr_process': ocr_process,
    'ocr_batch': ocr_batch,
    'parsing_process': parsing_process,
    'parsing_batch': parsing_batch,
    'chunking_process': chunking_process,
    'document_analysis': document_analysis,
    'batch_analysis': batch_analysis,
    'email_send': email_send,
    'notification_send': notification_send,
    'webhook_call': webhook_call,
    'scheduled_report': scheduled_report,
    'export_document': export_document,
    'batch_export': batch_export,
    'scheduled_export': scheduled_export,
    'export_cleanup': export_cleanup,
}
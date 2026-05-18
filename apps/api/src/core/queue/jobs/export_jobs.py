"""Export Job Definitions for Async Processing"""

from typing import Optional

from ..config import QUEUE_NOTIFICATIONS, QueueConfig
from .base_job import BaseJob, JobState


class ExportJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'export_document'
    job_timeout = 300
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        export_id: str,
        export_type: str,
        format: str,
        source_id: str,
        source_type: str,
        user_id: str,
        organization_id: str,
        template_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        await self.on_start()

        try:
            from ...core.export.service import get_export_service
            from ...core.export.schemas import ExportFormat, ExportType, ExportRequest

            service = get_export_service()

            request = ExportRequest(
                export_type=ExportType(export_type),
                format=ExportFormat(format),
                source_id=source_id,
                source_type=source_type,
                template_id=template_id,
            )

            job = service.create_export(request, user_id, organization_id)
            processed_job = service.process_export(job.job_id)

            await self.on_success({
                'export_id': processed_job.export_id,
                'job_id': processed_job.job_id,
                'status': processed_job.status.value,
                'format': processed_job.format.value,
                'file_size_bytes': processed_job.file_size_bytes,
            })

            return {
                'export_id': processed_job.export_id,
                'status': processed_job.status.value,
                'download_url': processed_job.download_url,
                'file_size_bytes': processed_job.file_size_bytes,
            }

        except Exception as e:
            await self.on_failure(e)
            raise


class BatchExportJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'batch_export'
    job_timeout = 600
    max_retries = 2

    async def run(
        self,
        batch_id: str,
        exports: list[dict],
        user_id: str,
        organization_id: str,
        **kwargs,
    ) -> dict:
        await self.on_start()

        try:
            from ...core.export.service import get_export_service
            from ...core.export.schemas import ExportFormat, ExportType, ExportRequest

            service = get_export_service()
            results = []

            for export_data in exports:
                request = ExportRequest(
                    export_type=ExportType(export_data['export_type']),
                    format=ExportFormat(export_data['format']),
                    source_id=export_data['source_id'],
                    source_type=export_data['source_type'],
                    title=export_data.get('title'),
                )

                job = service.create_export(request, user_id, organization_id)
                processed_job = service.process_export(job.job_id)

                results.append({
                    'export_id': processed_job.export_id,
                    'job_id': processed_job.job_id,
                    'status': processed_job.status.value,
                    'format': processed_job.format.value,
                })

            await self.on_success({
                'batch_id': batch_id,
                'total': len(exports),
                'completed': len(results),
                'results': results,
            })

            return {
                'batch_id': batch_id,
                'total': len(exports),
                'results': results,
            }

        except Exception as e:
            await self.on_failure(e)
            raise


class ScheduledExportJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'scheduled_export'
    job_timeout = 600
    max_retries = 1

    async def run(
        self,
        schedule_id: str,
        export_type: str,
        format: str,
        source_ids: list[str],
        recipients: list[str],
        user_id: str,
        organization_id: str,
        template_id: Optional[str] = None,
        **kwargs,
    ) -> dict:
        await self.on_start()

        try:
            from ...core.export.service import get_export_service
            from ...core.export.schemas import ExportFormat, ExportType, ExportRequest

            service = get_export_service()
            results = []

            for source_id in source_ids:
                request = ExportRequest(
                    export_type=ExportType(export_type),
                    format=ExportFormat(format),
                    source_id=source_id,
                    source_type=export_type,
                    template_id=template_id,
                )

                job = service.create_export(request, user_id, organization_id)
                processed_job = service.process_export(job.job_id)
                results.append({
                    'export_id': processed_job.export_id,
                    'source_id': source_id,
                    'status': processed_job.status.value,
                })

            attachment_urls = [
                f'/api/v1/exports/{r["export_id"]}/download'
                for r in results
                if r['status'] == 'completed'
            ]

            if recipients and attachment_urls:
                from ...services.email import EmailService
                email_service = EmailService()
                await email_service.send(
                    to=recipients[0],
                    subject=f'Scheduled Export - {schedule_id}',
                    body=f'Your scheduled exports are ready. {len(attachment_urls)} files attached.',
                    attachments=attachment_urls,
                )

            await self.on_success({
                'schedule_id': schedule_id,
                'total_exports': len(source_ids),
                'recipients': recipients,
                'attachment_count': len(attachment_urls),
            })

            return {
                'schedule_id': schedule_id,
                'total_exports': len(source_ids),
                'recipients': recipients,
                'results': results,
            }

        except Exception as e:
            await self.on_failure(e)
            raise


class ExportCleanupJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'export_cleanup'
    job_timeout = 120
    max_retries = 1

    async def run(
        self,
        older_than_hours: int = 24,
        **kwargs,
    ) -> dict:
        await self.on_start()

        try:
            import os
            from datetime import datetime, timedelta

            from ...core.export.engine import get_export_engine

            engine = get_export_engine()
            storage_path = engine._storage_path

            cleaned_count = 0
            cleaned_size = 0
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

            for filename in os.listdir(storage_path):
                file_path = os.path.join(storage_path, filename)
                if os.path.isfile(file_path):
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_count += 1
                        cleaned_size += file_size

            await self.on_success({
                'cleaned_files': cleaned_count,
                'cleaned_size_bytes': cleaned_size,
                'older_than_hours': older_than_hours,
            })

            return {
                'cleaned_files': cleaned_count,
                'cleaned_size_bytes': cleaned_size,
                'cleaned_size_formatted': engine.format_filesize(cleaned_size),
            }

        except Exception as e:
            await self.on_failure(e)
            raise
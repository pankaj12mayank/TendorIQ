"""Notification & Email Job Definitions"""

from typing import Optional
from uuid import UUID

from ..config import QUEUE_NOTIFICATIONS, QueueConfig
from .base_job import BaseJob, JobState


class EmailJob(BaseJob):
    queue_name = QUEUE_EMAIL
    job_name = 'email_send'
    job_timeout = 120
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: Optional[str] = None,
        attachments: Optional[list[str]] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...email.service import EmailService
            from ...email.schemas import EmailRequest

            email_service = EmailService()
            result = await email_service.send(
                EmailRequest(
                    to=to_email,
                    subject=subject,
                    html=body,
                )
            )
            result = {
                'message_id': result.message_id,
                'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
            }

            await self.on_success({
                'to': to_email,
                'subject': subject,
                'message_id': result.get('message_id'),
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class NotificationJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'notification_send'
    job_timeout = 60
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        user_id: UUID,
        tenant_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
        channel: str = 'in_app',
    ) -> dict:
        await self.on_start()

        try:
            from ...services.notifications import NotificationService
            from ...db.session import get_db_session

            db = get_db_session()
            notification_service = NotificationService(db)

            result = await notification_service.send(
                user_id=user_id,
                tenant_id=tenant_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                channel=channel,
            )

            await self.on_success({
                'user_id': str(user_id),
                'type': notification_type,
                'channel': channel,
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class WebhookJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'webhook_call'
    job_timeout = 30
    max_retries = 2

    async def run(
        self,
        url: str,
        method: str = 'POST',
        headers: Optional[dict] = None,
        payload: Optional[dict] = None,
        timeout: int = 30,
    ) -> dict:
        await self.on_start()

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    result = await response.json()

            await self.on_success({
                'url': url,
                'status': response.status,
                'response': result,
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class ScheduledReportJob(BaseJob):
    queue_name = QUEUE_NOTIFICATIONS
    job_name = 'scheduled_report'
    job_timeout = 300
    max_retries = 1

    async def run(
        self,
        report_id: UUID,
        tenant_id: UUID,
        recipients: list[str],
        format: str = 'pdf',
    ) -> dict:
        await self.on_start()

        try:
            from ...services.reports import ReportService
            from ...db.session import get_db_session

            db = get_db_session()
            report_service = ReportService(db)

            result = await report_service.generate_and_send(
                report_id=report_id,
                tenant_id=tenant_id,
                recipients=recipients,
                format=format,
            )

            await self.on_success({
                'report_id': str(report_id),
                'recipients': recipients,
                'format': format,
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise
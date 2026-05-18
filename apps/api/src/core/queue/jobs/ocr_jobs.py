"""OCR Job Definitions"""

from typing import Optional
from uuid import UUID

from ..config import QUEUE_OCR, QueueConfig
from .base_job import BaseJob, JobState, JobPriority


class OCRJob(BaseJob):
    queue_name = QUEUE_OCR
    job_name = 'ocr_process'
    job_timeout = 600
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        document_id: UUID,
        tenant_id: UUID,
        file_path: str,
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.ocr import OCRService
            from ...db.session import get_db_session

            options = options or {}
            db = get_db_session()

            ocr_service = OCRService(db)
            result = await ocr_service.process_document(
                document_id=document_id,
                tenant_id=tenant_id,
                file_path=file_path,
                options=options,
            )

            await self.on_success({
                'document_id': str(document_id),
                'status': 'completed',
                'pages_processed': result.get('pages_processed', 0),
                'confidence': result.get('avg_confidence', 0),
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class OCRBatchJob(BaseJob):
    queue_name = QUEUE_OCR
    job_name = 'ocr_batch'
    job_timeout = 3600
    max_retries = 2

    async def run(
        self,
        document_ids: list[UUID],
        tenant_id: UUID,
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.ocr import OCRService
            from ...db.session import get_db_session

            options = options or {}
            db = get_db_session()

            ocr_service = OCRService(db)
            results = await ocr_service.process_batch(
                document_ids=document_ids,
                tenant_id=tenant_id,
                options=options,
            )

            await self.on_success({
                'total': len(document_ids),
                'processed': results.get('processed', 0),
                'failed': results.get('failed', 0),
            })
            return results

        except Exception as e:
            await self.on_failure(e)
            raise


class OCRCleanupJob(BaseJob):
    queue_name = QUEUE_OCR
    job_name = 'ocr_cleanup'
    job_timeout = 60
    max_retries = 1

    async def run(self, document_id: UUID, temp_files: list[str]) -> dict:
        await self.on_start()

        try:
            import shutil
            from pathlib import Path

            cleaned = []
            for path in temp_files:
                p = Path(path)
                if p.exists():
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                    cleaned.append(path)

            await self.on_success({'cleaned': cleaned})
            return {'cleaned': cleaned}

        except Exception as e:
            await self.on_failure(e)
            raise
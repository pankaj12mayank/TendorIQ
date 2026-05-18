"""Analysis Job Definitions"""

from typing import Optional
from uuid import UUID

from ..config import QUEUE_ANALYSIS, QueueConfig
from .base_job import BaseJob, JobState, JobPriority


class AnalysisJob(BaseJob):
    queue_name = QUEUE_ANALYSIS
    job_name = 'document_analysis'
    job_timeout = 600
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        document_id: UUID,
        tenant_id: UUID,
        analysis_type: str = 'full',
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.analysis import AnalysisService
            from ...db.session import get_db_session

            db = get_db_session()
            analysis_service = AnalysisService(db)

            result = await analysis_service.analyze_document(
                document_id=document_id,
                tenant_id=tenant_id,
                analysis_type=analysis_type,
                options=options,
            )

            await self.on_success({
                'document_id': str(document_id),
                'analysis_type': analysis_type,
                'status': 'completed',
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class BatchAnalysisJob(BaseJob):
    queue_name = QUEUE_ANALYSIS
    job_name = 'batch_analysis'
    job_timeout = 3600
    max_retries = 2

    async def run(
        self,
        document_ids: list[UUID],
        tenant_id: UUID,
        analysis_type: str = 'full',
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.analysis import AnalysisService
            from ...db.session import get_db_session

            db = get_db_session()
            analysis_service = AnalysisService(db)

            results = await analysis_service.analyze_batch(
                document_ids=document_ids,
                tenant_id=tenant_id,
                analysis_type=analysis_type,
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


class CleanupOldResultsJob(BaseJob):
    queue_name = QUEUE_ANALYSIS
    job_name = 'cleanup_old_results'
    job_timeout = 300
    max_retries = 1

    async def run(self, days: int = 30) -> dict:
        await self.on_start()

        try:
            from ...db.repositories.analysis import AnalysisRepository
            from ...db.session import get_db_session

            db = get_db_session()
            repo = AnalysisRepository(db)

            deleted = await repo.delete_old_results(days=days)

            await self.on_success({
                'deleted_count': deleted,
                'days_threshold': days,
            })
            return {'deleted_count': deleted, 'days_threshold': days}

        except Exception as e:
            await self.on_failure(e)
            raise
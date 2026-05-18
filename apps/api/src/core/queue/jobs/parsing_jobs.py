"""Parsing Job Definitions"""

from typing import Optional
from uuid import UUID

from ..config import QUEUE_PARSING, QueueConfig
from .base_job import BaseJob, JobState, JobPriority


class ParsingJob(BaseJob):
    queue_name = QUEUE_PARSING
    job_name = 'parsing_process'
    job_timeout = 900
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        document_id: UUID,
        tenant_id: UUID,
        parsed_document_id: UUID,
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.parsing import ParsingService
            from ...db.session import get_db_session

            options = options or {}
            db = get_db_session()

            parsing_service = ParsingService(db)
            result = await parsing_service.parse_document(
                document_id=document_id,
                tenant_id=tenant_id,
                parsed_document_id=parsed_document_id,
                options=options,
            )

            await self.on_success({
                'document_id': str(document_id),
                'parsed_document_id': str(parsed_document_id),
                'status': 'completed',
                'page_count': result.get('page_count', 0),
                'word_count': result.get('word_count', 0),
                'chunk_count': result.get('chunk_count', 0),
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise


class ParsingBatchJob(BaseJob):
    queue_name = QUEUE_PARSING
    job_name = 'parsing_batch'
    job_timeout = 7200
    max_retries = 2

    async def run(
        self,
        parsed_document_ids: list[UUID],
        tenant_id: UUID,
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.parsing import ParsingService
            from ...db.session import get_db_session

            options = options or {}
            db = get_db_session()

            parsing_service = ParsingService(db)
            results = await parsing_service.parse_batch(
                parsed_document_ids=parsed_document_ids,
                tenant_id=tenant_id,
                options=options,
            )

            await self.on_success({
                'total': len(parsed_document_ids),
                'processed': results.get('processed', 0),
                'failed': results.get('failed', 0),
            })
            return results

        except Exception as e:
            await self.on_failure(e)
            raise


class ChunkingJob(BaseJob):
    queue_name = QUEUE_PARSING
    job_name = 'chunking_process'
    job_timeout = 300
    max_retries = QueueConfig.MAX_RETRIES

    async def run(
        self,
        parsed_document_id: UUID,
        tenant_id: UUID,
        strategy: str = 'hybrid',
        options: Optional[dict] = None,
    ) -> dict:
        await self.on_start()

        try:
            from ...services.parsing import ParsingService
            from ...db.session import get_db_session

            db = get_db_session()
            parsing_service = ParsingService(db)

            result = await parsing_service.create_chunks(
                parsed_document_id=parsed_document_id,
                tenant_id=tenant_id,
                strategy=strategy,
                options=options,
            )

            await self.on_success({
                'parsed_document_id': str(parsed_document_id),
                'chunks_created': result.get('chunks_created', 0),
            })
            return result

        except Exception as e:
            await self.on_failure(e)
            raise
"""Queue API — in-process jobs only (no Redis)."""

from fastapi import APIRouter

from ....core.queue.config import QueueConfig

router = APIRouter(prefix='/queue', tags=['queue'])


@router.get('/health')
async def queue_health():
    return {
        'status': 'healthy',
        'mode': 'inline',
        'queues': QueueConfig.QUEUES,
    }


@router.get('/stats')
async def queue_stats():
    return {
        'mode': 'inline',
        'message': 'Jobs run in the API process. No external queue backend.',
        'queues': {name: {'pending': 0, 'active': 0} for name in QueueConfig.QUEUES},
    }

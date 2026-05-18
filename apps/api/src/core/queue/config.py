"""ARQ Queue Configuration"""

from arq.connections import RedisSettings
from arq.constants import (
    DefaultQueueName,
    HealthCheckKey,
    ResultKeyPrefix,
    JobKeyPrefix,
    WorkerInfoKey,
)

from ..config import settings

QUEUE_OCR = f'{settings.QUEUE_NAME_PREFIX}:ocr'
QUEUE_PARSING = f'{settings.QUEUE_NAME_PREFIX}:parsing'
QUEUE_EMAIL = f'{settings.QUEUE_NAME_PREFIX}:email'
QUEUE_ANALYSIS = f'{settings.QUEUE_NAME_PREFIX}:analysis'
QUEUE_NOTIFICATIONS = f'{settings.QUEUE_NAME_PREFIX}:notifications'

DEAD_LETTER_QUEUE = f'{settings.QUEUE_NAME_PREFIX}:dead-letter'
FAILED_QUEUE = f'{settings.QUEUE_NAME_PREFIX}:failed'


def get_redis_settings(db: int = 0) -> RedisSettings:
    password = settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
    return RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=db,
        password=password,
        conn_timeout=10,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )


REDIS_POOL_MAIN = get_redis_settings(0)
REDIS_POOL_QUEUE = get_redis_settings(1)
REDIS_POOL_RESULTS = get_redis_settings(2)


class QueueConfig:
    PREFIX = settings.QUEUE_NAME_PREFIX
    DEFAULT_TIMEOUT = settings.QUEUE_DEFAULT_TIMEOUT
    MAX_RETRIES = settings.QUEUE_MAX_RETRIES

    RETRY_DELAYS = {
        1: 30,
        2: 120,
        3: 600,
    }

    PRIORITY_HIGH = 10
    PRIORITY_NORMAL = 5
    PRIORITY_LOW = 1

    QUEUES = {
        'ocr': QUEUE_OCR,
        'parsing': QUEUE_PARSING,
        'email': QUEUE_EMAIL,
        'analysis': QUEUE_ANALYSIS,
        'notifications': QUEUE_NOTIFICATIONS,
    }

    JOB_TTL = 86400
    RESULT_TTL = 86400
    KEEP_RESULT = 86400


class WorkerDefaults:
    max_jobs = 10
    job_timeout = 300
    keep_result = 86400
    keep_failed = 259200
    allow_abort = True
    max_tries = 3
    max_retries = 3

    shadow_path = None
    after_job_msg = None

    health_check_interval = 30
    max_concurrent_tasks = 10

    on_startup = None
    on_shutdown = None
    on_job_start = None
    on_job_end = None
"""Background job configuration (in-process; no Redis)."""

from enum import IntEnum


class JobPriority(IntEnum):
    HIGH = 10
    NORMAL = 5
    LOW = 1


class QueueConfig:
    PREFIX = 'tendoriq'
    DEFAULT_TIMEOUT = 300
    MAX_RETRIES = 3
    RETRY_DELAYS = {1: 30, 2: 120, 3: 600}
    KEEP_RESULT = 3600
    JOB_TTL = 86400
    PRIORITY_NORMAL = JobPriority.NORMAL

    QUEUES = ['ocr', 'parsing', 'email', 'analysis', 'notifications']


QUEUE_OCR = f'{QueueConfig.PREFIX}:ocr'
QUEUE_PARSING = f'{QueueConfig.PREFIX}:parsing'
QUEUE_EMAIL = f'{QueueConfig.PREFIX}:email'
QUEUE_ANALYSIS = f'{QueueConfig.PREFIX}:analysis'
QUEUE_NOTIFICATIONS = f'{QueueConfig.PREFIX}:notifications'
DEAD_LETTER_QUEUE = f'{QueueConfig.PREFIX}:dead_letter'
FAILED_QUEUE = f'{QueueConfig.PREFIX}:failed'

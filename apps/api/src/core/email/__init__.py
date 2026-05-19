"""Email Module - Transactional Email System"""

from .service import EmailService, get_email_service, EmailTriggerHandler, get_trigger_handler
from .schemas import (
    EmailRequest,
    EmailResponse,
    EmailStatus,
    EmailType,
    EmailLog,
    EmailTemplate,
    RetryConfig,
    EmailBatchRequest,
    EmailStats
)
from .templates import get_template, get_all_templates, TEMPLATES

__all__ = [
    'EmailService',
    'get_email_service',
    'EmailTriggerHandler',
    'get_trigger_handler',
    'EmailRequest',
    'EmailResponse',
    'EmailStatus',
    'EmailType',
    'EmailLog',
    'EmailTemplate',
    'RetryConfig',
    'EmailBatchRequest',
    'EmailStats',
    'get_template',
    'get_all_templates',
    'TEMPLATES'
]
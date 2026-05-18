"""Structured Logging Configuration"""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger
from structlog import (
    EventDictionary,
    LoggerFactory,
    make_filtering_bound_logger,
    processors,
    stdlib,
)

from .config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['message'] = record.getMessage()
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'tenant_id'):
            log_record['tenant_id'] = record.tenant_id


def configure_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        format='%(message)s',
        stream=sys.stdout,
        level=log_level,
    )

    processors_list = [
        stdlib.add_log_level,
        stdlib.add_logger_name,
        processors.TimeStamper(fmt='iso'),
        processors.StackInfoRenderer(),
        processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == 'json':
        processors_list.append(CustomJsonFormatter)
    else:
        processors_list.append(processors.JSONRenderer())

    LoggerFactory.set_processor(processors.CallLoggerFactory(make_filtering_bound_logger(log_level)))

    structlog.configure(
        processors=processors_list,
        wrapper_class=stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_context: Any):
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger
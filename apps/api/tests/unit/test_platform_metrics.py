"""Layer 10 — platform admin metrics (no mock observability data)."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from src.core.platform_metrics import (
    failed_queue_job_to_admin_dict,
    queue_job_to_admin_dict,
)


def test_queue_job_to_admin_dict_maps_fields():
    job = SimpleNamespace(
        id=uuid4(),
        job_type='document_parse',
        status='processing',
        attempts=1,
        max_attempts=3,
        priority=10,
        payload={'doc': '1'},
        error=None,
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        started_at=datetime(2026, 5, 1, 1, tzinfo=timezone.utc),
    )
    out = queue_job_to_admin_dict(job)
    assert out['id'] == str(job.id)
    assert out['queue'] == 'document_parse'
    assert out['status'] == 'processing'
    assert out['priority'] == 'high'
    assert out['progress'] == 50


def test_failed_queue_job_to_admin_dict_retryable():
    job = SimpleNamespace(
        id=uuid4(),
        job_type='ai_analysis',
        status='failed',
        attempts=1,
        max_attempts=3,
        error='timeout',
        payload={},
        created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
    )
    out = failed_queue_job_to_admin_dict(job)
    assert out['retryable'] is True
    assert out['error'] == 'timeout'


def test_admin_platform_does_not_import_mock_metrics():
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'admin_platform.py'
    content = path.read_text(encoding='utf-8')
    assert 'MOCK_QUEUE_METRICS' not in content
    assert 'MOCK_FAILURES' not in content
    assert 'MOCK_AI_METRICS' not in content

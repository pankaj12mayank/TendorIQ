"""Pipeline stage derivation from real document state."""

from src.core.dashboard.pipeline_stages import derive_pipeline_stages


def test_uploaded_stage():
    out = derive_pipeline_stages('uploaded')
    assert out['stages'][0]['status'] == 'completed'
    assert out['stages'][1]['status'] == 'active'
    assert out['is_terminal'] is False


def test_failed_at_extracting():
    out = derive_pipeline_stages('failed', analysis_meta=None, processing_error='Parse error')
    assert out['is_failed'] is True
    assert out['stages'][1]['status'] == 'failed'


def test_retrying_shows_active_extracting_or_processing():
    out = derive_pipeline_stages('retrying', retry_count=2)
    assert out['is_retrying'] is True
    assert out['retry_count'] == 2


def test_completed_with_proposal():
    out = derive_pipeline_stages(
        'completed',
        has_analysis_result=True,
        has_proposal=True,
    )
    assert out['stages'][-1]['status'] == 'completed'
    assert out['is_terminal'] is True

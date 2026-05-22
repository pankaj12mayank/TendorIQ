"""Layer 14 — email triggers, notifications, onboarding paths."""

from pathlib import Path

from src.api.router.email import TriggerRequest


def test_trigger_request_accepts_flat_body():
    req = TriggerRequest.model_validate(
        {
            'user_email': 'user@example.com',
            'file_name': 'doc.pdf',
            'tender_name': 'RFP-1',
        }
    )
    assert req.user_email == 'user@example.com'
    assert req.data['file_name'] == 'doc.pdf'
    assert req.data['tender_name'] == 'RFP-1'


def test_trigger_request_accepts_nested_data():
    req = TriggerRequest.model_validate(
        {
            'user_email': 'user@example.com',
            'data': {'feature': 'ocr', 'used': 10, 'limit': 5},
        }
    )
    assert req.data['feature'] == 'ocr'


def test_email_triggers_compat_router_registered():
    main_text = Path(__file__).resolve().parents[2] / 'src' / 'main.py'
    text = main_text.read_text(encoding='utf-8')
    assert 'email_triggers_router' in text

    triggers_text = (
        Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'email_triggers.py'
    ).read_text(encoding='utf-8')
    assert "prefix='/email/triggers'" in triggers_text
    assert '/upload-received' in triggers_text


def test_notifications_router_has_delete_and_soft_delete_filter():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'notifications.py'
    text = path.read_text(encoding='utf-8')
    assert "@router.delete('/{notification_id}')" in text
    assert 'deleted_at.is_(None)' in text


def test_email_logs_use_db_model_not_mock_list():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'router' / 'email.py'
    text = path.read_text(encoding='utf-8')
    assert 'DbEmailLog' in text
    assert 'MOCK_LOGS' not in text
    assert '_persist_email_log' in text


def test_onboarding_router_paths_for_fe():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'routers' / 'onboarding.py'
    text = path.read_text(encoding='utf-8')
    assert "@router.get('/status'" in text
    assert "@router.post('/step/1'" in text
    assert "@router.get('/plans'" in text

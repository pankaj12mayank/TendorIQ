"""FE-compatible email trigger paths: /api/v1/email/triggers/*"""

from fastapi import APIRouter

from .email import (
    trigger_processing_completed,
    trigger_processing_failed,
    trigger_quota_exceeded,
    trigger_subscription_alert,
    trigger_upload_received,
)

router = APIRouter(prefix='/email/triggers', tags=['Email Triggers'])

router.add_api_route('/upload-received', trigger_upload_received, methods=['POST'])
router.add_api_route('/processing-completed', trigger_processing_completed, methods=['POST'])
router.add_api_route('/processing-failed', trigger_processing_failed, methods=['POST'])
router.add_api_route('/quota-exceeded', trigger_quota_exceeded, methods=['POST'])
router.add_api_route('/subscription-alert', trigger_subscription_alert, methods=['POST'])

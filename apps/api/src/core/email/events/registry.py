"""Canonical event catalog for TenderIQ email automation."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EventDefinition:
    event_key: str
    name: str
    category: str
    description: str
    default_template_slug: str
    required_variables: tuple[str, ...] = ()


EVENT_REGISTRY: list[EventDefinition] = [
    # Auth
    EventDefinition('auth.signup.completed', 'Welcome Email', 'auth', 'User completed signup', 'welcome_email', ('user_name', 'dashboard_link')),
    EventDefinition('auth.email.verify', 'Verify Email', 'auth', 'Email verification', 'verify_email', ('user_name', 'verify_link')),
    EventDefinition('auth.forgot_password', 'Password Reset', 'auth', 'Forgot password request', 'reset_password', ('user_name', 'reset_link')),
    EventDefinition('auth.password.changed', 'Password Changed', 'auth', 'Password was changed', 'password_changed', ('user_name',)),
    EventDefinition('auth.login.suspicious', 'Suspicious Login', 'auth', 'Unusual login detected', 'suspicious_login', ('user_name', 'ip_address', 'timestamp')),
    EventDefinition('auth.login.otp', 'Login OTP', 'auth', 'One-time login code', 'login_otp', ('user_name', 'otp_code')),
    EventDefinition('auth.account.locked', 'Account Locked', 'auth', 'Account locked after failed attempts', 'account_locked', ('user_name',)),
    # Onboarding
    EventDefinition('onboarding.started', 'Onboarding Started', 'onboarding', 'Tenant started onboarding', 'onboarding_started', ('company_name', 'dashboard_link')),
    EventDefinition('onboarding.completed', 'Onboarding Completed', 'onboarding', 'Onboarding finished', 'onboarding_completed', ('company_name', 'plan_name')),
    EventDefinition('onboarding.profile.incomplete', 'Profile Incomplete', 'onboarding', 'Profile needs completion', 'profile_incomplete', ('user_name', 'dashboard_link')),
    EventDefinition('trial.started', 'Trial Started', 'onboarding', 'Free trial activated', 'trial_started', ('company_name', 'plan_name', 'trial_end_date')),
    # Documents
    EventDefinition('document.upload.received', 'Upload Received', 'document', 'Document uploaded', 'upload_received', ('user_name', 'document_name', 'tender_name')),
    EventDefinition('document.processing.started', 'Processing Started', 'document', 'AI processing started', 'processing_started', ('user_name', 'document_name')),
    EventDefinition('document.processing.completed', 'Processing Completed', 'document', 'AI processing finished', 'processing_completed', ('user_name', 'document_name', 'dashboard_link')),
    EventDefinition('document.processing.failed', 'Processing Failed', 'document', 'AI processing failed', 'processing_failed', ('user_name', 'document_name', 'error_message')),
    EventDefinition('document.processing.retry', 'Processing Retry', 'document', 'Retry started', 'processing_retry', ('user_name', 'document_name')),
    EventDefinition('document.review.required', 'Review Required', 'document', 'Manual review needed', 'review_required', ('user_name', 'document_name', 'dashboard_link')),
    EventDefinition('document.export.ready', 'Export Ready', 'document', 'Export file ready', 'export_ready', ('user_name', 'document_name', 'download_link')),
    # Billing
    EventDefinition('billing.payment.success', 'Payment Success', 'billing', 'Payment succeeded', 'payment_success', ('user_name', 'amount', 'plan_name')),
    EventDefinition('billing.payment.failed', 'Payment Failed', 'billing', 'Payment failed', 'payment_failed', ('user_name', 'billing_link')),
    EventDefinition('billing.subscription.activated', 'Subscription Activated', 'billing', 'Subscription active', 'subscription_activated', ('plan_name', 'billing_link')),
    EventDefinition('billing.subscription.expired', 'Subscription Expired', 'billing', 'Subscription expired', 'subscription_expired', ('plan_name', 'billing_link')),
    EventDefinition('billing.quota.exceeded', 'Quota Exceeded', 'billing', 'Usage quota exceeded', 'quota_exceeded', ('feature', 'used', 'limit', 'billing_link')),
    EventDefinition('billing.plan.upgraded', 'Plan Upgraded', 'billing', 'Plan upgraded', 'plan_upgraded', ('plan_name', 'billing_link')),
    # Admin
    EventDefinition('admin.queue.failed', 'Queue Failure Alert', 'admin', 'Queue job failed', 'queue_failed', ('job_name', 'error_message')),
    EventDefinition('admin.ai.provider.failure', 'AI Provider Failure', 'admin', 'AI provider error', 'ai_provider_failure', ('provider_name', 'error_message')),
    EventDefinition('admin.system.alert', 'System Alert', 'admin', 'Critical system alert', 'system_alert', ('alert_message',)),
    EventDefinition('admin.tokens.high_usage', 'High Token Usage', 'admin', 'Token usage threshold', 'high_token_usage', ('usage_percent',)),
    EventDefinition('admin.storage.warning', 'Storage Warning', 'admin', 'Storage threshold warning', 'storage_warning', ('usage_percent',)),
    # Team
    EventDefinition('team.invitation.sent', 'Team Invitation', 'team', 'Invitation email', 'team_invitation', ('inviter_name', 'company_name', 'invite_link')),
    EventDefinition('team.member.added', 'Member Added', 'team', 'New team member', 'member_added', ('user_name', 'company_name')),
    EventDefinition('team.role.changed', 'Role Changed', 'team', 'Member role updated', 'role_changed', ('user_name', 'new_role', 'company_name')),
]

EVENT_BY_KEY = {e.event_key: e for e in EVENT_REGISTRY}


def get_event_definition(event_key: str) -> Optional[EventDefinition]:
    return EVENT_BY_KEY.get(event_key)

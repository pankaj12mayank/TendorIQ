"""Shared Svix webhook verification (Clerk, Resend)."""

from __future__ import annotations

try:
    from svix.webhooks import Webhook, WebhookVerificationError
except ImportError:  # pragma: no cover - exercised when svix missing
    Webhook = None  # type: ignore[misc, assignment]
    WebhookVerificationError = Exception  # type: ignore[misc, assignment]

SVIX_AVAILABLE = Webhook is not None

__all__ = ['Webhook', 'WebhookVerificationError', 'SVIX_AVAILABLE']

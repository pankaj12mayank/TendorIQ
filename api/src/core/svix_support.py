"""Optional Clerk webhook verification via svix."""

try:
    from svix.webhooks import Webhook, WebhookVerificationError

    SVIX_AVAILABLE = True
except ImportError:
    Webhook = None  # type: ignore[misc, assignment]
    WebhookVerificationError = Exception  # type: ignore[misc, assignment]
    SVIX_AVAILABLE = False

"""Notification System - Toast & Email Templates"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

try:
    from ..email.service import EmailService
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    EmailService = None

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    # Plan/Payment Notifications
    PLAN_PURCHASED = "plan_purchased"
    PLAN_UPGRADED = "plan_upgraded"
    PLAN_CANCELLED = "plan_cancelled"
    PLAN_EXPIRED = "plan_expired"
    PLAN_RENEWED = "plan_renewed"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_DUE = "payment_due"
    
    # Account Notifications
    WELCOME = "welcome"
    USER_INVITED = "user_invited"
    USER_ADDED = "user_added"
    ROLE_CHANGED = "role_changed"
    
    # System Notifications
    DOCUMENT_PROCESSED = "document_processed"
    ANALYSIS_COMPLETE = "analysis_complete"
    EXPORT_READY = "export_ready"


# Human-readable notification messages
NOTIFICATION_MESSAGES = {
    # Plan/Payment - Human Language
    NotificationType.PLAN_PURCHASED: {
        "title": "🎉 Plan Activated!",
        "message": "Congratulations! Your {plan_name} plan is now active. You have access to all premium features!",
        "toast": "Your plan has been activated successfully!"
    },
    NotificationType.PLAN_UPGRADED: {
        "title": "🚀 Plan Upgraded!",
        "message": "You've upgraded to {plan_name}. Enjoy your new features and higher limits!",
        "toast": "Plan upgraded successfully! New features unlocked."
    },
    NotificationType.PLAN_CANCELLED: {
        "title": "⚠️ Plan Cancelled",
        "message": "Your {plan_name} plan has been cancelled. You'll have access until {end_date}.",
        "toast": "Your plan has been cancelled."
    },
    NotificationType.PLAN_EXPIRED: {
        "title": "⏰ Plan Expired",
        "message": "Your {plan_name} plan has expired. Please renew to continue using premium features.",
        "toast": "Your plan has expired. Please renew to continue."
    },
    NotificationType.PLAN_RENEWED: {
        "title": "✅ Plan Renewed!",
        "message": "Your {plan_name} plan has been automatically renewed for the next billing period.",
        "toast": "Plan renewed successfully! You're all set."
    },
    NotificationType.PAYMENT_SUCCESS: {
        "title": "💳 Payment Successful!",
        "message": "Payment of {amount} {currency} received. Thank you for your continued support!",
        "toast": "Payment successful! Thank you!"
    },
    NotificationType.PAYMENT_FAILED: {
        "title": "❌ Payment Failed",
        "message": "Your payment of {amount} {currency} failed. Please update your payment method.",
        "toast": "Payment failed. Please check your payment method."
    },
    NotificationType.PAYMENT_DUE: {
        "title": "💰 Payment Due",
        "message": "Your next payment of {amount} {currency} is due on {due_date}. Auto-renewal is enabled.",
        "toast": "Payment due soon. Your plan will auto-renew."
    },
    
    # Account
    NotificationType.WELCOME: {
        "title": "👋 Welcome to TenderIQ!",
        "message": "We're excited to have you! Get started by exploring your dashboard.",
        "toast": "Welcome to TenderIQ! Let's get started."
    },
    NotificationType.USER_INVITED: {
        "title": "📧 You've Been Invited!",
        "message": "{inviter_name} has invited you to join their team on TenderIQ.",
        "toast": "You've been invited to join a team!"
    },
    NotificationType.USER_ADDED: {
        "title": "👤 New Team Member",
        "message": "{user_name} has joined your team as {role}.",
        "toast": "New team member added!"
    },
    NotificationType.ROLE_CHANGED: {
        "title": "🔐 Role Updated",
        "message": "Your role has been changed to {new_role} in {team_name}.",
        "toast": "Your role has been updated."
    },
    
    # System
    NotificationType.DOCUMENT_PROCESSED: {
        "title": "📄 Document Ready",
        "message": "Your document '{doc_name}' has been processed and is ready for review.",
        "toast": "Document processing complete!"
    },
    NotificationType.ANALYSIS_COMPLETE: {
        "title": "🔍 Analysis Complete",
        "message": "AI analysis for '{tender_name}' is ready. View the insights now!",
        "toast": "AI analysis complete!"
    },
    NotificationType.EXPORT_READY: {
        "title": "📥 Export Ready",
        "message": "Your export '{export_name}' is ready for download.",
        "toast": "Your export is ready to download!"
    },
}


class NotificationService:
    """Send notifications via email and toast"""
    
    def __init__(self):
        self.email_service = EmailService() if EMAIL_SERVICE_AVAILABLE else None
    
    def get_human_message(self, notification_type: NotificationType, **kwargs) -> Dict[str, str]:
        """Get human-readable notification message"""
        
        template = NOTIFICATION_MESSAGES.get(notification_type, {
            "title": "Notification",
            "message": "You have a new notification",
            "toast": "New notification"
        })
        
        title = template["title"].format(**kwargs)
        message = template["message"].format(**kwargs)
        toast = template["toast"].format(**kwargs)
        
        return {
            "title": title,
            "message": message,
            "toast": toast,
            "type": notification_type.value
        }
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient_email: str,
        recipient_name: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send notification via email"""
        
        messages = self.get_human_message(notification_type, **kwargs)
        
        # Determine email template based on notification type
        if notification_type in [NotificationType.PLAN_PURCHASED, NotificationType.PLAN_UPGRADED, 
                                 NotificationType.PLAN_RENEWED, NotificationType.PAYMENT_SUCCESS]:
            template_name = "plan_confirmation"
        elif notification_type in [NotificationType.PLAN_EXPIRED, NotificationType.PLAN_CANCELLED,
                                   NotificationType.PAYMENT_FAILED, NotificationType.PAYMENT_DUE]:
            template_name = "plan_alert"
        elif notification_type == NotificationType.WELCOME:
            template_name = "welcome"
        else:
            template_name = "general"
        
        try:
            await self.email_service.send_template_email(
                recipient=recipient_email,
                template_name=template_name,
                subject=messages["title"],
                context={
                    "name": recipient_name or "User",
                    "message": messages["message"],
                    **kwargs
                }
            )
            
            logger.info(f"Notification sent: {notification_type} to {recipient_email}")
            
            return {
                "success": True,
                "notification": messages,
                "sent_to": recipient_email
            }
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                "success": False,
                "error": str(e),
                "notification": messages
            }
    
    async def notify_plan_change(
        self,
        notification_type: NotificationType,
        tenant_name: str,
        tenant_email: str,
        plan_name: str,
        amount: float = None,
        currency: str = "USD",
        end_date: str = None
    ) -> Dict[str, Any]:
        """Notify about plan/payment changes"""
        
        return await self.send_notification(
            notification_type=notification_type,
            recipient_email=tenant_email,
            recipient_name=tenant_name,
            tenant_name=tenant_name,
            plan_name=plan_name,
            amount=amount,
            currency=currency,
            end_date=end_date or "end of billing period"
        )
    
    async def notify_user(
        self,
        notification_type: NotificationType,
        user_email: str,
        user_name: str = None,
        **extra_context
    ) -> Dict[str, Any]:
        """Notify user about account events"""
        
        return await self.send_notification(
            notification_type=notification_type,
            recipient_email=user_email,
            recipient_name=user_name,
            **extra_context
        )


# Toast notification format for frontend
class ToastNotification:
    """Format notifications for frontend toast display"""
    
    @staticmethod
    def format_for_frontend(notification_type: NotificationType, **kwargs) -> Dict[str, Any]:
        """Format notification for React Toast"""
        
        messages = NOTIFICATION_MESSAGES.get(notification_type, {})
        
        # Map to toast types
        toast_type_map = {
            NotificationType.PLAN_PURCHASED: "success",
            NotificationType.PLAN_UPGRADED: "success",
            NotificationType.PLAN_RENEWED: "success",
            NotificationType.WELCOME: "success",
            NotificationType.USER_ADDED: "info",
            NotificationType.ROLE_CHANGED: "info",
            NotificationType.DOCUMENT_PROCESSED: "success",
            NotificationType.ANALYSIS_COMPLETE: "success",
            NotificationType.EXPORT_READY: "success",
            NotificationType.PLAN_CANCELLED: "warning",
            NotificationType.PLAN_EXPIRED: "warning",
            NotificationType.PAYMENT_FAILED: "error",
            NotificationType.PAYMENT_DUE: "warning",
        }
        
        return {
            "type": toast_type_map.get(notification_type, "info"),
            "title": messages.get("title", "Notification").format(**kwargs),
            "message": messages.get("toast", "").format(**kwargs),
            "duration": 5000,  # 5 seconds
            "dismissible": True,
        }


notification_service = NotificationService()

__all__ = [
    'NotificationType',
    'NotificationService',
    'ToastNotification',
    'notification_service',
    'NOTIFICATION_MESSAGES',
]
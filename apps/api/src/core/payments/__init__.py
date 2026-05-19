"""Payment Gateway Integration - Stripe & Razorpay"""

import logging
from typing import Optional, Dict, Any

# Import payment libraries - optional, will work if installed
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..config import settings

logger = logging.getLogger(__name__)


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"


class PaymentGateway:
    """Payment gateway manager"""
    
    def __init__(self):
        self.stripe_enabled = bool(settings.STRIPE_SECRET_KEY and STRIPE_AVAILABLE)
        self.razorpay_enabled = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET and RAZORPAY_AVAILABLE)
        
        # Initialize Stripe
        if self.stripe_enabled:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            logger.info("Stripe payment gateway initialized")
        else:
            logger.warning("Stripe not available - install stripe package")
        
        # Initialize Razorpay
        if self.razorpay_enabled:
            self.razorpay_client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            logger.info("Razorpay payment gateway initialized")
        else:
            logger.warning("Razorpay not available - install razorpay package")
    
    def get_available_gateways(self) -> Dict[str, bool]:
        return {
            "stripe": self.stripe_enabled,
            "razorpay": self.razorpay_enabled,
        }
    
    def create_checkout_session(
        self,
        provider: PaymentProvider,
        plan_name: str,
        amount: int,
        currency: str = "usd",
        tenant_id: str = None,
        customer_email: str = None,
    ) -> Dict[str, Any]:
        """Create payment checkout session"""
        
        if provider == PaymentProvider.STRIPE:
            return self._create_stripe_session(plan_name, amount, currency, tenant_id, customer_email)
        elif provider == PaymentProvider.RAZORPAY:
            return self._create_razorpay_order(plan_name, amount, currency, tenant_id, customer_email)
        
        raise ValueError(f"Payment provider {provider} not available")
    
    def _create_stripe_session(
        self,
        plan_name: str,
        amount: int,
        currency: str,
        tenant_id: str,
        customer_email: str = None
    ) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'TenderIQ {plan_name} Plan',
                        },
                        'unit_amount': amount * 100,  # Convert to cents
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{settings.APP_URL}/billing?success=true',
                cancel_url=f'{settings.APP_URL}/billing?canceled=true',
                customer_email=customer_email,
                metadata={
                    'tenant_id': tenant_id,
                    'plan': plan_name,
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
                'provider': 'stripe'
            }
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_razorpay_order(
        self,
        plan_name: str,
        amount: int,
        currency: str,
        tenant_id: str,
        customer_email: str = None
    ) -> Dict[str, Any]:
        """Create Razorpay order"""
        
        try:
            amount_paise = amount * 100  # Razorpay uses paise
            
            order = self.razorpay_client.order.create({
                'amount': amount_paise,
                'currency': currency.upper(),
                'receipt': f'tenant_{tenant_id}_{datetime.utcnow().timestamp()}',
                'notes': {
                    'tenant_id': tenant_id,
                    'plan': plan_name,
                }
            })
            
            return {
                'success': True,
                'order_id': order['id'],
                'amount': amount,
                'checkout_url': f'https://razorpay.com/pay/{order["id"]}',
                'provider': 'razorpay'
            }
        except Exception as e:
            logger.error(f"Razorpay order error: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_payment(
        self,
        provider: PaymentProvider,
        payment_id: str,
        amount: int = None
    ) -> Dict[str, Any]:
        """Verify payment was successful"""
        
        if provider == PaymentProvider.STRIPE:
            try:
                session = stripe.checkout.Session.retrieve(payment_id)
                return {
                    'success': session.payment_status == 'paid',
                    'customer_email': session.customer_email,
                    'subscription_id': session.subscription
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        elif provider == PaymentProvider.RAZORPAY:
            try:
                payment = self.razorpay_client.payment.fetch(payment_id)
                return {
                    'success': payment['status'] == 'captured',
                    'amount': payment['amount'] / 100,
                    'order_id': payment['order_id']
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Unknown provider'}
    
    def create_customer(
        self,
        provider: PaymentProvider,
        email: str,
        name: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Create customer in payment gateway"""
        
        if provider == PaymentProvider.STRIPE:
            try:
                customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata={'tenant_id': tenant_id}
                )
                return {'success': True, 'customer_id': customer.id}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Razorpay doesn't need separate customer creation
        return {'success': True, 'customer_id': tenant_id}


# Invoice Generator
class InvoiceGenerator:
    """Generate invoices for tenants"""
    
    INVOICE_TEMPLATE = """
    ========================================
    TENDERIQ INVOICE
    ========================================
    
    Invoice #: {invoice_number}
    Date: {invoice_date}
    Due Date: {due_date}
    
    ----------------------------------------
    BILL TO:
    ----------------------------------------
    Company: {tenant_name}
    Email: {tenant_email}
    
    ----------------------------------------
    PLAN DETAILS:
    ----------------------------------------
    Plan: {plan_name}
    Billing Cycle: {billing_cycle}
    Amount: {amount} {currency}
    
    ----------------------------------------
    SERVICES INCLUDED:
    ----------------------------------------
    {services}
    
    ----------------------------------------
    SUMMARY:
    ----------------------------------------
    Subtotal: {amount} {currency}
    Tax (0%): 0.00 {currency}
    Total: {amount} {currency}
    
    ========================================
    Payment Methods:
    - Stripe: stripe.com
    - Razorpay: razorpay.com
    
    Thank you for your business!
    ========================================
    """
    
    @staticmethod
    def generate_invoice(
        invoice_number: str,
        tenant_name: str,
        tenant_email: str,
        plan_name: str,
        billing_cycle: str,
        amount: float,
        currency: str = "USD",
        services: list = None
    ) -> str:
        """Generate invoice text"""
        
        return InvoiceGenerator.INVOICE_TEMPLATE.format(
            invoice_number=invoice_number,
            invoice_date=datetime.now().strftime("%Y-%m-%d"),
            due_date=datetime.now().strftime("%Y-%m-%d"),
            tenant_name=tenant_name,
            tenant_email=tenant_email,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            amount=f"{amount:.2f}",
            currency=currency,
            services="\n".join([f"    - {s}" for s in (services or ["Basic Access"])])
        )


# Payment Service
payment_gateway = PaymentGateway()

__all__ = [
    'PaymentProvider',
    'PaymentGateway',
    'InvoiceGenerator',
    'payment_gateway',
]
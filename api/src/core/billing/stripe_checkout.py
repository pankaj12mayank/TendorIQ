"""Stripe Checkout (HTTP API — no stripe SDK required)."""

from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .fe_responses import normalize_plan_id
from .razorpay_lite import plan_amount_paise

logger = logging.getLogger(__name__)


def _stripe_request(secret: str, method: str, path: str, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    url = f'https://api.stripe.com/v1/{path.lstrip("/")}'
    body = urllib.parse.urlencode(_flatten_params(data or {})).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, method=method)
    token = base64.b64encode(f'{secret}:'.encode('utf-8')).decode('ascii')
    req.add_header('Authorization', f'Basic {token}')
    if body:
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        logger.warning('Stripe API error %s: %s', exc.code, detail[:500])
        raise ValueError('Payment could not be started. Please try again.') from exc


def _flatten_params(data: dict[str, Any], prefix: str = '') -> dict[str, str]:
    out: dict[str, str] = {}
    for key, val in data.items():
        full = f'{prefix}[{key}]' if prefix else key
        if isinstance(val, dict):
            out.update(_flatten_params(val, full))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    out.update(_flatten_params(item, f'{full}[{i}]'))
                else:
                    out[f'{full}[{i}]'] = str(item)
        elif val is not None:
            out[full] = str(val)
    return out


def create_checkout_session(
    *,
    secret_key: str,
    tenant_id: str,
    plan_id: str,
    billing_interval: str,
    success_url: str,
    cancel_url: str,
    pricing: dict | None = None,
    customer_email: Optional[str] = None,
) -> dict[str, Any]:
    api_plan = normalize_plan_id(plan_id)
    amount_cents = plan_amount_paise(plan_id, billing_interval, pricing=pricing)
    currency = 'usd'
    payload: dict[str, Any] = {
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'client_reference_id': tenant_id,
        'metadata': {
            'tenant_id': tenant_id,
            'plan_id': api_plan,
            'billing_interval': billing_interval,
        },
        'line_items': [
            {
                'quantity': 1,
                'price_data': {
                    'currency': currency,
                    'unit_amount': amount_cents,
                    'product_data': {'name': f'TenderIQ {api_plan.title()} plan'},
                },
            }
        ],
    }
    if customer_email:
        payload['customer_email'] = customer_email
    session = _stripe_request(secret_key, 'POST', 'checkout/sessions', payload)
    if not session.get('url'):
        raise ValueError('Payment could not be started. Please try again.')
    return {
        'session_id': session.get('id'),
        'checkout_url': session.get('url'),
        'plan': api_plan,
    }


def retrieve_checkout_session(secret_key: str, session_id: str) -> dict[str, Any]:
    url = f'https://api.stripe.com/v1/checkout/sessions/{session_id}'
    req = urllib.request.Request(url, method='GET')
    token = base64.b64encode(f'{secret_key}:'.encode('utf-8')).decode('ascii')
    req.add_header('Authorization', f'Basic {token}')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise ValueError('Could not verify payment') from exc

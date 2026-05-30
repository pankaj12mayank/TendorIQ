"""Platform settings defaults and pricing resolution."""

from src.core.platform.lite_settings import (
    DEFAULT_PRICING,
    _deep_merge,
    pricing_amount_paise,
)


def test_deep_merge_nested():
    base = {'hero': {'headline': 'A'}, 'faq': []}
    patch = {'hero': {'subheadline': 'B'}}
    merged = _deep_merge(base, patch)
    assert merged['hero']['headline'] == 'A'
    assert merged['hero']['subheadline'] == 'B'


def test_pricing_amount_paise_from_admin_plans():
    amount = pricing_amount_paise('starter', 'monthly', DEFAULT_PRICING)
    assert amount == 29 * 100


def test_pricing_amount_paise_fallback():
    amount = pricing_amount_paise('starter', 'monthly', None)
    assert amount == 2900

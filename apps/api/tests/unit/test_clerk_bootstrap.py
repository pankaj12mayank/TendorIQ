"""Layer 7 — Clerk bootstrap helpers."""

from src.core.clerk_bootstrap import _clerk_email, _clerk_name
from src.core.local_auth import login_user_payload


def test_clerk_email_from_addresses():
    email = _clerk_email(
        {
            'email_addresses': [{'email_address': 'User@Example.com'}],
        }
    )
    assert email == 'user@example.com'


def test_clerk_name_from_parts():
    assert _clerk_name({'first_name': 'Ada', 'last_name': 'Lovelace'}, 'a@b.com') == 'Ada Lovelace'


def test_login_payload_alias():
    """Clerk session uses same payload helper as local login."""
    user = login_user_payload(
        user_id='u1',
        email='a@b.com',
        name='A',
        role='member',
        membership_role='member',
        tenant_id='t1',
        is_super_admin=False,
    )
    assert user['user_id'] == user['id'] == 'u1'

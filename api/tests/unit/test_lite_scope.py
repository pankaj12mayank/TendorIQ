"""Lite user-scoping helpers."""

from uuid import uuid4

import pytest

from src.core.auth import AuthContext
from src.core.lite_scope import owner_filter_dict, user_owns_row
def test_owner_filter_dict_regular_user():
    auth = AuthContext(user_id=str(uuid4()), tenant_id=str(uuid4()), role='member')
    assert owner_filter_dict(auth) == {'owner_id': auth.user_id}


def test_owner_filter_dict_super_admin():
    auth = AuthContext(user_id='super_admin', role='super_admin')
    assert owner_filter_dict(auth) == {}


def test_user_owns_row_by_owner_id():
    uid = str(uuid4())

    class Row:
        owner_id = uid
        created_by_id = None

    assert user_owns_row(Row(), uid) is True
    assert user_owns_row(Row(), str(uuid4())) is False

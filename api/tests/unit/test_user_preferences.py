from src.core.local_user_auth import _password_hash
from src.core.models import User
from src.core.passwords import hash_password


def test_password_hash_from_json_string_preferences():
    user = User(
        email='a@b.com',
        preferences='{"password_hash": "' + hash_password('secret123') + '"}',
    )
    assert _password_hash(user) is not None

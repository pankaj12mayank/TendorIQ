"""Encrypted Secrets Management"""

import base64
import hashlib
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend

from ..config import settings


class SecretEncryptor:
    """Encrypt and decrypt sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or settings.JWT_SECRET
        self._fernet = self._generate_fernet(self.master_key)
    
    def _generate_fernet(self, key: str) -> Fernet:
        """Generate Fernet cipher from string key"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tenderiq_salt_v1',
            iterations=100000,
            backend=default_backend()
        )
        key_bytes = kdf.derive(key.encode())
        return Fernet(base64.urlsafe_b64encode(key_bytes))
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        encrypted = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return ""
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dictionary"""
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_dict(value)
            else:
                encrypted[key] = value
        return encrypted
    
    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt all encrypted string values in a dictionary"""
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str) and value and not value.startswith('ENC:'):
                try:
                    decrypted[key] = self.decrypt(value)
                except Exception:
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted


class SecretsManager:
    """Manage application secrets"""
    
    def __init__(self, encryptor: SecretEncryptor = None):
        self.encryptor = encryptor or SecretEncryptor()
        self._secrets_cache: dict = {}
    
    def store_secret(self, key: str, value: str, encrypt: bool = True) -> dict:
        """Store a secret"""
        if encrypt:
            encrypted_value = self.encryptor.encrypt(value)
            stored_value = f"ENC:{encrypted_value}"
        else:
            stored_value = value
        
        self._secrets_cache[key] = {
            'value': stored_value,
            'encrypted': encrypt,
            'updated_at': 'now'
        }
        
        return {'success': True, 'key': key}
    
    def get_secret(self, key: str, decrypt: bool = True) -> Optional[str]:
        """Retrieve a secret"""
        if key not in self._secrets_cache:
            return None
        
        stored = self._secrets_cache[key]
        
        if not decrypt:
            return stored['value']
        
        if stored.get('encrypted') and stored['value'].startswith('ENC:'):
            encrypted_part = stored['value'][4:]
            return self.encryptor.decrypt(encrypted_part)
        
        return stored['value']
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        if key in self._secrets_cache:
            del self._secrets_cache[key]
            return True
        return False
    
    def list_secrets(self) -> list[str]:
        """List all secret keys (not values)"""
        return list(self._secrets_cache.keys())
    
    def rotate_secret(self, key: str, new_value: str) -> dict:
        """Rotate a secret"""
        if key in self._secrets_cache:
            return self.store_secret(key, new_value, self._secrets_cache[key]['encrypted'])
        return {'success': False, 'error': 'Secret not found'}


class APIKeyManager:
    """Manage API keys with encryption"""
    
    def __init__(self, encryptor: SecretEncryptor = None):
        self.encryptor = encryptor or SecretEncryptor()
        self._keys: dict = {}
    
    def generate_key(
        self,
        user_id: str,
        name: str,
        scopes: list[str],
        expires_days: Optional[int] = None
    ) -> dict:
        """Generate a new API key"""
        import uuid
        from datetime import datetime, timedelta
        
        key_id = f"tq_{uuid.uuid4().hex[:8]}"
        raw_key = f"tq_{os.urandom(32).hex()}"
        
        encrypted_key = self.encryptor.encrypt(raw_key)
        
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        self._keys[key_id] = {
            'id': key_id,
            'user_id': user_id,
            'name': name,
            'key_hash': hashlib.sha256(raw_key.encode()).hexdigest(),
            'scopes': scopes,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': expires_at.isoformat() if expires_at else None,
            'last_used': None,
            'is_active': True
        }
        
        return {
            'key_id': key_id,
            'key': raw_key,
            'scopes': scopes,
            'expires_at': expires_at.isoformat() if expires_at else None
        }
    
    def validate_key(self, key: str) -> Optional[dict]:
        """Validate an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        for key_data in self._keys.values():
            if key_data['key_hash'] == key_hash and key_data['is_active']:
                if key_data['expires_at']:
                    from datetime import datetime
                    if datetime.fromisoformat(key_data['expires_at']) < datetime.utcnow():
                        return None
                return key_data
        
        return None
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self._keys:
            self._keys[key_id]['is_active'] = False
            return True
        return False
    
    def get_user_keys(self, user_id: str) -> list[dict]:
        """Get all keys for a user (without the actual key)"""
        return [
            {
                'id': k['id'],
                'name': k['name'],
                'scopes': k['scopes'],
                'created_at': k['created_at'],
                'expires_at': k['expires_at'],
                'last_used': k['last_used'],
                'is_active': k['is_active']
            }
            for k in self._values() if k['user_id'] == user_id
        ]


secret_encryptor = SecretEncryptor()
secrets_manager = SecretsManager()
api_key_manager = APIKeyManager()


def get_secret_encryptor() -> SecretEncryptor:
    return secret_encryptor


def get_secrets_manager() -> SecretsManager:
    return secrets_manager


def get_api_key_manager() -> APIKeyManager:
    return api_key_manager
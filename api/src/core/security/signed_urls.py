"""Signed URL Generation and Validation"""

import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from ..config import settings


class SignedURLGenerator:
    """Generate and validate signed URLs for secure resource access"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or settings.JWT_SECRET
    
    def generate(
        self,
        resource_path: str,
        expires_in: int = 3600,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        allowed_ips: Optional[list[str]] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Generate a signed URL"""
        
        expires_at = int(time.time()) + expires_in
        
        payload = {
            'path': resource_path,
            'exp': expires_at,
            'iat': int(time.time()),
        }
        
        if user_id:
            payload['uid'] = user_id
        if tenant_id:
            payload['tid'] = tenant_id
        if allowed_ips:
            payload['ips'] = allowed_ips
        if metadata:
            payload['meta'] = metadata
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(',', ':')).encode()
        ).decode()
        
        signature = hmac.new(
            self.secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signed_url = f"{resource_path}?sig={signature}&p={payload_b64}"
        
        return signed_url
    
    def validate(self, signed_url: str, client_ip: Optional[str] = None) -> Optional[dict]:
        """Validate a signed URL and return payload if valid"""
        
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(signed_url)
            query_params = parse_qs(parsed.query)
            
            if 'sig' not in query_params or 'p' not in query_params:
                return None
            
            signature = query_params['sig'][0]
            payload_b64 = query_params['p'][0]
            
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            payload = json.loads(
                base64.urlsafe_b64decode(payload_b64.encode()).decode()
            )
            
            if payload['exp'] < int(time.time()):
                return None
            
            if 'ips' in payload and client_ip:
                if client_ip not in payload['ips']:
                    return None
            
            return payload
            
        except Exception:
            return None
    
    def generate_presigned_upload(
        self,
        file_path: str,
        content_type: str,
        max_size_mb: int = 10,
        expires_in: int = 3600
    ) -> dict:
        """Generate presigned upload URL"""
        
        signed_url = self.generate(
            resource_path=file_path,
            expires_in=expires_in,
            metadata={
                'action': 'upload',
                'content_type': content_type,
                'max_size_mb': max_size_mb
            }
        )
        
        return {
            'upload_url': signed_url,
            'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
            'method': 'PUT',
            'headers': {
                'Content-Type': content_type
            }
        }
    
    def generate_presigned_download(
        self,
        file_path: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> dict:
        """Generate presigned download URL"""
        
        metadata = {'action': 'download'}
        if filename:
            metadata['filename'] = filename
            
        signed_url = self.generate(
            resource_path=file_path,
            expires_in=expires_in,
            metadata=metadata
        )
        
        return {
            'download_url': signed_url,
            'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
            'method': 'GET'
        }


signed_url_generator = SignedURLGenerator()


def get_signed_url_generator() -> SignedURLGenerator:
    return signed_url_generator


class SecureFileHandler:
    """Handle secure file operations with signed URLs"""
    
    def __init__(self, generator: SignedURLGenerator = None):
        self.generator = generator or signed_url_generator
    
    def get_upload_url(
        self,
        user_id: str,
        tenant_id: str,
        file_name: str,
        content_type: str,
        max_size_mb: int = 10
    ) -> dict:
        """Get secure upload URL"""
        
        resource_path = f'/api/v1/files/upload/{tenant_id}/{file_name}'
        
        return self.generator.generate_presigned_upload(
            file_path=resource_path,
            content_type=content_type,
            max_size_mb=max_size_mb
        )
    
    def get_download_url(
        self,
        user_id: str,
        tenant_id: str,
        file_id: str,
        filename: str
    ) -> dict:
        """Get secure download URL"""
        
        resource_path = f'/api/v1/files/{tenant_id}/{file_id}'
        
        return self.generator.generate_presigned_download(
            file_path=resource_path,
            filename=filename
        )
    
    def validate_request(
        self,
        signed_url: str,
        client_ip: str,
        expected_tenant_id: str
    ) -> tuple[bool, Optional[dict]]:
        """Validate signed URL and check tenant access"""
        
        payload = self.generator.validate(signed_url, client_ip)
        
        if not payload:
            return False, None
        
        if payload.get('tid') != expected_tenant_id:
            return False, None
        
        return True, payload


secure_file_handler = SecureFileHandler()


def get_secure_file_handler() -> SecureFileHandler:
    return secure_file_handler
"""S3/R2/local storage — boto3 runs in asyncio.to_thread; local uses disk."""

import asyncio
import hashlib
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from ..config import settings
from ..logging import get_logger
from .keys import assert_tenant_storage_key
from .tokens import create_storage_token

logger = get_logger('storage')


from ..upload_policy import LITE_MIME_BY_EXT

ALLOWED_MIME_TYPES = dict(LITE_MIME_BY_EXT)

MAX_FILENAME_LENGTH = 255
SANITIZE_PATTERN = re.compile(r'[^\w.\-]')


def _run_sync(fn, *args, **kwargs):
    return asyncio.to_thread(fn, *args, **kwargs)


class StorageService:
    _client: Optional[boto3.client] = None

    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        self.bucket = settings.STORAGE_BUCKET
        self.region = settings.STORAGE_REGION
        self.max_file_size = settings.max_file_size_bytes
        self.allowed_extensions = settings.allowed_extensions
        self._local_root = settings.resolved_storage_local_path

    @property
    def is_local(self) -> bool:
        return self.provider == 'local'

    def _local_path(self, storage_key: str) -> Path:
        normalized = storage_key.replace('\\', '/').lstrip('/')
        if '..' in normalized.split('/'):
            raise ValueError('Invalid storage key')
        path = (self._local_root / normalized).resolve()
        if not str(path).startswith(str(self._local_root)):
            raise ValueError('Invalid storage key path')
        return path

    @property
    def client(self) -> boto3.client:
        if self.is_local:
            raise RuntimeError('S3 client not used when STORAGE_PROVIDER=local')
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> boto3.client:
        client_kwargs = {
            'service_name': 's3',
            'region_name': self.region,
            'config': Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'},
            ),
        }

        if self.provider == 'r2':
            client_kwargs.update({
                'endpoint_url': settings.STORAGE_ENDPOINT_URL or f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                'aws_access_key_id': settings.R2_ACCESS_KEY_ID or settings.STORAGE_ACCESS_KEY,
                'aws_secret_access_key': settings.R2_SECRET_ACCESS_KEY or settings.STORAGE_SECRET_KEY,
            })
        elif self.provider in ('s3', 'local'):
            if settings.STORAGE_ENDPOINT_URL:
                client_kwargs['endpoint_url'] = settings.STORAGE_ENDPOINT_URL
            if settings.STORAGE_ACCESS_KEY and settings.STORAGE_SECRET_KEY:
                client_kwargs['aws_access_key_id'] = settings.STORAGE_ACCESS_KEY
                client_kwargs['aws_secret_access_key'] = settings.STORAGE_SECRET_KEY

        return boto3.client(**client_kwargs)

    def sanitize_filename(self, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        name = SANITIZE_PATTERN.sub('_', name).strip('._')
        ext = ext.lower()
        safe_name = f"{name[:MAX_FILENAME_LENGTH - len(ext)]}{ext}"
        return safe_name or f"file_{uuid4().hex[:8]}{ext}"

    def generate_storage_key(
        self,
        tenant_id: str,
        category: str = 'documents',
        filename: str = '',
        tender_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> str:
        date = datetime.now(timezone.utc).strftime('%Y/%m/%d')
        unique_id = uuid4().hex[:12]

        root = f'users/{owner_id}' if owner_id else tenant_id
        parts = [root, category, date]

        if tender_id:
            parts.append(f"tender-{tender_id}")

        if filename:
            safe_name = self.sanitize_filename(filename)
            parts.append(f"{unique_id}_{safe_name}")
        else:
            parts.append(unique_id)

        return '/'.join(parts)

    def validate_file(
        self,
        filename: str,
        file_size: int,
        content_type: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        if not filename:
            return False, 'Filename is required'

        _, ext = os.path.splitext(filename.lower())
        if ext not in self.allowed_extensions:
            return False, f'File type {ext} is not allowed. Allowed: {", ".join(self.allowed_extensions)}'

        if file_size > self.max_file_size:
            max_mb = settings.STORAGE_MAX_FILE_SIZE_MB
            return False, f'File size exceeds {max_mb}MB limit'

        if file_size == 0:
            return False, 'File is empty'

        return True, None

    def compute_checksum(self, file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    async def read_file(self, storage_key: str) -> dict:
        """Read object bytes (local disk or S3 download)."""
        if self.is_local:
            try:
                path = self._local_path(storage_key)

                def _read() -> bytes:
                    return path.read_bytes()

                content = await _run_sync(_read)
                return {'success': True, 'content': content, 'storage_key': storage_key}
            except Exception as e:
                return {'success': False, 'error': str(e), 'storage_key': storage_key}

        try:
            response = await _run_sync(
                self.client.get_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            body = response['Body'].read()
            return {'success': True, 'content': body, 'storage_key': storage_key}
        except ClientError as e:
            return {'success': False, 'error': str(e), 'storage_key': storage_key}

    async def upload_file(
        self,
        file_content: bytes,
        storage_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        acl: Optional[str] = None,
    ) -> dict:
        if self.is_local:
            try:
                path = self._local_path(storage_key)
                path.parent.mkdir(parents=True, exist_ok=True)

                def _write() -> None:
                    path.write_bytes(file_content)

                await _run_sync(_write)
                return {
                    'success': True,
                    'storage_key': storage_key,
                    'file_size': len(file_content),
                    'checksum': self.compute_checksum(file_content),
                    'content_type': content_type,
                }
            except Exception as e:
                logger.error('Local upload failed: %s', e, storage_key=storage_key)
                return {'success': False, 'error': str(e), 'storage_key': storage_key}

        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
            if acl:
                extra_args['ACL'] = acl

            await _run_sync(
                self.client.put_object,
                Bucket=self.bucket,
                Key=storage_key,
                Body=file_content,
                **extra_args,
            )

            file_size = len(file_content)
            checksum = self.compute_checksum(file_content)

            return {
                'success': True,
                'storage_key': storage_key,
                'file_size': file_size,
                'checksum': checksum,
                'content_type': content_type,
            }

        except ClientError as e:
            logger.error(f'Upload failed: {e}', storage_key=storage_key)
            return {
                'success': False,
                'error': str(e),
                'storage_key': storage_key,
            }

    async def delete_file(self, storage_key: str) -> dict:
        if self.is_local:
            try:
                path = self._local_path(storage_key)

                def _delete() -> None:
                    if path.is_file():
                        path.unlink()

                await _run_sync(_delete)
                return {'success': True, 'storage_key': storage_key}
            except Exception as e:
                return {'success': False, 'error': str(e)}

        try:
            await _run_sync(
                self.client.delete_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            logger.info(f'File deleted', storage_key=storage_key)
            return {'success': True, 'storage_key': storage_key}

        except ClientError as e:
            logger.error(f'Delete failed: {e}', storage_key=storage_key)
            return {'success': False, 'error': str(e)}

    async def delete_files_batch(self, storage_keys: list[str]) -> dict:
        if self.is_local:
            deleted = 0
            for key in storage_keys:
                result = await self.delete_file(key)
                if result.get('success'):
                    deleted += 1
            return {'success': True, 'deleted': deleted}

        try:
            if not storage_keys:
                return {'success': True, 'deleted': 0}

            objects = [{'Key': key} for key in storage_keys]
            await _run_sync(
                self.client.delete_objects,
                Bucket=self.bucket,
                Delete={'Objects': objects},
            )
            logger.info(f'Batch delete completed', count=len(storage_keys))
            return {'success': True, 'deleted': len(storage_keys)}

        except ClientError as e:
            logger.error(f'Batch delete failed: {e}')
            return {'success': False, 'error': str(e)}

    async def generate_signed_upload_url(
        self,
        storage_key: str,
        content_type: Optional[str] = None,
        expires_seconds: Optional[int] = None,
    ) -> dict:
        expire = expires_seconds or settings.STORAGE_SIGNED_URL_EXPIRE_SECONDS
        expiration = datetime.now(timezone.utc) + timedelta(seconds=expire)

        if self.is_local:
            token = create_storage_token(storage_key, 'put', expire)
            encoded_key = storage_key.replace('/', '%2F')
            upload_url = (
                f'{settings.api_url}/api/v1/files/blob/{encoded_key}'
                f'?token={token}'
            )
            return {
                'success': True,
                'upload_url': upload_url,
                'storage_key': storage_key,
                'expires_at': expiration.isoformat(),
                'expires_in': expire,
            }

        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type

            presigned_url = await _run_sync(
                self.client.generate_presigned_url,
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key,
                },
                ExpiresIn=expire,
            )

            return {
                'success': True,
                'upload_url': presigned_url,
                'storage_key': storage_key,
                'expires_at': expiration.isoformat(),
                'expires_in': expire,
            }

        except ClientError as e:
            logger.error(f'Signed URL generation failed: {e}')
            return {'success': False, 'error': str(e)}

    async def generate_signed_download_url(
        self,
        storage_key: str,
        expires_seconds: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> dict:
        expire = expires_seconds or settings.STORAGE_SIGNED_URL_EXPIRE_SECONDS
        expiration = datetime.now(timezone.utc) + timedelta(seconds=expire)

        if self.is_local:
            token = create_storage_token(storage_key, 'get', expire)
            encoded_key = storage_key.replace('/', '%2F')
            q = f'token={token}'
            if filename:
                from urllib.parse import quote

                q += f'&filename={quote(filename)}'
            download_url = f'{settings.api_url}/api/v1/files/blob/{encoded_key}?{q}'
            return {
                'success': True,
                'download_url': download_url,
                'storage_key': storage_key,
                'expires_at': expiration.isoformat(),
                'expires_in': expire,
            }

        try:
            extra_args = {}
            if filename:
                extra_args['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

            signed_url = await _run_sync(
                self.client.generate_presigned_url,
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': storage_key,
                    **extra_args,
                },
                ExpiresIn=expire,
            )

            return {
                'success': True,
                'download_url': signed_url,
                'storage_key': storage_key,
                'expires_at': expiration.isoformat(),
                'expires_in': expire,
            }

        except ClientError as e:
            logger.error(f'Download URL generation failed: {e}')
            return {'success': False, 'error': str(e)}

    async def get_file_metadata(self, storage_key: str) -> dict:
        if self.is_local:
            try:
                path = self._local_path(storage_key)

                def _stat():
                    st = path.stat()
                    return st.st_size, st.st_mtime

                size, mtime = await _run_sync(_stat)
                return {
                    'success': True,
                    'storage_key': storage_key,
                    'content_length': size,
                    'content_type': self.get_mime_type(path.name),
                    'last_modified': datetime.fromtimestamp(mtime, tz=timezone.utc),
                }
            except FileNotFoundError:
                return {'success': False, 'error': 'not found'}
            except Exception as e:
                return {'success': False, 'error': str(e)}

        try:
            response = await _run_sync(
                self.client.head_object,
                Bucket=self.bucket,
                Key=storage_key,
            )
            return {
                'success': True,
                'storage_key': storage_key,
                'content_length': response.get('ContentLength', 0),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
            }
        except ClientError as e:
            return {'success': False, 'error': str(e)}

    async def copy_file(
        self,
        source_key: str,
        destination_key: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        try:
            copy_source = {'Bucket': self.bucket, 'Key': source_key}

            extra_args = {}
            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
                extra_args['MetadataDirective'] = 'REPLACE'

            await _run_sync(
                self.client.copy_object,
                Bucket=self.bucket,
                Key=destination_key,
                CopySource=copy_source,
                **extra_args,
            )
            return {'success': True, 'source': source_key, 'destination': destination_key}

        except ClientError as e:
            logger.error(f'Copy failed: {e}', source=source_key, dest=destination_key)
            return {'success': False, 'error': str(e)}

    def get_mime_type(self, filename: str) -> str:
        _, ext = os.path.splitext(filename.lower())
        return ALLOWED_MIME_TYPES.get(ext, 'application/octet-stream')

    async def list_files(
        self,
        prefix: str,
        max_keys: int = 100,
        continuation_token: Optional[str] = None,
    ) -> dict:
        try:
            kwargs = {
                'Bucket': self.bucket,
                'Prefix': prefix,
                'MaxKeys': max_keys,
            }
            if continuation_token:
                kwargs['ContinuationToken'] = continuation_token

            response = await _run_sync(self.client.list_objects_v2, **kwargs)

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"'),
                })

            return {
                'success': True,
                'files': files,
                'prefix': prefix,
                'is_truncated': response.get('IsTruncated', False),
                'next_token': response.get('NextContinuationToken'),
            }

        except ClientError as e:
            logger.error(f'List files failed: {e}', prefix=prefix)
            return {'success': False, 'error': str(e)}

    async def lifecycle_cleanup(self, tenant_id: str, days_old: int = 90) -> dict:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
            cutoff_str = cutoff.strftime('%Y/%m/%d')
            prefix = f'{tenant_id}/'

            response = await _run_sync(
                self.client.list_objects_v2,
                Bucket=self.bucket,
                Prefix=prefix,
            )

            objects_to_delete = []
            deleted_count = 0

            for obj in response.get('Contents', []):
                if obj['LastModified'] < cutoff:
                    objects_to_delete.append({'Key': obj['Key']})
                    deleted_count += 1

                if len(objects_to_delete) >= 1000:
                    await _run_sync(
                        self.client.delete_objects,
                        Bucket=self.bucket,
                        Delete={'Objects': objects_to_delete},
                    )
                    objects_to_delete = []

            if objects_to_delete:
                await _run_sync(
                    self.client.delete_objects,
                    Bucket=self.bucket,
                    Delete={'Objects': objects_to_delete},
                )

            logger.info(f'Lifecycle cleanup completed', tenant_id=tenant_id, deleted=deleted_count)
            return {'success': True, 'deleted': deleted_count, 'cutoff': cutoff_str}

        except ClientError as e:
            logger.error(f'Lifecycle cleanup failed: {e}', tenant_id=tenant_id)
            return {'success': False, 'error': str(e)}


storage_service = StorageService()
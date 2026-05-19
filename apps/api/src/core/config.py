"""Application Configuration - Centralized Settings Management"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # ===========================================
    # COMMON
    # ===========================================
    APP_NAME: str = 'TenderIQ'
    VERSION: str = '1.0.0'
    NODE_ENV: Literal['development', 'staging', 'production'] = 'development'
    LOG_LEVEL: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    LOG_FORMAT: Literal['json', 'text'] = 'text'

    # ===========================================
    # API
    # ===========================================
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1
    API_PREFIX: str = '/api/v1'

    # ===========================================
    # DATABASE
    # ===========================================
    DATABASE_URL: str = (
        'mysql+aiomysql://root:root@localhost:3306/tenderiq?charset=utf8mb4'
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_POOL_RECYCLE: int = 3600

    # Queue settings (in-process; no Redis)
    QUEUE_NAME_PREFIX: str = 'tendoriq'
    QUEUE_DEFAULT_TIMEOUT: int = 300
    QUEUE_MAX_RETRIES: int = 3
    QUEUE_RETRY_DELAYS: list[int] = [30, 120, 600]
    QUEUE_DEAD_LETTER_TTL: int = 604800

    # ===========================================
    # CORS
    # ===========================================
    CORS_ORIGINS: str = 'http://localhost:3000'
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ['*']
    CORS_ALLOW_HEADERS: list[str] = ['*']

    # ===========================================
    # AUTH
    # ===========================================
    AUTH_PROVIDER: Literal['clerk', 'supabase'] = 'clerk'
    CLERK_SECRET_KEY: str = ''
    CLERK_WEBHOOK_SECRET: str = ''

    JWT_SECRET: str = 'dev-secret-change-in-production-min-32-chars'
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===========================================
    # OBSERVABILITY
    # ===========================================
    SENTRY_DSN: str = ''
    SENTRY_ENVIRONMENT: str = 'development'
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_PROFILING_SAMPLE_RATE: float = 0

    # ===========================================
    # AI
    # ===========================================
    AI_PROVIDER: Literal['openai', 'anthropic', 'azure'] = 'openai'
    AI_API_KEY: str = ''
    AI_MODEL: str = 'gpt-4'
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.7

    # Azure-specific
    AZURE_OPENAI_ENDPOINT: str = ''
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ''

    # ===========================================
    # EMAIL
    # ===========================================
    EMAIL_PROVIDER: Literal['resend', 'sendgrid', 'smtp'] = 'resend'
    EMAIL_API_KEY: str = ''
    EMAIL_FROM: str = 'noreply@tendoriq.com'
    EMAIL_FROM_NAME: str = 'TenderIQ'
    FRONTEND_URL: str = 'http://localhost:3000'
    SUPER_ADMIN_EMAIL: str = 'admin@tenderiq.com'
    SUPER_ADMIN_PASSWORD: str = 'changeme'

    # SMTP
    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''

    # ===========================================
    # STORAGE
    # ===========================================
    STORAGE_PROVIDER: Literal['s3', 'r2', 'local'] = 'local'
    STORAGE_BUCKET: str = 'tendoriq-uploads'
    STORAGE_REGION: str = 'us-east-1'
    STORAGE_ACCESS_KEY: str = ''
    STORAGE_SECRET_KEY: str = ''
    STORAGE_ENDPOINT_URL: str = ''
    R2_ACCOUNT_ID: str = ''
    R2_ACCESS_KEY_ID: str = ''
    R2_SECRET_ACCESS_KEY: str = ''
    STORAGE_SIGNED_URL_EXPIRE_SECONDS: int = 3600
    STORAGE_MAX_FILE_SIZE_MB: int = 50
    STORAGE_ALLOWED_EXTENSIONS: str = '.pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.txt,.csv'

    # ===========================================
    # RATE LIMITING
    # ===========================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # ===========================================
    # FEATURE FLAGS
    # ===========================================
    FEATURE_AI_ANALYSIS: bool = True
    FEATURE_DOCUMENT_OCR: bool = False
    FEATURE_ADVANCED_ANALYTICS: bool = False
    FEATURE_WEBHOOKS: bool = True
    FEATURE_API_ACCESS: bool = True
    FEATURE_CUSTOM_DOMAINS: bool = False
    FEATURE_SSO: bool = False

    # ===========================================
    # RAILWAY
    # ===========================================
    RAILWAY_SERVICE_NAME: str = ''
    RAILWAY_PUBLIC_DOMAIN: str = ''

    # ===========================================
    # VERCEL
    # ===========================================
    VERCEL: bool = False
    VERCEL_ENV: str = ''
    VERCEL_DEPLOYMENT_URL: str = ''

    # ===========================================
    # INTERNAL
    # ===========================================
    INTERNAL_API_KEY: str = ''
    ENCRYPTION_KEY: str = ''

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]

    @property
    def is_development(self) -> bool:
        return self.NODE_ENV == 'development'

    @property
    def is_staging(self) -> bool:
        return self.NODE_ENV == 'staging'

    @property
    def is_production(self) -> bool:
        return self.NODE_ENV == 'production'

    @property
    def is_railway(self) -> bool:
        return bool(self.RAILWAY_SERVICE_NAME)

    @property
    def is_vercel(self) -> bool:
        return self.VERCEL or bool(self.VERCEL_DEPLOYMENT_URL)

    @property
    def api_url(self) -> str:
        if self.is_railway and self.RAILWAY_PUBLIC_DOMAIN:
            return f'https://{self.RAILWAY_PUBLIC_DOMAIN}'
        if self.is_vercel and self.VERCEL_DEPLOYMENT_URL:
            return f'https://{self.VERCEL_DEPLOYMENT_URL}'
        return f'http://{self.HOST}:{self.PORT}'

    @property
    def allowed_extensions(self) -> list[str]:
        return [e.strip().lower() for e in self.STORAGE_ALLOWED_EXTENSIONS.split(',')]

    @property
    def max_file_size_bytes(self) -> int:
        return self.STORAGE_MAX_FILE_SIZE_MB * 1024 * 1024

    @field_validator('JWT_SECRET')
    @classmethod
    def validate_jwt_secret(cls, v):
        if hasattr(v, '__str__'):
            v = str(v)
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters')
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        if hasattr(v, 'scheme'):
            v = str(v)
        if not v.startswith(('mysql', 'mariadb')):
            raise ValueError(
                'DATABASE_URL must be MySQL '
                '(e.g. mysql+aiomysql://user:pass@host:3306/db?charset=utf8mb4)'
            )
        return v

    @property
    def database_url_sync(self) -> str:
        """Sync driver URL for Alembic (pymysql)."""
        url = self.DATABASE_URL
        if '+aiomysql' in url:
            return url.replace('+aiomysql', '+pymysql')
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
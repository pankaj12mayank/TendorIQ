"""Application Configuration - Centralized Settings Management"""

from pathlib import Path
from typing import Any, Literal, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Monorepo root .env (run.bat / uvicorn cwd may be tendoriq/api)
import os

# config.py → core → src → api → repo root (tendoriq/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DOTENV_OVERRIDE = os.environ.get('DOTENV_PATH', '').strip()
_ENV_FILE = (
    Path(_DOTENV_OVERRIDE)
    if _DOTENV_OVERRIDE and Path(_DOTENV_OVERRIDE).is_file()
    else _PROJECT_ROOT / '.env'
)


def default_sqlite_path() -> Path:
    return _PROJECT_ROOT / '.tenderiq' / 'data' / 'tenderiq.db'


def build_sqlite_database_url(path: Path | None = None) -> str:
    db_file = (path or default_sqlite_path()).resolve()
    return f'sqlite+aiosqlite:///{db_file.as_posix()}'


def build_mysql_database_url(
    *,
    user: str = 'root',
    password: str = '',
    host: str = 'localhost',
    port: int = 3306,
    database: str = 'tenderiq',
) -> str:
    """Build DATABASE_URL with proper encoding (@ and special chars in password)."""
    return (
        f'mysql+aiomysql://{quote_plus(user)}:{quote_plus(password)}'
        f'@{host}:{port}/{database}?charset=utf8mb4'
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.is_file() else '.env',
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
    # sqlite = zero-install local file DB (default dev). mysql = production / advanced local.
    DATABASE_DRIVER: Literal['sqlite', 'mysql'] = 'sqlite'
    SQLITE_PATH: str = ''
    # MySQL only (ignored when DATABASE_DRIVER=sqlite):
    MYSQL_HOST: str = 'localhost'
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = 'root'
    MYSQL_PASSWORD: str = ''
    MYSQL_DATABASE: str = 'tenderiq'
    DATABASE_URL: str = ''  # Set directly, or leave empty when MYSQL_PASSWORD is set
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
    CORS_ALLOW_METHODS: str = 'GET,POST,PUT,PATCH,DELETE,OPTIONS'
    CORS_ALLOW_HEADERS: str = (
        'Authorization,Content-Type,Accept,X-Tenant-ID,X-Tenant-Slug,X-Request-ID'
    )
    EXPOSE_ERROR_DETAILS: bool = False

    # ===========================================
    # AUTH
    # ===========================================
    AUTH_PROVIDER: Literal['local', 'clerk'] = 'local'
    CLERK_SECRET_KEY: str = ''
    CLERK_WEBHOOK_SECRET: str = ''

    JWT_SECRET: str = ''  # Must be set in .env (min 32 chars)
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 1

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
    AI_PROVIDER: Literal['openai', 'anthropic', 'azure', 'gemini', 'ollama'] = 'openai'
    AI_API_KEY: str = ''
    AI_MODEL: str = 'gpt-4'
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.7
    AI_DEFAULT_PROVIDER: str = ''
    AI_DEFAULT_MODEL: str = ''
    AI_AUTO_ANALYZE_ON_UPLOAD: bool = True

    # Lite export (Phase 6) — PDF only in MVP
    LITE_EXPORT_PDF_ONLY: bool = True

    # Provider API keys (any one enables Phase 4 analysis)
    OPENAI_API_KEY: str = ''
    ANTHROPIC_API_KEY: str = ''
    GEMINI_API_KEY: str = ''
    GOOGLE_API_KEY: str = ''
    OLLAMA_BASE_URL: str = 'http://localhost:11434'

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
    RESEND_WEBHOOK_SECRET: str = ''
    FRONTEND_URL: str = 'http://localhost:3000'

    # Default system owner (seed only — login always checks database password_hash)
    SYSTEM_OWNER_EMAIL: str = 'admin@tendoriq.com'
    SYSTEM_OWNER_DEFAULT_PASSWORD: str = 'Owner@ChangeMe123'
    SYSTEM_OWNER_NAME: str = 'System Owner'

    # SMTP
    SMTP_HOST: str = ''
    SMTP_PORT: int = 587
    SMTP_USER: str = ''
    SMTP_PASSWORD: str = ''

    # ===========================================
    # STORAGE
    # ===========================================
    STORAGE_PROVIDER: Literal['s3', 'r2', 'local'] = 'local'
    STORAGE_LOCAL_PATH: str = './uploads'
    STORAGE_BUCKET: str = 'tendoriq-uploads'
    STORAGE_REGION: str = 'us-east-1'
    STORAGE_ACCESS_KEY: str = ''
    STORAGE_SECRET_KEY: str = ''
    STORAGE_ENDPOINT_URL: str = ''
    R2_ACCOUNT_ID: str = ''
    R2_ACCESS_KEY_ID: str = ''
    R2_SECRET_ACCESS_KEY: str = ''
    STORAGE_SIGNED_URL_EXPIRE_SECONDS: int = 3600
    STORAGE_TOKEN_CLOCK_SKEW_SECONDS: int = 120
    STORAGE_MAX_FILE_SIZE_MB: int = 25
    STORAGE_ALLOWED_EXTENSIONS: str = '.pdf,.doc,.docx'

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
    # PAYMENTS (optional — configure in Super Admin / billing)
    # ===========================================
    STRIPE_SECRET_KEY: str = ''
    STRIPE_WEBHOOK_SECRET: str = ''
    RAZORPAY_KEY_ID: str = ''
    RAZORPAY_KEY_SECRET: str = ''
    RAZORPAY_CURRENCY: str = 'USD'
    # When false (default in development), only monthly quotas apply — not subscription expiry.
    BILLING_ENFORCE_SUBSCRIPTION_EXPIRY: bool = False

    # ===========================================
    # INTERNAL
    # ===========================================
    INTERNAL_API_KEY: str = ''
    ENCRYPTION_KEY: str = ''

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        raw = self.CORS_ALLOW_METHODS
        if isinstance(raw, list):
            return raw
        return [m.strip().upper() for m in str(raw).split(',') if m.strip()]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        raw = self.CORS_ALLOW_HEADERS
        if isinstance(raw, list):
            return raw
        return [h.strip() for h in str(raw).split(',') if h.strip()]

    @property
    def expose_error_details(self) -> bool:
        return self.EXPOSE_ERROR_DETAILS or self.is_development

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
    def billing_enforce_subscription_expiry(self) -> bool:
        """Block usage when paid plan expired (production should set env true)."""
        if self.BILLING_ENFORCE_SUBSCRIPTION_EXPIRY:
            return True
        return self.is_production

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

    @property
    def resolved_storage_local_path(self) -> Path:
        """Absolute local disk root (STORAGE_LOCAL_PATH is normalized at load)."""
        return Path(self.STORAGE_LOCAL_PATH)

    @field_validator('STORAGE_LOCAL_PATH')
    @classmethod
    def normalize_storage_local_path(cls, v: str) -> str:
        from .local_storage_paths import resolve_storage_local_path

        return str(resolve_storage_local_path(v))

    @field_validator('JWT_SECRET')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v:
            raise ValueError('JWT_SECRET must be set in .env (min 32 characters)')
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters')
        return v

    @field_validator('STORAGE_PROVIDER', mode='before')
    @classmethod
    def normalize_storage_provider(cls, v: object) -> object:
        if v is None or v == '':
            return 'local'
        return v

    @model_validator(mode='before')
    @classmethod
    def assemble_database_url(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        driver = str(
            data.get('DATABASE_DRIVER') or os.environ.get('DATABASE_DRIVER') or 'sqlite'
        ).strip().lower()
        if driver == 'sqlite':
            custom = (data.get('SQLITE_PATH') or os.environ.get('SQLITE_PATH') or '').strip()
            path = Path(custom) if custom else default_sqlite_path()
            data['DATABASE_URL'] = build_sqlite_database_url(path)
            return data
        pwd = (data.get('MYSQL_PASSWORD') or os.environ.get('MYSQL_PASSWORD') or '').strip()
        if not pwd:
            return data
        host = str(data.get('MYSQL_HOST') or os.environ.get('MYSQL_HOST') or 'localhost').strip()
        port_raw = data.get('MYSQL_PORT') or os.environ.get('MYSQL_PORT') or 3306
        user = str(data.get('MYSQL_USER') or os.environ.get('MYSQL_USER') or 'root').strip()
        database = str(
            data.get('MYSQL_DATABASE') or os.environ.get('MYSQL_DATABASE') or 'tenderiq'
        ).strip()
        data['DATABASE_URL'] = build_mysql_database_url(
            user=user,
            password=pwd,
            host=host,
            port=int(port_raw),
            database=database,
        )
        return data

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError(
                'Set MYSQL_PASSWORD in .env (recommended) or DATABASE_URL '
                '(encode @ in passwords as %40)'
            )
        if v.startswith('sqlite'):
            return v
        if not v.startswith(('mysql', 'mariadb')):
            raise ValueError(
                'DATABASE_URL must be sqlite+aiosqlite://... or mysql+aiomysql://...'
            )
        return v

    @model_validator(mode='after')
    def validate_production_database(self) -> 'Settings':
        if self.NODE_ENV == 'production' and self.uses_sqlite:
            raise ValueError('Use DATABASE_DRIVER=mysql in production (SQLite is dev-only)')
        return self

    @property
    def uses_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith('sqlite')

    @property
    def resend_api_key_configured(self) -> bool:
        """True when Resend can send via env (EMAIL_API_KEY or RESEND_API_KEY)."""
        import os

        key = (os.environ.get('RESEND_API_KEY') or self.EMAIL_API_KEY or '').strip()
        return bool(key) and 'placeholder' not in key.lower()

    @property
    def database_url_sync(self) -> str:
        """Sync driver URL for Alembic / scripts."""
        url = self.DATABASE_URL
        if '+aiomysql' in url:
            return url.replace('+aiomysql', '+pymysql')
        if '+aiosqlite' in url:
            return url.replace('+aiosqlite', '')
        return url


def get_settings() -> Settings:
    """Load settings; monorepo root .env wins over stale process env."""
    env_path = _ENV_FILE
    if not env_path.is_file():
        fallback = Path.cwd() / '.env'
        if fallback.is_file():
            env_path = fallback
    if env_path.is_file():
        load_dotenv(env_path, override=True)
    return Settings()


settings = get_settings()
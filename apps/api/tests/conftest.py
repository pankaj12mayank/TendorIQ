"""Shared pytest environment defaults (no .env required for unit/contract tests)."""

from __future__ import annotations

import os

os.environ.setdefault(
    'DATABASE_URL',
    'mysql+aiomysql://root:pass@127.0.0.1:3306/tendoriq_test?charset=utf8mb4',
)
os.environ.setdefault('JWT_SECRET', 'test-secret-key-at-least-32-chars-long-for-pytest')
os.environ.setdefault('NODE_ENV', 'development')
os.environ.setdefault('EXPOSE_ERROR_DETAILS', 'false')

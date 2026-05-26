"""Integration tests use project SQLite (not MySQL from root conftest)."""

from __future__ import annotations

import os
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
os.environ['DATABASE_DRIVER'] = 'sqlite'
os.environ['DOTENV_PATH'] = str(_root.parent / '.env')
os.environ.pop('DATABASE_URL', None)
os.environ.setdefault('JWT_SECRET', 'test-secret-key-at-least-32-chars-long-for-pytest')
os.environ['NODE_ENV'] = 'development'
os.environ['RATE_LIMIT_ENABLED'] = 'false'

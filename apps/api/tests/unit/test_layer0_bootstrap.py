"""Layer 0 — bootstrap and database-unavailable login."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError


def _load_ensure_mysql():
    path = Path(__file__).resolve().parents[2] / 'scripts' / 'ensure_mysql.py'
    spec = importlib.util.spec_from_file_location('ensure_mysql', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_parse_mysql_url_from_aiomysql_dsn():
    mod = _load_ensure_mysql()
    cfg = mod._parse_mysql_url('mysql+aiomysql://root:secret@localhost:3306/tenderiq?charset=utf8mb4')
    assert cfg['host'] == 'localhost'
    assert cfg['port'] == 3306
    assert cfg['user'] == 'root'
    assert cfg['password'] == 'secret'
    assert cfg['database'] == 'tenderiq'


def test_login_maps_operational_error_to_503():
    from src.api.routers.auth import _database_unavailable

    exc = _database_unavailable(OperationalError('stmt', {}, Exception('connection refused')))
    assert exc.status_code == 503
    assert 'Database is unavailable' in exc.detail

"""Config paths resolve to tendoriq repo root (not parent Py_Projects)."""

from pathlib import Path

from src.core.config import _PROJECT_ROOT, default_sqlite_path


def test_project_root_is_tendoriq_folder():
    assert _PROJECT_ROOT.name == 'tendoriq'
    assert (_PROJECT_ROOT / 'api').is_dir()
    assert (_PROJECT_ROOT / 'web').is_dir()


def test_default_sqlite_under_tendoriq_data():
    db = default_sqlite_path()
    assert 'tendoriq' in db.parts
    assert db.parent.name == 'data'

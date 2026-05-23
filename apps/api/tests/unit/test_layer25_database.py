"""Layer 25 — Database & migrations."""

from pathlib import Path


def test_init_db_does_not_create_all():
    path = Path(__file__).resolve().parents[2] / 'src' / 'core' / 'database.py'
    text = path.read_text(encoding='utf-8')
    assert 'create_all' not in text
    assert 'SELECT 1' in text


def test_admin_store_migration_uses_metadata_create_all():
    path = (
        Path(__file__).resolve().parents[2]
        / 'alembic'
        / 'versions'
        / '20260522_admin_store.py'
    )
    text = path.read_text(encoding='utf-8')
    assert 'Base.metadata.create_all' in text
    assert "op.create_table(\n        'ai_providers'" not in text


def test_layer1_migration_is_idempotent():
    path = (
        Path(__file__).resolve().parents[2]
        / 'alembic'
        / 'versions'
        / '20260522_layer1_db_refinements.py'
    )
    text = path.read_text(encoding='utf-8')
    assert 'add_column_if_missing' in text
    assert 'create_index_if_missing' in text


def test_base_repository_soft_delete_helpers():
    repo = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'repositories'
    base = (repo / 'base.py').read_text(encoding='utf-8')
    soft = (repo / 'soft_delete.py').read_text(encoding='utf-8')
    assert 'apply_active_only' in base
    assert 'mark_soft_deleted' in base
    assert 'deleted_at.is_(None)' in soft


def test_database_migrations_doc_exists():
    path = Path(__file__).resolve().parents[4] / 'docs' / 'database-migrations.md'
    text = path.read_text(encoding='utf-8')
    assert 'alembic upgrade head' in text
    assert 'create_all' in text


def test_mysql_setup_documents_alembic():
    path = Path(__file__).resolve().parents[4] / 'docs' / 'MYSQL_SETUP.md'
    assert 'alembic upgrade head' in path.read_text(encoding='utf-8')
    assert 'create_all on API startup' not in path.read_text(encoding='utf-8')


def test_api_package_has_db_migrate_script():
    path = Path(__file__).resolve().parents[2] / 'package.json'
    assert '"db:migrate"' in path.read_text(encoding='utf-8')


def test_soft_delete_module_filters_deleted_at():
    path = Path(__file__).resolve().parents[2] / 'src' / 'api' / 'repositories' / 'soft_delete.py'
    text = path.read_text(encoding='utf-8')
    assert 'def apply_active_only' in text
    assert 'def mark_soft_deleted' in text

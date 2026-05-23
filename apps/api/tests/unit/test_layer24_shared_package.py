"""Layer 24 — Shared package (`@tendoriq/shared`)."""

from pathlib import Path


def test_tender_schema_uses_tenant_id():
    path = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'src' / 'types' / 'index.ts'
    text = path.read_text(encoding='utf-8')
    assert 'tenantId: z.string().uuid()' in text
    assert 'organizationId: z.string().uuid().optional()' in text


def test_shared_tenders_mapper_module():
    path = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'src' / 'tenders.ts'
    text = path.read_text(encoding='utf-8')
    assert 'mapTenderFromApi' in text
    assert 'tenantId' in text
    assert 'organizationId: tenantId' in text


def test_env_builds_mysql_database_url():
    path = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'src' / 'env.ts'
    text = path.read_text(encoding='utf-8')
    assert 'mysql+aiomysql' in text
    assert 'FRONTEND_URL' in text
    assert 'postgresql' not in text


def test_feature_flags_client_module():
    path = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'src' / 'feature-flags-client.ts'
    text = path.read_text(encoding='utf-8')
    assert 'isClientFeatureEnabled' in text
    assert 'NEXT_PUBLIC_FEATURE_SSO' in text


def test_api_route_prefix_constant():
    path = Path(__file__).resolve().parents[4] / 'packages' / 'shared' / 'src' / 'constants' / 'index.ts'
    assert "API_ROUTE_PREFIX = '/api/v1'" in path.read_text(encoding='utf-8')


def test_web_api_config_uses_shared_prefix():
    path = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'api-config.ts'
    text = path.read_text(encoding='utf-8')
    assert 'API_ROUTE_PREFIX' in text
    assert '@tendoriq/shared/constants' in text


def test_web_feature_flags_and_sidebar_gates():
    sidebar = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'components' / 'design-system' / 'app-sidebar.tsx'
    assert 'isAppFeatureEnabled' in sidebar.read_text(encoding='utf-8')
    flags = Path(__file__).resolve().parents[3] / 'web' / 'src' / 'lib' / 'feature-flags.ts'
    assert 'feature-flags-client' in flags.read_text(encoding='utf-8')

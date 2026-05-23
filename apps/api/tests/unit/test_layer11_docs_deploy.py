"""Layer L11 — documentation & deploy artifacts."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]


def test_local_setup_mysql_no_redis_required():
    text = (REPO / 'docs' / 'local-setup.md').read_text(encoding='utf-8')
    assert 'MySQL' in text
    assert 'No PostgreSQL, Redis' in text or 'no Redis' in text.lower()


def test_deployment_mysql_run_bat():
    text = (REPO / 'docs' / 'deployment.md').read_text(encoding='utf-8')
    assert 'mysql+aiomysql' in text
    assert 'run.bat' in text
    assert 'postgresql://' not in text.split('Prerequisites')[0]
    assert 'ARQ are not required' in text or 'not required' in text


def test_docker_compose_mysql_without_redis_dependency():
    text = (REPO / 'docker-compose.yml').read_text(encoding='utf-8')
    assert 'mysql:8' in text
    assert 'profiles:' in text and 'with-redis' in text
    block = text.split('api:', 1)[1].split('mysql:', 1)[0]
    assert 'redis:' not in block or 'depends_on' not in block.split('redis')[0]


def test_troubleshooting_mysql_not_postgres_primary():
    text = (REPO / 'docs' / 'troubleshooting.md').read_text(encoding='utf-8')
    assert 'run.bat check' in text
    assert 'mysql+aiomysql' in text
    db = text.split('### Database Issues', 1)[1].split('### Queue', 1)[0]
    assert 'postgresql://' not in db


def test_scaling_strategy_documents_current_mysql():
    text = (REPO / 'docs' / 'scaling-strategy.md').read_text(encoding='utf-8')
    assert 'MySQL' in text.split('Current Architecture')[1].split('---', 1)[0]


def test_enterprise_readiness_inline_queue_note():
    text = (REPO / 'docs' / 'enterprise-readiness.md').read_text(encoding='utf-8')
    assert 'inline' in text.lower() or 'MySQL' in text[:500]


def test_environment_config_mysql_first_banner():
    text = (REPO / 'docs' / 'environment-config.md').read_text(encoding='utf-8')
    assert 'MYSQL_SETUP' in text[:800]
    assert 'optional' in text.lower()


def test_missing_dependency_checks_mysql():
    text = (REPO / 'docs' / 'missing-dependency-checks.md').read_text(encoding='utf-8')
    assert 'MySQL 8+' in text
    assert 'PostgreSQL 15+' not in text


def test_database_performance_mysql_primary():
    text = (REPO / 'docs' / 'database-performance.md').read_text(encoding='utf-8')
    assert 'MySQL 8' in text
    assert 'legacy reference' in text.lower() or 'not used' in text.lower()


def test_readme_points_mysql_before_env_config():
    text = (REPO / 'README.md').read_text(encoding='utf-8')
    mysql_pos = text.index('MYSQL_SETUP.md')
    env_pos = text.index('environment-config.md')
    assert mysql_pos < env_pos

#!/usr/bin/env python3
"""Production readiness validation (MySQL stack)."""

import os
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg):
    print(f'{Colors.GREEN}✓{Colors.RESET} {msg}')


def print_error(msg):
    print(f'{Colors.RED}✗{Colors.RESET} {msg}')


def print_warning(msg):
    print(f'{Colors.YELLOW}⚠{Colors.RESET} {msg}')


def print_info(msg):
    print(f'{Colors.BLUE}ℹ{Colors.RESET} {msg}')


def validate_required_env():
    print('\n' + '=' * 50)
    print('Environment Variable Validation')
    print('=' * 50)

    required = [
        'DATABASE_URL',
        'JWT_SECRET',
    ]

    optional = [
        'CLERK_SECRET_KEY',
        'SENTRY_DSN',
        'OPENAI_API_KEY',
    ]

    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print_error(f'Missing required: {", ".join(missing)}')
        return False

    db_url = os.getenv('DATABASE_URL', '')
    if not db_url.startswith(('mysql', 'mariadb')):
        print_error('DATABASE_URL must be MySQL (mysql+aiomysql://...)')
        return False

    print_success(f'All {len(required)} required vars present')
    found_optional = [v for v in optional if os.getenv(v)]
    print_info(f'Optional vars: {len(found_optional)}/{len(optional)}')
    return True


def validate_dependencies():
    print('\n' + '=' * 50)
    print('Dependency Validation')
    print('=' * 50)

    try:
        import fastapi

        print_success(f'FastAPI {fastapi.__version__}')
    except ImportError:
        print_error('FastAPI not installed')
        return False

    try:
        import sqlalchemy

        print_success(f'SQLAlchemy {sqlalchemy.__version__}')
    except ImportError:
        print_error('SQLAlchemy not installed')
        return False

    try:
        import aiomysql  # noqa: F401

        print_success('aiomysql installed')
    except ImportError:
        print_error('aiomysql not installed')
        return False

    return True


def main():
    ok = validate_required_env() and validate_dependencies()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

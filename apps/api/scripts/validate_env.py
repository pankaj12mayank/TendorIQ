#!/usr/bin/env python3
"""Production Readiness Validation Script"""

import os
import sys
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

def validate_required_env():
    """Validate required environment variables"""
    print("\n" + "="*50)
    print("Environment Variable Validation")
    print("="*50)
    
    required = [
        'DATABASE_URL',
        'REDIS_URL',
        'CLERK_PUBLISHABLE_KEY',
        'CLERK_SECRET_KEY',
    ]
    
    optional = [
        'SENTRY_DSN',
        'STRIPE_SECRET_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
    ]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print_error(f"Missing required: {', '.join(missing)}")
        return False
    
    print_success(f"All {len(required)} required vars present")
    
    found_optional = [v for v in optional if os.getenv(v)]
    print_info(f"Optional vars: {len(found_optional)}/{len(optional)}")
    
    return True

def validate_dependencies():
    """Validate dependencies are installed"""
    print("\n" + "="*50)
    print("Dependency Validation")
    print("="*50)
    
    try:
        import fastapi
        print_success(f"FastAPI {fastapi.__version__}")
    except ImportError:
        print_error("FastAPI not installed")
        return False
    
    try:
        import sqlalchemy
        print_success(f"SQLAlchemy {sqlalchemy.__version__}")
    except ImportError:
        print_error("SQLAlchemy not installed")
        return False
    
    try:
        import redis
        print_success(f"Redis {redis.__version__}")
    except ImportError:
        print_error("Redis not installed")
        return False
    
    return True

def validate_security():
    """Validate security configuration"""
    print("\n" + "="*50)
    print("Security Validation")
    print("="*50)
    
    checks = []
    
    # Check secret key
    secret = os.getenv('SECRET_KEY', '')
    if len(secret) < 32:
        print_error("SECRET_KEY too short (min 32 chars)")
        checks.append(False)
    else:
        print_success("SECRET_KEY configured")
        checks.append(True)
    
    # Check CORS
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if not cors_origins:
        print_warning("CORS_ORIGINS not set (defaults to all)")
        checks.append(True)
    else:
        print_success("CORS_ORIGINS configured")
        checks.append(True)
    
    # Check rate limiting
    rate_limit = os.getenv('RATE_LIMIT_PER_MINUTE', '100')
    print_info(f"Rate limit: {rate_limit}/min")
    checks.append(True)
    
    return all(checks)

def validate_monitoring():
    """Validate monitoring and health checks"""
    print("\n" + "="*50)
    print("Monitoring Validation")
    print("="*50)
    
    # Check health endpoints exist
    from pathlib import Path
    api_path = Path(__file__).parent.parent / 'api'
    
    health_files = list(api_path.glob('**/health.py'))
    if health_files:
        print_success(f"Health endpoints: {len(health_files)} files")
    else:
        print_warning("No health endpoint files found")
    
    # Check sentry
    sentry_dsn = os.getenv('SENTRY_DSN', '')
    if sentry_dsn:
        print_success("Sentry configured")
    else:
        print_warning("Sentry not configured")
    
    return True

def main():
    print(Colors.BLUE + "\n" + "="*50)
    print("Production Readiness Validation")
    print("="*50 + Colors.RESET)
    
    results = {
        'env': validate_required_env(),
        'deps': validate_dependencies(),
        'security': validate_security(),
        'monitoring': validate_monitoring(),
    }
    
    print("\n" + "="*50)
    print("Summary")
    print("="*50)
    
    for name, passed in results.items():
        status = Colors.GREEN + "PASS" + Colors.RESET if passed else Colors.RED + "FAIL" + Colors.RESET
        print(f"{name.upper()}: {status}")
    
    if all(results.values()):
        print_success("\n✓ All validations passed!")
        sys.exit(0)
    else:
        print_error("\n✗ Some validations failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
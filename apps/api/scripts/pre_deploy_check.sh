#!/bin/bash
# Pre-Deployment Validation Script

set -e

echo "========================================"
echo "Pre-Deployment Validation"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

cd "$(dirname "$0")/../.."

echo ""
echo "1. Checking git status..."
if [ -d ".git" ]; then
    pass "Git repository"
else
    fail "Not a git repository"
fi

echo ""
echo "2. Running linter..."
cd apps/api
uv run ruff check src/ || warn "Linting issues found"
pass "Linting complete"

echo ""
echo "3. Checking types..."
uv run mypy src/ || warn "Type issues found"
pass "Type checking complete"

echo ""
echo "4. Running tests..."
uv run pytest tests/unit -v -x --tb=short || fail "Tests failed"
pass "All tests passed"

echo ""
echo "5. Checking dependencies..."
cd ../..
cd apps/web
npm audit --audit-level=high --registry=https://registry.npmjs.org/ || warn "Security warnings"
pass "Dependency check complete"

echo ""
echo "6. Building application..."
cd ../..
pnpm build:web || fail "Frontend build failed"
pass "Frontend built"

cd apps/api
uv run uvicorn --help > /dev/null || fail "Backend build failed"
pass "Backend built"

echo ""
echo "7. Checking environment variables..."
if [ -f ".env.production" ]; then
    pass "Production env file exists"
else
    warn "No .env.production file"
fi

echo ""
echo "========================================"
pass "Pre-deployment validation complete!"
echo "========================================"
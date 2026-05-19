# TenderIQ Local Development Setup
# Run this script to set up your local development environment

Write-Host "Setting up TenderIQ Development Environment..." -ForegroundColor Cyan

# Check prerequisites
$ErrorActionPreference = "Stop"

Write-Host "`n[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Node.js
try {
    $nodeVersion = node --version
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Node.js not found. Please install Node.js 20+." -ForegroundColor Red
    exit 1
}

# pnpm
try {
    $pnpmVersion = pnpm --version
    Write-Host "  pnpm: $pnpmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: pnpm not found. Installing..." -ForegroundColor Yellow
    npm install -g pnpm
}

# Python
try {
    $pythonVersion = python --version
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.12+." -ForegroundColor Red
    exit 1
}

# uv (Python package manager)
try {
    $uvVersion = uv --version
    Write-Host "  uv: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "  Installing uv..." -ForegroundColor Yellow
    pip install uv
}

Write-Host "`n[2/6] Installing Node.js dependencies..." -ForegroundColor Yellow
pnpm install

Write-Host "`n[3/6] Setting up Python environment..." -ForegroundColor Yellow
cd apps/api
uv sync
cd ../..

Write-Host "`n[4/6] Creating environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env file" -ForegroundColor Green
    Write-Host "  IMPORTANT: Update .env with your credentials!" -ForegroundColor Yellow
} else {
    Write-Host "  .env already exists" -ForegroundColor Gray
}

Write-Host "`n[5/6] Setting up pre-commit hooks..." -ForegroundColor Yellow
try {
    uv run pre-commit install
    Write-Host "  Pre-commit hooks installed" -ForegroundColor Green
} catch {
    Write-Host "  Skipped pre-commit setup" -ForegroundColor Gray
}

Write-Host "`n[6/6] Starting services..." -ForegroundColor Yellow
Write-Host "  Make sure MySQL is running (see docs/MYSQL_SETUP.md)" -ForegroundColor Yellow

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "`nTo start development:" -ForegroundColor Cyan
Write-Host "  pnpm dev          - Start all apps"
Write-Host "  pnpm dev:web      - Start frontend only"
Write-Host "  pnpm dev:api      - Start backend only"
Write-Host "`nFor more commands, see package.json scripts" -ForegroundColor Cyan
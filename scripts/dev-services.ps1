# TenderIQ Dev Services
# Start/stop required development services (PostgreSQL, Redis)

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

switch ($Action) {
    "start" {
        Write-Host "Starting development services..." -ForegroundColor Cyan

        # Start PostgreSQL (using Docker)
        try {
            docker start tendoriq-postgres 2>$null
            Write-Host "PostgreSQL: Running" -ForegroundColor Green
        } catch {
            docker run -d --name tendoriq-postgres `
                -e POSTGRES_PASSWORD=postgres `
                -e POSTGRES_DB=tendoriq `
                -p 5432:5432 postgres:16
            Write-Host "PostgreSQL: Started" -ForegroundColor Green
        }

        # Start Redis
        try {
            docker start tendoriq-redis 2>$null
            Write-Host "Redis: Running" -ForegroundColor Green
        } catch {
            docker run -d --name tendoriq-redis `
                -p 6379:6379 redis:7-alpine
            Write-Host "Redis: Started" -ForegroundColor Green
        }

        Write-Host "`nAll services running!" -ForegroundColor Green
    }

    "stop" {
        Write-Host "Stopping development services..." -ForegroundColor Cyan

        docker stop tendoriq-postgres 2>$null
        docker stop tendoriq-redis 2>$null

        Write-Host "All services stopped." -ForegroundColor Yellow
    }

    "status" {
        Write-Host "Service Status:" -ForegroundColor Cyan

        $pg = docker ps --filter "name=tendoriq-postgres" --format "{{.Names}}"
        if ($pg) {
            Write-Host "PostgreSQL: Running" -ForegroundColor Green
        } else {
            Write-Host "PostgreSQL: Stopped" -ForegroundColor Red
        }

        $redis = docker ps --filter "name=tendoriq-redis" --format "{{.Names}}"
        if ($redis) {
            Write-Host "Redis: Running" -ForegroundColor Green
        } else {
            Write-Host "Redis: Stopped" -ForegroundColor Red
        }
    }
}
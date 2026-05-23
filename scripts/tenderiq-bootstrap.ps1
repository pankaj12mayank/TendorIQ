# Shared bootstrap helpers for tenderiq-start.ps1 and tenderiq-check.ps1

. (Join-Path $PSScriptRoot 'install-python-deps.ps1')

function Get-TenderIqDatabaseUrlFromEnv {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) { return $null }
    foreach ($line in Get-Content $EnvPath) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        if ($t -match '^DATABASE_URL=(.+)$') {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Test-TenderIqDatabaseUrlConfigured {
    param([string]$EnvPath)
    $url = Get-TenderIqDatabaseUrlFromEnv -EnvPath $EnvPath
    if (-not $url) {
        throw "DATABASE_URL is missing in $EnvPath - copy .env.example to .env and set your MySQL password."
    }
    if ($url -match 'changeme|YOUR_MYSQL_PASSWORD') {
        Write-Host '[WARN] DATABASE_URL still uses a placeholder password - edit .env before login will work.' -ForegroundColor Yellow
    }
}

function Invoke-TenderIqApiScript {
    param(
        [string]$VenvPython,
        [string]$ApiDir,
        [string]$EnvPath,
        [string[]]$ScriptArgs
    )
    Push-Location $ApiDir
    $env:DOTENV_PATH = $EnvPath
    & $VenvPython (Join-Path $ApiDir 'scripts\ensure_mysql.py') @ScriptArgs
    $code = $LASTEXITCODE
    Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
    Pop-Location
    return $code
}

function Initialize-TenderIqMySql {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn = { param($l, $m) Write-Host "[$l] $m" }
    )
    $rootEnv = Join-Path $Root '.env'
    & $LogFn 'INFO' 'Checking MySQL (DATABASE_URL in .env)...'
    Test-TenderIqDatabaseUrlConfigured -EnvPath $rootEnv
    $code = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @()
    if ($code -ne 0) {
        throw @"
MySQL is not ready.
  1. Install MySQL 8+ and start the service
  2. Edit .env: set DATABASE_URL (replace YOUR_MYSQL_PASSWORD or changeme)
  3. See docs/MYSQL_SETUP.md
"@
    }
    & $LogFn 'INFO' 'MySQL OK'
}

function Invoke-TenderIqAlembicUpgrade {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn = { param($l, $m) Write-Host "[$l] $m" }
    )
    $rootEnv = Join-Path $Root '.env'
    & $LogFn 'INFO' 'Applying database migrations (alembic upgrade head)...'
    Push-Location $ApiDir
    $env:DOTENV_PATH = $rootEnv
    & $VenvPython -m alembic upgrade head
    $code = $LASTEXITCODE
    Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
    Pop-Location
    if ($code -ne 0) {
        throw 'alembic upgrade head failed - check DATABASE_URL and .tenderiq/startup.log'
    }
    & $LogFn 'INFO' 'Database schema up to date'
}

function Test-TenderIqApiReady {
    param([int]$Port = 8000)
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:$Port/health/ready" -TimeoutSec 3
        return ($r.status -eq 'ready' -and $r.checks.database -eq $true)
    } catch {
        return $false
    }
}

function Start-TenderIqDockerMySql {
    param([string]$Root)
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return $false
    }
    $compose = Join-Path $Root 'docker-compose.yml'
    if (-not (Test-Path $compose)) {
        return $false
    }
    Write-Host '[INFO] Starting MySQL via docker compose (mysql service)...' -ForegroundColor Yellow
    Push-Location $Root
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    docker compose up -d mysql 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    Pop-Location
    if ($code -ne 0) {
        Write-Host '[WARN] docker compose mysql failed (is Docker Desktop running?)' -ForegroundColor Yellow
        return $false
    }
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        $healthy = docker compose -f $compose ps mysql 2>$null | Select-String -Pattern 'healthy'
        if ($healthy) {
            Write-Host '[INFO] Docker MySQL is healthy on localhost:3306' -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 3
    }
    Write-Host '[WARN] Docker MySQL started but health check timed out' -ForegroundColor Yellow
    return $true
}

function Get-TenderIqDockerDatabaseUrl {
    return 'mysql+aiomysql://root:password@localhost:3306/tenderiq?charset=utf8mb4'
}

function Initialize-TenderIqDatabase {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn
    )
    Initialize-TenderIqMySql -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir -LogFn $LogFn
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir -LogFn $LogFn
}

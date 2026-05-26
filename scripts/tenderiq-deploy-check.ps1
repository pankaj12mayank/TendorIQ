# TenderIQ Lite — production deploy readiness (env + migrations + tests)
$ErrorActionPreference = 'Stop'

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root 'api'
$VenvPython = Join-Path $ApiDir 'venv\Scripts\python.exe'
$EnvFile = Join-Path $Root '.env'

. (Join-Path $PSScriptRoot 'tenderiq-bootstrap.ps1')

function Get-EnvValue([string]$name) {
    if (-not (Test-Path $EnvFile)) { return '' }
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match "^\s*$([regex]::Escape($name))\s*=\s*(.*)$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return ''
}

$fail = 0

Write-Host ''
Write-Host ' TenderIQ — Deploy readiness check' -ForegroundColor Cyan
Write-Host ' ===================================' -ForegroundColor Cyan
Write-Host ''

if (-not (Test-Path $EnvFile)) {
    Write-Host '[FAIL] Missing .env' -ForegroundColor Red
    exit 1
}

$nodeEnv = Get-EnvValue 'NODE_ENV'
$jwt = Get-EnvValue 'JWT_SECRET'
$cors = Get-EnvValue 'CORS_ORIGINS'
$apiUrl = Get-EnvValue 'NEXT_PUBLIC_API_URL'
$appUrl = Get-EnvValue 'NEXT_PUBLIC_APP_URL'
$expose = Get-EnvValue 'EXPOSE_ERROR_DETAILS'

if ($jwt.Length -lt 32) {
    Write-Host '[FAIL] JWT_SECRET must be at least 32 characters' -ForegroundColor Red
    $fail++
} else {
    Write-Host '[OK] JWT_SECRET length' -ForegroundColor Green
}

if ($nodeEnv -eq 'production') {
    if ($expose -eq 'true') {
        Write-Host '[WARN] EXPOSE_ERROR_DETAILS=true in production' -ForegroundColor Yellow
    }
    if (-not $cors -or $cors -eq '*') {
        Write-Host '[FAIL] Set CORS_ORIGINS to your web origin (not *)' -ForegroundColor Red
        $fail++
    } else {
        Write-Host '[OK] CORS_ORIGINS set' -ForegroundColor Green
    }
    if (-not $apiUrl -or $apiUrl -match 'localhost') {
        Write-Host '[WARN] NEXT_PUBLIC_API_URL should be your public API URL' -ForegroundColor Yellow
    }
    if (-not $appUrl -or $appUrl -match 'localhost') {
        Write-Host '[WARN] NEXT_PUBLIC_APP_URL should be your public app URL' -ForegroundColor Yellow
    }
}

Write-Host '[INFO] Platform admin is a database user (preferences.platform_super_admin), not .env' -ForegroundColor DarkGray

if (-not (Test-Path $VenvPython)) {
    Write-Host '[FAIL] API venv missing — run: run.bat setup' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '[1/3] Alembic head...' -ForegroundColor Cyan
try {
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir
    Write-Host '      migrations OK' -ForegroundColor Green
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
    exit 1
}

Write-Host '[2/3] Full unit tests...' -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit -q --tb=no
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host '[FAIL] Unit tests failed' -ForegroundColor Red
    exit 1
}
Pop-Location
Write-Host '      tests OK' -ForegroundColor Green

Write-Host '[3/3] Docker files...' -ForegroundColor Cyan
$dockerApi = Join-Path $ApiDir 'Dockerfile'
$dockerWeb = Join-Path $Root 'web\Dockerfile'
$compose = Join-Path $Root 'docker-compose.yml'
foreach ($f in @($dockerApi, $dockerWeb, $compose)) {
    if (Test-Path $f) {
        Write-Host "      OK $(Split-Path $f -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "      MISSING $f" -ForegroundColor Red
        $fail++
    }
}

Write-Host ''
if ($fail -gt 0) {
    Write-Host "Deploy check finished with $fail issue(s). Fix before go-live." -ForegroundColor Red
    exit 1
}
Write-Host 'Deploy readiness: PASS. See docs/DEPLOY.md for hosting steps.' -ForegroundColor Green
exit 0

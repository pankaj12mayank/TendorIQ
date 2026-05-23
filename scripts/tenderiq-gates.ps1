# Client-ready gates G0-G5 (see docs/AUDIT_STATUS.md)
$ErrorActionPreference = 'Stop'

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root 'apps\api'
$WebDir = Join-Path $Root 'apps\web'
$VenvPython = Join-Path $ApiDir 'venv\Scripts\python.exe'
$rootEnv = Join-Path $Root '.env'
$results = @{}
$gateDatabaseUrl = $null

. (Join-Path $PSScriptRoot 'tenderiq-bootstrap.ps1')

function Set-GateResult {
    param([string]$Id, [bool]$Ok, [string]$Detail)
    $results[$Id] = @{ ok = $Ok; detail = $Detail }
    $color = if ($Ok) { 'Green' } else { 'Red' }
    $mark = if ($Ok) { 'PASS' } else { 'FAIL' }
    Write-Host "[$mark] $Id - $Detail" -ForegroundColor $color
}

if (-not (Test-Path $rootEnv)) {
    Write-Host '[FAIL] Missing .env - copy from .env.example' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Host '[FAIL] Missing apps\api\venv - run: run.bat setup' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '=== G0 MySQL + DB ===' -ForegroundColor Cyan
try {
    Test-TenderIqDatabaseUrlConfigured -EnvPath $rootEnv
    $mysqlCode = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @()
    if ($mysqlCode -ne 0) {
        $dbUrl = Get-TenderIqDatabaseUrlFromEnv -EnvPath $rootEnv
        if ($dbUrl -match '@localhost:3306' -and (Start-TenderIqDockerMySql -Root $Root)) {
            if ($dbUrl -match 'changeme|YOUR_MYSQL_PASSWORD') {
                $gateDatabaseUrl = Get-TenderIqDockerDatabaseUrl
                $env:DATABASE_URL = $gateDatabaseUrl
                Write-Host '[INFO] Using Docker MySQL credentials (root:password) for gates' -ForegroundColor Yellow
            }
            $mysqlCode = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @()
        }
    }
    if ($mysqlCode -ne 0) {
        throw 'MySQL not reachable. Start MySQL 8+ or Docker Desktop, then set DATABASE_URL in .env (see docs/MYSQL_SETUP.md).'
    }
    Set-GateResult 'G0' $true 'MySQL reachable; database ensured'
} catch {
    Set-GateResult 'G0' $false $_.Exception.Message
}

Write-Host ''
Write-Host '=== G1 run.bat check ===' -ForegroundColor Cyan
if ($gateDatabaseUrl) { $env:DATABASE_URL = $gateDatabaseUrl }
$checkScript = Join-Path $PSScriptRoot 'tenderiq-check.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript
if ($LASTEXITCODE -eq 0) {
    Set-GateResult 'G1' $true 'tenderiq-check.ps1 (L0-L13 + MySQL + alembic)'
} else {
    Set-GateResult 'G1' $false "tenderiq-check.ps1 exit $LASTEXITCODE"
}

Write-Host ''
Write-Host '=== G2 alembic upgrade head ===' -ForegroundColor Cyan
try {
    if ($gateDatabaseUrl) { $env:DATABASE_URL = $gateDatabaseUrl }
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir
    Set-GateResult 'G2' $true 'alembic upgrade head'
} catch {
    Set-GateResult 'G2' $false $_.Exception.Message
}

Write-Host ''
Write-Host '=== G3 run.bat stack ===' -ForegroundColor Cyan
$apiPort = 8000
$apiReady = Test-TenderIqApiReady -Port $apiPort
$webOk = $false
try {
    $wr = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 5
    $webOk = $wr.StatusCode -lt 500
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -lt 500) { $webOk = $true }
}

if (-not $apiReady -or -not $webOk) {
    Write-Host '[INFO] Stack not fully up - starting via tenderiq-start.ps1...' -ForegroundColor Yellow
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'tenderiq-start.ps1')
    if ($LASTEXITCODE -ne 0) {
        Set-GateResult 'G3' $false 'tenderiq-start.ps1 failed - see .tendoriq\startup.log'
    } else {
        Start-Sleep -Seconds 8
        $apiReady = Test-TenderIqApiReady -Port $apiPort
        $webOk = $false
        try {
            $wr = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 10
            $webOk = $wr.StatusCode -lt 500
        } catch {
            if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -lt 500) { $webOk = $true }
        }
        if ($apiReady -and $webOk) {
            Set-GateResult 'G3' $true "API :$apiPort ready + web :3000"
        } else {
            Set-GateResult 'G3' $false "API ready=$apiReady web=$webOk - check .tendoriq logs"
        }
    }
} else {
    Set-GateResult 'G3' $true 'API and web already running'
}

Write-Host ''
Write-Host '=== G4 manual smoke (API) ===' -ForegroundColor Cyan
if (-not $apiReady) {
    $apiReady = Test-TenderIqApiReady -Port $apiPort
}
if ($apiReady) {
    Push-Location $ApiDir
    $env:DOTENV_PATH = $rootEnv
    & $VenvPython scripts\smoke_gate.py
    $smokeCode = $LASTEXITCODE
    Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
    Pop-Location
    if ($smokeCode -eq 0) {
        Set-GateResult 'G4' $true 'smoke_gate.py (login, tenders, billing, admin, health)'
    } else {
        Set-GateResult 'G4' $false 'smoke_gate.py failed'
    }
} else {
    Set-GateResult 'G4' $false 'API not ready for smoke'
}

Write-Host ''
Write-Host '=== G5 Playwright auth E2E ===' -ForegroundColor Cyan
if ($webOk -and $apiReady) {
    Push-Location $WebDir
    pnpm exec playwright install chromium 2>$null | Out-Null
    if (-not $env:NEXT_PUBLIC_API_URL) { $env:E2E_API_URL = "http://127.0.0.1:$apiPort" }
    else { $env:E2E_API_URL = $env:NEXT_PUBLIC_API_URL }
    $env:BASE_URL = 'http://localhost:3000'
    if ($env:DEMO_USER_EMAIL) { $env:E2E_DEMO_EMAIL = $env:DEMO_USER_EMAIL }
    if ($env:DEMO_USER_PASSWORD) { $env:E2E_DEMO_PASSWORD = $env:DEMO_USER_PASSWORD }
    if ($env:SUPER_ADMIN_EMAIL) { $env:E2E_ADMIN_EMAIL = $env:SUPER_ADMIN_EMAIL }
    if ($env:SUPER_ADMIN_PASSWORD) { $env:E2E_ADMIN_PASSWORD = $env:SUPER_ADMIN_PASSWORD }
    pnpm exec playwright test --project=chromium --project=chromium-authenticated
    $e2eCode = $LASTEXITCODE
    Pop-Location
    if ($e2eCode -eq 0) {
        Set-GateResult 'G5' $true 'Playwright public + authenticated projects'
    } else {
        Set-GateResult 'G5' $false "playwright exit $e2eCode"
    }
} else {
    Set-GateResult 'G5' $false 'Need API + web for Playwright'
}

Write-Host ''
Write-Host '=== Gate summary ===' -ForegroundColor Cyan
$allOk = $true
foreach ($k in @('G0', 'G1', 'G2', 'G3', 'G4', 'G5')) {
    if (-not $results.ContainsKey($k) -or -not $results[$k].ok) { $allOk = $false }
}
if ($allOk) {
    Write-Host 'All gates G0-G5 PASSED.' -ForegroundColor Green
    exit 0
}
Write-Host 'One or more gates FAILED.' -ForegroundColor Red
exit 1

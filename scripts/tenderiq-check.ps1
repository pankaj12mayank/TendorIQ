# Quick reliability check (L0 + L1: deps, compile, import, MySQL, migrations)
$ErrorActionPreference = "Stop"

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root "apps\api"
$VenvPython = Join-Path $ApiDir "venv\Scripts\python.exe"
$VenvPip = Join-Path $ApiDir "venv\Scripts\pip.exe"
$rootEnv = Join-Path $Root ".env"

. (Join-Path $PSScriptRoot "tenderiq-bootstrap.ps1")

if (-not (Test-Path $rootEnv)) {
    Write-Host "[FAIL] Missing $rootEnv - copy from .env.example and set DATABASE_URL" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[FAIL] Missing venv at apps\api\venv - run: run.bat setup" -ForegroundColor Red
    exit 1
}

$devToolsOk = Test-TenderIqPythonDevTools -VenvPython $VenvPython
if (-not $devToolsOk) {
    Write-Host "[INFO] Installing dev Python tools (requirements-dev.txt)..." -ForegroundColor Yellow
    Install-TenderIqPythonDeps -ApiDir $ApiDir -VenvPython $VenvPython -VenvPip $VenvPip -Force
    $devToolsOk = Test-TenderIqPythonDevTools -VenvPython $VenvPython
    if (-not $devToolsOk) {
        Write-Host "[FAIL] pytest/ruff/mypy missing - run: run.bat setup" -ForegroundColor Red
        exit 1
    }
}

Test-TenderIqDatabaseUrlConfigured -EnvPath $rootEnv

Write-Host "[1/11] L6 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer6_tenant_dashboard.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[2/11] L5 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer5_onboarding.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[3/11] L4 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer4_auth.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[4/11] L3 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer3_api_routing.py tests/unit/test_openapi_contract.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[5/11] L2 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer2_database.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[6/11] L1 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer1_dependencies.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "[7/11] compileall..." -ForegroundColor Cyan
& $VenvPython -m compileall -q src
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "[8/11] verify_import..." -ForegroundColor Cyan
$env:DOTENV_PATH = $rootEnv
& $VenvPython scripts/verify_import.py
$code = $LASTEXITCODE
Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
if ($code -ne 0) { Pop-Location; exit 1 }

Write-Host "[9/11] MySQL reachability..." -ForegroundColor Cyan
$mysqlCode = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @('--check-only')
Pop-Location
if ($mysqlCode -ne 0) {
    Write-Host '[FAIL] MySQL not reachable - start MySQL and fix DATABASE_URL in .env' -ForegroundColor Red
    exit 1
}

Write-Host "[10/11] alembic upgrade head..." -ForegroundColor Cyan
try {
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
    exit 1
}

Write-Host "[11/11] optional API readiness (if already running)..." -ForegroundColor Cyan
try {
    if (Test-TenderIqApiReady -Port 8000) {
        Write-Host '      API ready on :8000 (database OK)' -ForegroundColor Green
    } else {
        $h = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2
        if ($h.status -eq 'healthy') {
            Write-Host '      API up but /health/ready not OK (check MySQL)' -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host '      API not running (OK for check-only)' -ForegroundColor DarkGray
}

Write-Host ""
Write-Host 'All L0-L6 checks passed (tenant dashboard, onboarding, auth, routing, deps, schema, compile, import, MySQL, migrations).' -ForegroundColor Green
exit 0

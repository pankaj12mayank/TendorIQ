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

Write-Host "[1/19] L12 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer12_client_ready.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[2/19] All layer regression tests (L0-L13)..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer0_bootstrap.py tests/unit/test_layer1_dependencies.py tests/unit/test_layer2_database.py tests/unit/test_layer3_api_routing.py tests/unit/test_layer4_auth.py tests/unit/test_layer5_onboarding.py tests/unit/test_layer6_tenant_dashboard.py tests/unit/test_layer7_documents_ocr.py tests/unit/test_layer8_billing.py tests/unit/test_layer9_notifications_email.py tests/unit/test_layer10_super_admin.py tests/unit/test_layer11_docs_deploy.py tests/unit/test_layer12_client_ready.py tests/unit/test_layer13_ui_api_disconnect.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[3/19] L11 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer11_docs_deploy.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[4/19] L10 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer10_super_admin.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[5/19] L9 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer9_notifications_email.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[6/19] L8 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer8_billing.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[7/19] L7 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer7_documents_ocr.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[8/19] L13 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer13_ui_api_disconnect.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[9/19] L6 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer6_tenant_dashboard.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[10/19] L5 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer5_onboarding.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[11/19] L4 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer4_auth.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[12/19] L3 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer3_api_routing.py tests/unit/test_openapi_contract.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[13/19] L2 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer2_database.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[14/19] L1 contract tests..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit/test_layer1_dependencies.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "[15/19] Web Vitest (auth 401)..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "apps\web")
pnpm exec vitest run src/lib/__tests__/auth-unauthorized.test.ts
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host "[16/19] compileall..." -ForegroundColor Cyan
& $VenvPython -m compileall -q src
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "[17/19] verify_import..." -ForegroundColor Cyan
$env:DOTENV_PATH = $rootEnv
& $VenvPython scripts/verify_import.py
$code = $LASTEXITCODE
Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
if ($code -ne 0) { Pop-Location; exit 1 }

Write-Host "[18/19] MySQL reachability..." -ForegroundColor Cyan
$mysqlCode = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @('--check-only')
Pop-Location
if ($mysqlCode -ne 0) {
    Write-Host '[FAIL] MySQL not reachable - start MySQL and fix DATABASE_URL in .env' -ForegroundColor Red
    exit 1
}

Write-Host "[19/19] alembic upgrade head..." -ForegroundColor Cyan
try {
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
    exit 1
}

Write-Host "[optional] API readiness (if already running)..." -ForegroundColor Cyan
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
Write-Host 'All L0-L13 checks passed. For client sign-off run stack (run.bat) then: run.bat e2e - see docs/CLIENT_READY.md' -ForegroundColor Green
exit 0

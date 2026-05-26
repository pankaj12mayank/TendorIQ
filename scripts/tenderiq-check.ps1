# TenderIQ Lite â€” quick reliability check (deps, import, migrations, core tests)
$ErrorActionPreference = 'Stop'

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root 'api'
$VenvPython = Join-Path $ApiDir 'venv\Scripts\python.exe'
$VenvPip = Join-Path $ApiDir 'venv\Scripts\pip.exe'
$rootEnv = Join-Path $Root '.env'

. (Join-Path $PSScriptRoot 'tenderiq-bootstrap.ps1')

if (-not (Test-Path $rootEnv)) {
    Write-Host '[FAIL] Missing .env â€” copy from .env.example' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Host '[FAIL] Missing venv at api\venv â€” run: run.bat setup' -ForegroundColor Red
    exit 1
}

Write-Host '[1/5] Python import check...' -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -c 'from src.main import app; print(len(app.routes), "routes")'
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host '[2/5] Core unit tests...' -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m pytest tests/unit -q --tb=no
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

Write-Host '[3/5] Web typecheck...' -ForegroundColor Cyan
Push-Location (Join-Path $Root 'web')
pnpm exec tsc --noEmit 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[WARN] Web typecheck reported issues (non-blocking for Lite dev)' -ForegroundColor Yellow
}
Pop-Location

Write-Host '[4/5] alembic upgrade head...' -ForegroundColor Cyan
try {
    Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir
} catch {
    Write-Host "[FAIL] $_" -ForegroundColor Red
    exit 1
}

Write-Host '[5/5] API health (if running)...' -ForegroundColor Cyan
try {
    if (Test-TenderIqApiReady -Port 8000) {
        Write-Host '      API ready on :8000' -ForegroundColor Green
    }
} catch {
    Write-Host '      API not running (OK for check-only)' -ForegroundColor DarkGray
}

Write-Host ''
Write-Host 'TenderIQ Lite checks passed. Start stack: run.bat' -ForegroundColor Green
exit 0


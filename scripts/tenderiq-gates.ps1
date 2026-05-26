# TenderIQ Lite â€” smoke gates (DB, check, stack health)
$ErrorActionPreference = 'Stop'

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root 'api'
$VenvPython = Join-Path $ApiDir 'venv\Scripts\python.exe'
$rootEnv = Join-Path $Root '.env'

. (Join-Path $PSScriptRoot 'tenderiq-bootstrap.ps1')

if (-not (Test-Path $rootEnv)) {
    Write-Host '[FAIL] Missing .env' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Host '[FAIL] Missing venv â€” run: run.bat setup' -ForegroundColor Red
    exit 1
}

Write-Host '=== G1 run.bat check ===' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'tenderiq-check.ps1')
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host '=== G2 API /health ===' -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 5
    if ($h.status -ne 'healthy') { throw 'unhealthy' }
    Write-Host '[PASS] API health' -ForegroundColor Green
} catch {
    Write-Host '[FAIL] Start API first: run.bat' -ForegroundColor Red
    exit 1
}

Write-Host '=== G3 Web ===' -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -ge 400) { throw "HTTP $($r.StatusCode)" }
    Write-Host '[PASS] Web :3000' -ForegroundColor Green
} catch {
    Write-Host '[FAIL] Web not reachable on :3000' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host 'Lite gates passed.' -ForegroundColor Green
exit 0


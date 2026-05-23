# Quick reliability check (same gates as startup, without launching servers)
$ErrorActionPreference = "Stop"

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root "apps\api"
$VenvPython = Join-Path $ApiDir "venv\Scripts\python.exe"
$rootEnv = Join-Path $Root ".env"

if (-not (Test-Path $rootEnv)) {
    Write-Host "[FAIL] Missing $rootEnv — copy from .env.example" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[FAIL] Missing venv at apps\api\venv — run: run.bat setup" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] compileall..." -ForegroundColor Cyan
Push-Location $ApiDir
& $VenvPython -m compileall -q src
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

Write-Host "[2/3] verify_import..." -ForegroundColor Cyan
$env:DOTENV_PATH = $rootEnv
& $VenvPython scripts/verify_import.py
$code = $LASTEXITCODE
Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
Pop-Location
if ($code -ne 0) { exit 1 }

Write-Host "[3/3] optional health (if API already running)..." -ForegroundColor Cyan
try {
    $h = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($h.status -eq 'healthy') {
        Write-Host "      API already healthy on :8000" -ForegroundColor Green
    }
} catch {
    Write-Host "      API not running (OK for check-only)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "All import checks passed." -ForegroundColor Green
exit 0

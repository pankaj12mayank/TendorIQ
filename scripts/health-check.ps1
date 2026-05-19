# TenderIQ Health Check Script

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TenderIQ Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$healthStatus = @{
    "Backend API" = $false
    "Frontend"    = $false
    "MySQL"       = $false
}

Write-Host "=== Service Health ===" -ForegroundColor Yellow

try {
    Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5 | Out-Null
    Write-Host "[OK] Backend API - Healthy" -ForegroundColor Green
    $healthStatus["Backend API"] = $true
} catch {
    Write-Host "[FAIL] Backend API - Not responding" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -in 200, 304) {
        Write-Host "[OK] Frontend - Healthy" -ForegroundColor Green
        $healthStatus["Frontend"] = $true
    }
} catch {
    Write-Host "[FAIL] Frontend - Not responding" -ForegroundColor Red
}

try {
    $ready = Invoke-RestMethod "http://localhost:8000/health/ready" -TimeoutSec 5
    if ($ready.status -eq "ready") {
        Write-Host "[OK] MySQL (via API ready) - Connected" -ForegroundColor Green
        $healthStatus["MySQL"] = $true
    } else {
        Write-Host "[WARN] API up but database not ready" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Could not verify database readiness" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Yellow

$allHealthy = $true
foreach ($service in $healthStatus.Keys) {
    if (-not $healthStatus[$service]) {
        $allHealthy = $false
        Write-Host "  $service : DOWN" -ForegroundColor Red
    } else {
        Write-Host "  $service : UP" -ForegroundColor Green
    }
}

Write-Host ""
if ($allHealthy) {
    Write-Host "All services healthy." -ForegroundColor Green
} else {
    Write-Host "Some services need attention." -ForegroundColor Yellow
}

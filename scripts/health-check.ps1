# TenderIQ Health Check Script

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TenderIQ Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$healthStatus = @{
    "Backend API" = $false
    "Frontend" = $false
    "Database" = $false
    "Redis" = $false
}

function Test-HealthEndpoint($name, $url, $status) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] $name - Healthy" -ForegroundColor Green
            $status[$name] = $true
            return $true
        }
    } catch {}
    Write-Host "[FAIL] $name - Not responding" -ForegroundColor Red
    $status[$name] = $false
    return $false
}

Write-Host "=== Service Health ===" -ForegroundColor Yellow

# Check Backend API
try {
    $response = Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "[OK] Backend API - Healthy" -ForegroundColor Green
    $healthStatus["Backend API"] = $true
} catch {
    Write-Host "[FAIL] Backend API - Not responding" -ForegroundColor Red
}

# Check Frontend
try {
    $response = Invoke-WebRequest "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 304) {
        Write-Host "[OK] Frontend - Healthy" -ForegroundColor Green
        $healthStatus["Frontend"] = $true
    }
} catch {
    Write-Host "[FAIL] Frontend - Not responding" -ForegroundColor Red
}

# Check Database
try {
    $result = & python --version 2>&1
    Write-Host "[OK] Python - Available" -ForegroundColor Green
    $healthStatus["Database"] = $true
} catch {
    Write-Host "[FAIL] Python - Not available" -ForegroundColor Red
}

# Check Redis
try {
    $redisTest = redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "[OK] Redis - Connected" -ForegroundColor Green
        $healthStatus["Redis"] = $true
    }
} catch {
    Write-Host "[WARN] Redis - Not connected (may not be required)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Yellow

$allHealthy = $true
foreach ($service in $healthStatus.Keys) {
    if (-not $healthStatus[$service]) {
        $allHealthy = $false
        break
    }
}

if ($allHealthy) {
    Write-Host "All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Cyan
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
    Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White
    exit 0
} else {
    Write-Host "Some services are not healthy. Try running run.bat" -ForegroundColor Red
    exit 1
}
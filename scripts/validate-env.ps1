# TenderIQ Environment Validation Script

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TenderIQ Environment Validation" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

function Test-Command($name, $command) {
    Write-Host "Checking $name... " -NoNewline
    try {
        $result = Invoke-Expression $command 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK]" -ForegroundColor Green
            return $true
        }
    } catch {}
    Write-Host "[MISSING]" -ForegroundColor Red
    return $false
}

function Test-File($name, $path) {
    Write-Host "Checking $name... " -NoNewline
    if (Test-Path $path) {
        Write-Host "[OK]" -ForegroundColor Green
        return $true
    }
    Write-Host "[MISSING]" -ForegroundColor Red
    return $false
}

function Test-Port($name, $port) {
    Write-Host "Checking $name... " -NoNewline
    $connection = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "[OK - Running]" -ForegroundColor Green
        return $true
    }
    Write-Host "[NOT RUNNING]" -ForegroundColor Yellow
    return $false
}

Write-Host "=== System Requirements ===" -ForegroundColor Yellow
$allPassed = (Test-Command "Python" "python --version") -and $allPassed
$allPassed = (Test-Command "Node.js" "node --version") -and $allPassed
$allPassed = (Test-Command "npm" "npm --version") -and $allPassed
$allPassed = (Test-Command "Git" "git --version") -and $allPassed

Write-Host ""
Write-Host "=== File Structure ===" -ForegroundColor Yellow
$allPassed = (Test-File "Backend Dir" "$PSScriptRoot\..\api") -and $allPassed
$allPassed = (Test-File "Frontend Dir" "$PSScriptRoot\..\web") -and $allPassed
$allPassed = (Test-File "Env File" "$PSScriptRoot\..\.env") -and $allPassed
$allPassed = (Test-File "Requirements" "$PSScriptRoot\..\api\requirements.txt") -and $allPassed

Write-Host ""
Write-Host "=== Services (Optional) ===" -ForegroundColor Yellow
Test-Port "MySQL" 3306 | Out-Null

Write-Host ""
Write-Host "=== Running Services ===" -ForegroundColor Yellow
Test-Port "Backend API" 8000 | Out-Null
Test-Port "Frontend" 3000 | Out-Null

Write-Host ""
if ($allPassed) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  All required checks passed!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  Some required items are missing" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}

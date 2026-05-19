# TenderIQ - stop local services. Called by stop.bat
$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$PidFile = Join-Path $Root ".tenderiq\pids.json"

function Stop-Port($port) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

if (Test-Path $PidFile) {
    $p = Get-Content $PidFile -Raw | ConvertFrom-Json
    foreach ($id in @($p.api_pid, $p.web_pid)) {
        if ($id) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

Stop-Port 8000
Stop-Port 3000
Stop-Port 8765

Write-Host "[TenderIQ] Stopped." -ForegroundColor Green

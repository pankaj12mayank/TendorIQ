# Local MySQL helper for run.bat (Windows). No Docker.
# - Starts MySQL80 / MariaDB service if already installed
# - Optionally installs via winget (may prompt for Admin once)
# - Sets dev DATABASE_URL when .env still has placeholder password

$script:TenderIqDevMySqlPassword = if ($env:TENDERIQ_DEV_MYSQL_PASSWORD) {
    $env:TENDERIQ_DEV_MYSQL_PASSWORD
} else {
    'TenderIQ@Dev123'
}

function Test-TenderIqMySqlPort {
    try {
        $r = Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return [bool]$r.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Start-TenderIqMySqlServices {
    foreach ($name in @('MySQL80', 'MySQL', 'MariaDB')) {
        $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
        if (-not $svc) { continue }
        if ($svc.Status -eq 'Running') { return $name }
        try {
            Start-Service -Name $name -ErrorAction Stop
            Start-Sleep -Seconds 3
            if ((Get-Service -Name $name).Status -eq 'Running') { return $name }
        } catch {
            # needs elevation or manual start
        }
    }
    return $null
}

function Install-TenderIqMySqlWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }
    $packages = @(
        @{ Id = 'MariaDB.Server'; Name = 'MariaDB Server' },
        @{ Id = 'Oracle.MySQL'; Name = 'MySQL' }
    )
    foreach ($pkg in $packages) {
        Write-Host "[INFO] Installing $($pkg.Name) via winget (Admin approval may appear)..." -ForegroundColor Yellow
        $args = @(
            'install', '-e', '--id', $pkg.Id,
            '--accept-package-agreements', '--accept-source-agreements',
            '--disable-interactivity'
        )
        $p = Start-Process -FilePath 'winget' -ArgumentList $args -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -in 0, 3010) {
            Write-Host "[INFO] $($pkg.Name) installer finished (exit $($p.ExitCode))." -ForegroundColor Green
            return $true
        }
    }
    return $false
}

function Wait-TenderIqMySqlPort {
    param([int]$TimeoutSec = 120)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-TenderIqMySqlPort) { return $true }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Set-TenderIqEnvMySqlPassword {
    param(
        [string]$EnvPath,
        [string]$Password
    )
    if (-not (Test-Path $EnvPath)) { return }
    $keys = @{
        'MYSQL_PASSWORD' = $Password
        'MYSQL_HOST'       = 'localhost'
        'MYSQL_PORT'       = '3306'
        'MYSQL_USER'       = 'root'
        'MYSQL_DATABASE'   = 'tenderiq'
    }
    $lines = Get-Content $EnvPath
    $seen = @{}
    $out = foreach ($line in $lines) {
        $matched = $false
        foreach ($key in $keys.Keys) {
            if ($line -match "^\s*$([regex]::Escape($key))\s*=") {
                $seen[$key] = $true
                $matched = $true
                "$key=$($keys[$key])"
                break
            }
        }
        if (-not $matched) {
            if ($line -match '^\s*DATABASE_URL\s*=') { continue }
            $line
        }
    }
    foreach ($key in $keys.Keys) {
        if (-not $seen[$key]) { $out += "$key=$($keys[$key])" }
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($EnvPath, ($out -join "`n").TrimEnd() + "`n", $utf8)
}

function Initialize-TenderIqLocalMySql {
    param(
        [string]$Root,
        [scriptblock]$LogFn = { param($l, $m) Write-Host "[$l] $m" }
    )
    if ($env:TENDERIQ_SKIP_MYSQL_INSTALL -eq '1') {
        return (Test-TenderIqMySqlPort)
    }

    if (Test-TenderIqMySqlPort) {
        return $true
    }

    & $LogFn 'INFO' 'MySQL not listening on :3306 - starting local service if installed...'
    $started = Start-TenderIqMySqlServices
    if ($started) {
        & $LogFn 'INFO' "Started service: $started"
    }
    if (Wait-TenderIqMySqlPort -TimeoutSec 15) {
        return $true
    }

    if ($env:TENDERIQ_AUTO_MYSQL_INSTALL -eq '0') {
        return $false
    }

    & $LogFn 'INFO' 'MySQL not installed - attempting winget install (one-time, may need Admin)...'
    $null = Install-TenderIqMySqlWinget
    Start-TenderIqMySqlServices | Out-Null
    if (-not (Wait-TenderIqMySqlPort -TimeoutSec 120)) {
        return $false
    }

    $envPath = Join-Path $Root '.env'
    $content = if (Test-Path $envPath) { Get-Content $envPath -Raw } else { '' }
    if ($content -match 'changeme|YOUR_MYSQL_PASSWORD') {
        Set-TenderIqEnvMySqlPassword -EnvPath $envPath -Password $script:TenderIqDevMySqlPassword
        & $LogFn 'INFO' "Updated .env MYSQL_PASSWORD for dev ($script:TenderIqDevMySqlPassword)"
        & $LogFn 'WARN' 'During MySQL setup, set root password to the same value, or edit MYSQL_PASSWORD in .env.'
    }
    return $true
}


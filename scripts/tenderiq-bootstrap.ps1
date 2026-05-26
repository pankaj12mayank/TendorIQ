# Shared bootstrap helpers for tenderiq-start.ps1 and tenderiq-check.ps1

. (Join-Path $PSScriptRoot 'install-python-deps.ps1')
. (Join-Path $PSScriptRoot 'install-mysql-windows.ps1')

function Get-TenderIqDatabaseUrlFromEnv {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) { return $null }
    foreach ($line in Get-Content $EnvPath) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        if ($t -match '^DATABASE_URL=(.+)$') {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Get-TenderIqMySqlPasswordFromEnv {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) { return $null }
    foreach ($line in Get-Content $EnvPath) {
        $t = $line.Trim()
        if ($t -match '^MYSQL_PASSWORD=(.+)$') {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return $null
}

function Get-TenderIqDatabaseDriverFromEnv {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) { return 'sqlite' }
    foreach ($line in Get-Content $EnvPath) {
        $t = $line.Trim()
        if ($t -match '^DATABASE_DRIVER=(.+)$') {
            return $Matches[1].Trim().Trim('"').Trim("'").ToLowerInvariant()
        }
    }
    return 'sqlite'
}

function Test-TenderIqDatabaseUrlConfigured {
    param([string]$EnvPath)
    $driver = Get-TenderIqDatabaseDriverFromEnv -EnvPath $EnvPath
    if ($driver -eq 'sqlite') {
        Write-Host '[INFO] DATABASE_DRIVER=sqlite (no MySQL required)' -ForegroundColor Cyan
        return
    }
    $pwd = Get-TenderIqMySqlPasswordFromEnv -EnvPath $EnvPath
    $url = Get-TenderIqDatabaseUrlFromEnv -EnvPath $EnvPath
    if (-not $pwd -and -not $url) {
        throw "MYSQL_PASSWORD or DATABASE_URL missing in $EnvPath - copy .env.example to .env"
    }
    if ($pwd -match 'changeme|YOUR_MYSQL_PASSWORD' -or ($url -and $url -match 'changeme|YOUR_MYSQL_PASSWORD')) {
        Write-Host '[WARN] MySQL password still placeholder - set MYSQL_PASSWORD in .env' -ForegroundColor Yellow
    }
}

function Invoke-TenderIqApiScript {
    param(
        [string]$VenvPython,
        [string]$ApiDir,
        [string]$EnvPath,
        [string[]]$ScriptArgs
    )
    Push-Location $ApiDir
    $env:DOTENV_PATH = $EnvPath
    $output = & $VenvPython (Join-Path $ApiDir 'scripts\ensure_database.py') @ScriptArgs 2>&1
    $code = $LASTEXITCODE
    Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
    Pop-Location
    if ($output) {
        $text = ($output | Out-String).Trim()
        if ($code -ne 0) {
            Write-Host $text -ForegroundColor Red
        } else {
            Write-Host $text -ForegroundColor DarkGray
        }
    }
    return $code
}

function Initialize-TenderIqMySql {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn = { param($l, $m) Write-Host "[$l] $m" }
    )
    $rootEnv = Join-Path $Root '.env'
    $driver = Get-TenderIqDatabaseDriverFromEnv -EnvPath $rootEnv
    Test-TenderIqDatabaseUrlConfigured -EnvPath $rootEnv

    if ($driver -eq 'sqlite') {
        & $LogFn 'INFO' 'Setting up SQLite database (no MySQL)...'
        $code = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @()
        if ($code -ne 0) {
            throw @'
SQLite database setup failed.
  Run: run.bat setup
  Or: cd api; venv\Scripts\python.exe -m pip install -r requirements-dev.txt
  Common cause: missing aiosqlite (see error above).
'@
        }
        & $LogFn 'INFO' 'SQLite OK'
        return
    }

    & $LogFn 'INFO' 'Checking local MySQL (DATABASE_URL in .env)...'
    if (-not (Initialize-TenderIqLocalMySql -Root $Root -LogFn $LogFn)) {
        & $LogFn 'WARN' 'Auto MySQL setup did not complete - install manually if winget failed.'
    }
    $code = Invoke-TenderIqApiScript -VenvPython $VenvPython -ApiDir $ApiDir -EnvPath $rootEnv -ScriptArgs @()
    if ($code -ne 0) {
        throw @'
Local MySQL is not ready on localhost:3306.
  Tip: use DATABASE_DRIVER=sqlite in .env (no MySQL install) and run run.bat again.
  Or fix MYSQL_PASSWORD and start MySQL80 service. See docs/MYSQL_SETUP.md
'@
    }
    & $LogFn 'INFO' 'MySQL OK'
}

function Invoke-TenderIqAlembicUpgrade {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn = { param($l, $m) Write-Host "[$l] $m" }
    )
    $rootEnv = Join-Path $Root '.env'
    & $LogFn 'INFO' 'Applying database migrations (alembic upgrade head)...'
    Push-Location $ApiDir
    $env:DOTENV_PATH = $rootEnv
    & $VenvPython -m alembic upgrade head
    $code = $LASTEXITCODE
    Remove-Item Env:DOTENV_PATH -ErrorAction SilentlyContinue
    Pop-Location
    if ($code -ne 0) {
        throw 'alembic upgrade head failed - check DATABASE_URL and .tenderiq/startup.log'
    }
    & $LogFn 'INFO' 'Database schema up to date'
}

function Test-TenderIqApiReady {
    param([int]$Port = 8000)
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:$Port/health/ready" -TimeoutSec 3
        return ($r.status -eq 'ready' -and $r.checks.database -eq $true)
    } catch {
        return $false
    }
}

function Initialize-TenderIqDatabase {
    param(
        [string]$Root,
        [string]$VenvPython,
        [string]$ApiDir,
        [scriptblock]$LogFn
    )
    $rootEnv = Join-Path $Root '.env'
    Initialize-TenderIqMySql -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir -LogFn $LogFn
    if ((Get-TenderIqDatabaseDriverFromEnv -EnvPath $rootEnv) -eq 'mysql') {
        Invoke-TenderIqAlembicUpgrade -Root $Root -VenvPython $VenvPython -ApiDir $ApiDir -LogFn $LogFn
    } else {
        & $LogFn 'INFO' 'SQLite dev mode - schema created via ensure_database (no alembic required)'
    }
}


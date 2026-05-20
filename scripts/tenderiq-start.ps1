# TenderIQ - full local bootstrap (no Docker). Called by run.bat
$ErrorActionPreference = "Stop"

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$ApiDir = Join-Path $Root "apps\api"
$WebDir = Join-Path $Root "apps\web"
$LogDir = Join-Path $Root ".tenderiq"
$PidFile = Join-Path $LogDir "pids.json"
$LogFile = Join-Path $LogDir "startup.log"
$VenvPython = Join-Path $ApiDir "venv\Scripts\python.exe"
$VenvPip = Join-Path $ApiDir "venv\Scripts\pip.exe"

function Write-Log($level, $msg) {
    $line = "[{0}] {1}" -f $level, $msg
    Write-Host $line -ForegroundColor $(if ($level -eq 'ERROR') { 'Red' } elseif ($level -eq 'WARN') { 'Yellow' } else { 'Cyan' })
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
    Add-Content -Path $LogFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $line"
}

function Stop-ListenPort($port) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
}

function Remove-JsonBom($path) {
    if (-not (Test-Path $path)) { return }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $text = [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3)
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($path, $text, $utf8)
        Write-Log "INFO" "Removed UTF-8 BOM from $(Split-Path $path -Leaf)"
    }
}

function Ensure-Pnpm {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) { return }
    Write-Log "INFO" "Enabling pnpm via corepack..."
    if (-not (Get-Command corepack -ErrorAction SilentlyContinue)) {
        throw "pnpm not found. Install Node.js 20+ from https://nodejs.org then re-run run.bat"
    }
    corepack enable 2>$null | Out-Null
    Push-Location $Root
    corepack prepare pnpm@9.15.4 --activate 2>$null | Out-Null
    Pop-Location
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        throw "Could not activate pnpm. Run: corepack enable && corepack prepare pnpm@9.15.4 --activate"
    }
}

function Ensure-WorkspaceFile {
    $ws = Join-Path $Root "pnpm-workspace.yaml"
    if (Test-Path $ws) { return }
    Write-Log "INFO" "Creating pnpm-workspace.yaml..."
    @"
packages:
  - "apps/web"
  - "packages/*"
"@ | Set-Content $ws -Encoding utf8
}

function Ensure-EnvFileKeys {
    param([string]$EnvPath)
    $example = Join-Path $Root ".env.example"
    if (-not (Test-Path $EnvPath)) { return }
    $required = @(
        'SUPER_ADMIN_EMAIL=admin@tenderiq.com',
        'SUPER_ADMIN_PASSWORD=SuperAdmin@123',
        'DEMO_USER_EMAIL=demo@tenderiq.com',
        'DEMO_USER_PASSWORD=Demo@123',
        'DEMO_USER_ROLE=admin',
        'DEMO_USER_NAME=Demo User'
    )
    $content = Get-Content $EnvPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { $content = "" }
    $added = $false
    foreach ($line in $required) {
        $key = ($line -split '=', 2)[0]
        if ($content -notmatch "(?m)^\s*$([regex]::Escape($key))\s*=") {
            if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) { $content += "`n" }
            $content += "$line`n"
            $added = $true
        }
    }
    if ($added) {
        Set-Content -Path $EnvPath -Value $content.TrimEnd() -Encoding utf8
        Write-Log "INFO" "Added missing login credentials to .env (SUPER_ADMIN_*, DEMO_USER_*)"
    }
}

function Ensure-EnvFiles {
    $rootEnv = Join-Path $Root ".env"
    if (-not (Test-Path $rootEnv)) {
        Write-Log "INFO" "Creating .env from template..."
        Copy-Item (Join-Path $Root ".env.example") $rootEnv -ErrorAction SilentlyContinue
        if (-not (Test-Path $rootEnv)) {
            @"
# TenderIQ - local development (MySQL required for persistence)
NODE_ENV=development
DATABASE_URL=mysql+aiomysql://root:root@localhost:3306/tenderiq?charset=utf8mb4
JWT_SECRET=dev-secret-key-change-in-production-min-32chars
CLERK_SECRET_KEY=sk_test_placeholder
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
"@ | Set-Content $rootEnv -Encoding utf8
        }
    }

    Ensure-EnvFileKeys $rootEnv
    Sync-WebEnvLocal -ApiPort 8000
}

function Sync-WebEnvLocal {
    param([int]$ApiPort = 8000)
    $rootEnv = Join-Path $Root ".env"
    $webEnv = Join-Path $WebDir ".env.local"
    $pk = "pk_test_placeholder"
    $sk = "sk_test_placeholder"
    foreach ($line in Get-Content $rootEnv -ErrorAction SilentlyContinue) {
        if ($line -match '^CLERK_SECRET_KEY=(.+)$') { $sk = $Matches[1].Trim() }
        if ($line -match '^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=(.+)$') { $pk = $Matches[1].Trim() }
        if ($line -match '^CLERK_PUBLISHABLE_KEY=(.+)$') { $pk = $Matches[1].Trim() }
    }
    $content = @(
        "NEXT_PUBLIC_API_URL=http://localhost:$ApiPort"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$pk"
        "CLERK_SECRET_KEY=$sk"
    ) -join "`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($webEnv, $content + "`n", $utf8)
    Write-Log "INFO" "Synced apps/web/.env.local (API http://localhost:$ApiPort)"
}

function Resolve-ApiPort {
    Stop-ListenPort 8000
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
        Write-Log "WARN" "Port 8000 still in use (stale process). Using port 8002 for API."
        Stop-ListenPort 8002
        return 8002
    }
    return 8000
}

function Is-Truthy($value) {
    if ($null -eq $value) { return $false }
    return @("1", "true", "yes", "on") -contains $value.ToString().ToLowerInvariant()
}

# --- main ---
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
Set-Content -Path $LogFile -Value "TenderIQ startup $(Get-Date)`n"

Write-Log "INFO" "========== TenderIQ Startup =========="
$forceSetup = Is-Truthy $env:TENDERIQ_FORCE_SETUP
if ($forceSetup) {
    Write-Log "INFO" "Running in full setup mode (forced dependency install)"
}

Write-Log "INFO" "Checking Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ not in PATH. Install from https://python.org"
}
$pyVer = python --version 2>&1
Write-Log "INFO" "Python: $pyVer"

Write-Log "INFO" "Checking Node.js..."
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js not in PATH. Install Node 20+ from https://nodejs.org"
}
$nodeVer = node --version 2>&1
Write-Log "INFO" "Node: $nodeVer"
if ($nodeVer -match 'v(\d+)') {
    if ([int]$Matches[1] -lt 20) {
        throw "Node 20+ required (found $nodeVer)"
    }
}

Ensure-Pnpm
$pnpmVer = pnpm --version 2>&1
Write-Log "INFO" "pnpm: $pnpmVer"

Ensure-WorkspaceFile
Ensure-EnvFiles
Remove-JsonBom (Join-Path $WebDir "package.json")

Write-Log "INFO" "Setting up Python virtual environment..."
if (-not (Test-Path $VenvPython)) {
    Push-Location $ApiDir
    python -m venv venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }
    Pop-Location
}

Write-Log "INFO" "Installing Python dependencies..."
if ($forceSetup -or -not (Test-Path (Join-Path $ApiDir "venv\pyvenv.cfg"))) {
    & $VenvPython -m pip install --upgrade pip --quiet
    & $VenvPip install -r (Join-Path $ApiDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
} else {
    Write-Log "INFO" "Python dependencies already present, skipping pip install"
}

Write-Log "INFO" "Verifying backend imports..."
Push-Location $ApiDir
& $VenvPython -c "from src.main import app; assert app.title"
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Backend import check failed" }
Pop-Location
Write-Log "INFO" "Backend verification OK"

Write-Log "INFO" "Installing frontend dependencies (pnpm workspace)..."
Push-Location $Root
$modulesStamp = Join-Path $Root "node_modules\.modules.yaml"
$lockFile = Join-Path $Root "pnpm-lock.yaml"
$needsPnpmInstall = $forceSetup -or (-not (Test-Path $modulesStamp)) -or ((Get-Item $lockFile).LastWriteTimeUtc -gt (Get-Item $modulesStamp).LastWriteTimeUtc)
if ($needsPnpmInstall) {
    pnpm install --no-frozen-lockfile 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "pnpm-install.log") | Out-Null
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "pnpm install failed - see .tenderiq\pnpm-install.log" }
} else {
    Write-Log "INFO" "Node dependencies already present, skipping pnpm install"
}
Pop-Location

Write-Log "INFO" "Verifying Next.js..."
Push-Location $Root
pnpm --filter @tendoriq/web exec next --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Next.js not available after pnpm install"
}
Pop-Location
Write-Log "INFO" "Next.js verification OK"

Stop-ListenPort 3000
$apiPort = Resolve-ApiPort
Sync-WebEnvLocal -ApiPort $apiPort

function Get-LoginEnvBootstrap {
    param([string]$EnvPath)
    $keys = @(
        'SUPER_ADMIN_EMAIL', 'SUPER_ADMIN_PASSWORD',
        'DEMO_USER_EMAIL', 'DEMO_USER_PASSWORD', 'DEMO_USER_ROLE', 'DEMO_USER_NAME',
        'JWT_SECRET'
    )
    $bootstrap = "`$env:DOTENV_PATH='$EnvPath'"
    if (-not (Test-Path $EnvPath)) { return $bootstrap }
    $map = @{}
    foreach ($raw in Get-Content $EnvPath) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $map[$matches[1]] = $matches[2].Trim().Trim('"').Trim("'")
        }
    }
    foreach ($key in $keys) {
        if ($map.ContainsKey($key) -and $map[$key]) {
            $val = $map[$key] -replace "'", "''"
            $bootstrap += "; `$env:$key='$val'"
        }
    }
    return $bootstrap
}

Write-Log "INFO" "Starting backend on http://localhost:$apiPort ..."
$apiLog = Join-Path $LogDir "api.log"
$rootEnv = Join-Path $Root ".env"
$loginEnv = Get-LoginEnvBootstrap -EnvPath $rootEnv
$apiCmd = "Set-Location '$ApiDir'; $loginEnv; & '$VenvPython' -m uvicorn src.main:app --host 0.0.0.0 --port $apiPort --reload *>> '$apiLog'"
$apiProc = Start-Process powershell -ArgumentList @("-NoProfile", "-WindowStyle", "Hidden", "-Command", $apiCmd) -PassThru

Start-Sleep -Seconds 8

$webpackCache = Join-Path $WebDir ".next\cache\webpack"
if (Test-Path $webpackCache) {
    Write-Log "INFO" "Clearing webpack dev cache (prevents chunk load errors)..."
    Remove-Item -Recurse -Force $webpackCache -ErrorAction SilentlyContinue
}
if ($env:TENDERIQ_CLEAR_NEXT_CACHE -eq "1") {
    Write-Log "INFO" "Clearing full Next.js cache (.next)..."
    Remove-Item -Recurse -Force (Join-Path $WebDir ".next") -ErrorAction SilentlyContinue
}

Write-Log "INFO" "Starting frontend on http://localhost:3000 ..."
$webLog = Join-Path $LogDir "web.log"
$webCmd = "Set-Location '$Root'; pnpm --filter @tendoriq/web run dev *>> '$webLog'"
$webProc = Start-Process powershell -ArgumentList @("-NoProfile", "-WindowStyle", "Hidden", "-Command", $webCmd) -PassThru

@{
    api_pid = $apiProc.Id
    web_pid = $webProc.Id
    api_port = $apiPort
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content $PidFile -Encoding utf8

$apiOk = $false
$webOk = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    if (-not $apiOk) {
        try {
            $h = Invoke-RestMethod "http://127.0.0.1:$apiPort/health" -TimeoutSec 3
            if ($h.status -eq 'healthy') { $apiOk = $true }
        } catch {}
    }
    if (-not $webOk) {
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -lt 500) { $webOk = $true }
        } catch {
            if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -lt 500) {
                $webOk = $true
            }
        }
    }
    if ($apiOk -and $webOk) { break }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  TenderIQ" -ForegroundColor Green
Write-Host "  Backend:   http://localhost:$apiPort  $(if ($apiOk) { '[OK]' } else { '[starting...]' })" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:$apiPort/docs" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:3000  $(if ($webOk) { '[OK]' } else { '[check .tenderiq\web.log]' })" -ForegroundColor White
Write-Host "  Logs:      .tenderiq\api.log , web.log , startup.log" -ForegroundColor DarkGray
Write-Host "  Stop:      run.bat stop" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Green

if (-not $apiOk) {
    Write-Log "WARN" "API health check pending - see .tenderiq\api.log"
}
if (-not $webOk) {
    Write-Log "WARN" "Frontend not ready yet - see .tenderiq\web.log"
} else {
    $pk = $env:NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    if (-not $pk) {
        $webEnv = Join-Path $WebDir ".env.local"
        if (Test-Path $webEnv) {
            foreach ($line in Get-Content $webEnv) {
                if ($line -match '^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=(.+)$') { $pk = $Matches[1].Trim() }
            }
        }
    }
    if ($pk -match 'placeholder') {
        Write-Log "INFO" "Clerk not configured - sign in at /sign-in (SUPER_ADMIN_* or DEMO_USER_* in .env)"
    }
}

if (-not $apiOk) { exit 1 }

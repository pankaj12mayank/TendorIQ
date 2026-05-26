# Install api Python deps (requirements-dev.txt) into api/venv.
# Dot-sourced from tenderiq-bootstrap.ps1

function Test-TenderIqVenvHealthy {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiDir,
        [Parameter(Mandatory = $true)]
        [string]$VenvPython
    )
    if (-not (Test-Path $VenvPython)) {
        return $false
    }
    $cfg = Join-Path $ApiDir 'venv\pyvenv.cfg'
    if (Test-Path $cfg) {
        $raw = Get-Content $cfg -Raw -ErrorAction SilentlyContinue
        # venv moved from removed apps/api layout — pip launchers break
        if ($raw -match 'apps[\\/]api') {
            return $false
        }
    }
    & $VenvPython -m pip --version 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Repair-TenderIqVenv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiDir
    )
    $venvPath = Join-Path $ApiDir 'venv'
    if (Test-Path $venvPath) {
        Remove-Item -Recurse -Force $venvPath -ErrorAction Stop
    }
    Push-Location $ApiDir
    try {
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to create Python venv under api/venv'
        }
    } finally {
        Pop-Location
    }
}

function Install-TenderIqPythonDeps {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiDir,
        [Parameter(Mandatory = $true)]
        [string]$VenvPython,
        [string]$VenvPip,
        [switch]$Force
    )

    $reqFile = Join-Path $ApiDir 'requirements.txt'
    $reqDevFile = Join-Path $ApiDir 'requirements-dev.txt'
    if (-not (Test-Path $reqDevFile)) {
        throw "Missing $reqDevFile - run git pull or restore api/requirements-dev.txt"
    }

    $stamp = Join-Path $ApiDir 'venv\.deps.sha256'
    $hash = @(
        (Get-FileHash $reqFile -Algorithm SHA256).Hash
        (Get-FileHash $reqDevFile -Algorithm SHA256).Hash
    ) -join ':'

    $needs = $Force -or (-not (Test-Path $stamp)) -or ((Get-Content $stamp -Raw).Trim() -ne $hash)
    if (-not $needs) {
        return
    }

    # Always use python -m pip (pip.exe may point at old apps/api path after folder move)
    & $VenvPython -m pip install --upgrade pip --quiet
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }

    & $VenvPython -m pip install -r $reqDevFile
    if ($LASTEXITCODE -ne 0) { throw 'pip install -r requirements-dev.txt failed' }

    Set-Content -Path $stamp -Value $hash -Encoding ascii -NoNewline
}

function Test-TenderIqPythonDevTools {
    param([Parameter(Mandatory = $true)][string]$VenvPython)
    & $VenvPython -c "import pytest, ruff, mypy" 2>$null
    return $LASTEXITCODE -eq 0
}

function Test-TenderIqPythonRuntimeDeps {
    param([Parameter(Mandatory = $true)][string]$VenvPython)
    & $VenvPython -c "import aiosqlite, aiomysql, fastapi" 2>$null
    return $LASTEXITCODE -eq 0
}

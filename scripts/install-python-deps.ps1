# Install apps/api Python deps (requirements-dev.txt) into apps/api/venv.
# Dot-sourced from tenderiq-bootstrap.ps1

function Install-TenderIqPythonDeps {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApiDir,
        [Parameter(Mandatory = $true)]
        [string]$VenvPython,
        [Parameter(Mandatory = $true)]
        [string]$VenvPip,
        [switch]$Force
    )

    $reqFile = Join-Path $ApiDir 'requirements.txt'
    $reqDevFile = Join-Path $ApiDir 'requirements-dev.txt'
    if (-not (Test-Path $reqDevFile)) {
        throw "Missing $reqDevFile - run git pull or restore apps/api/requirements-dev.txt"
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

    & $VenvPython -m pip install --upgrade pip --quiet
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }

    & $VenvPip install -r $reqDevFile
    if ($LASTEXITCODE -ne 0) { throw 'pip install -r requirements-dev.txt failed' }

    Set-Content -Path $stamp -Value $hash -Encoding ascii -NoNewline
}

function Test-TenderIqPythonDevTools {
    param([Parameter(Mandatory = $true)][string]$VenvPython)
    & $VenvPython -c "import pytest, ruff, mypy" 2>$null
    return $LASTEXITCODE -eq 0
}

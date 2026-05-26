# TenderIQ Playwright E2E — requires API :8000 and web :3000
$ErrorActionPreference = 'Stop'
$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }

if (Test-Path (Join-Path $Root '.env')) {
    Get-Content (Join-Path $Root '.env') | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $name = $matches[1]
            if ($name -match '^(E2E_|NEXT_PUBLIC_API_URL|JWT_SECRET)') {
                $val = $matches[2].Trim().Trim('"').Trim("'")
                Set-Item -Path "env:$name" -Value $val
            }
        }
    }
}

$credFile = Join-Path $Root '.tenderiq\bootstrap-credentials.json'
if ((Test-Path $credFile) -and -not $env:E2E_DEMO_EMAIL) {
    $json = Get-Content $credFile -Raw | ConvertFrom-Json
    foreach ($acct in $json.accounts) {
        if ($acct.role -eq 'platform_admin' -and -not $env:E2E_ADMIN_EMAIL) {
            $env:E2E_ADMIN_EMAIL = $acct.email
            $env:E2E_ADMIN_PASSWORD = $acct.password
        }
        if ($acct.role -eq 'tenant_admin' -and -not $env:E2E_DEMO_EMAIL) {
            $env:E2E_DEMO_EMAIL = $acct.email
            $env:E2E_DEMO_PASSWORD = $acct.password
        }
    }
}

if (-not $env:E2E_DEMO_EMAIL) { $env:E2E_DEMO_EMAIL = 'demo@tendoriq.com' }
if (-not $env:E2E_DEMO_PASSWORD) {
    Write-Host '[FAIL] Set E2E_DEMO_PASSWORD or run run.bat once to create .tenderiq/bootstrap-credentials.json' -ForegroundColor Red
    exit 1
}

Push-Location (Join-Path $Root 'web')
try {
    pnpm exec playwright test @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}

# Run Playwright E2E (public + authenticated when API is up)
$ErrorActionPreference = "Stop"

$Root = if ($PSScriptRoot -match 'scripts$') { Split-Path $PSScriptRoot -Parent } else { $PSScriptRoot }
$rootEnv = Join-Path $Root ".env"

if (Test-Path $rootEnv) {
    Get-Content $rootEnv | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            if ($name -match '^(E2E_|DEMO_USER_|SUPER_ADMIN_|NEXT_PUBLIC_API_URL)') {
                Set-Item -Path "env:$name" -Value $value
            }
        }
    }
}

if (-not $env:E2E_API_URL) {
    $env:E2E_API_URL = if ($env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL } else { 'http://127.0.0.1:8000' }
}
if (-not $env:BASE_URL) {
    $env:BASE_URL = 'http://localhost:3000'
}
if (-not $env:E2E_DEMO_EMAIL -and $env:DEMO_USER_EMAIL) { $env:E2E_DEMO_EMAIL = $env:DEMO_USER_EMAIL }
if (-not $env:E2E_DEMO_PASSWORD -and $env:DEMO_USER_PASSWORD) { $env:E2E_DEMO_PASSWORD = $env:DEMO_USER_PASSWORD }
if (-not $env:E2E_ADMIN_EMAIL -and $env:SUPER_ADMIN_EMAIL) { $env:E2E_ADMIN_EMAIL = $env:SUPER_ADMIN_EMAIL }
if (-not $env:E2E_ADMIN_PASSWORD -and $env:SUPER_ADMIN_PASSWORD) { $env:E2E_ADMIN_PASSWORD = $env:SUPER_ADMIN_PASSWORD }

Write-Host "[e2e] API=$($env:E2E_API_URL) WEB=$($env:BASE_URL)" -ForegroundColor Cyan

Push-Location (Join-Path $Root "web")
pnpm exec playwright test
$code = $LASTEXITCODE
Pop-Location
exit $code


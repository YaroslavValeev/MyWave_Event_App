#Requires -Version 5.1
<#
.SYNOPSIS
  Safely reset Kazan 2026 SQLite DB: stop API on :8000 → seed --reset-db → start API.
.EXAMPLE
  pwsh -File scripts/reseed.ps1
#>
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $Root "services\api"
$VenvPython = "C:\tmp\mw_event_api_venv\Scripts\python.exe"
$VenvUvicorn = "C:\tmp\mw_event_api_venv\Scripts\uvicorn.exe"
$Seed = Join-Path $Root "scripts\seed_kazan_2026.py"

Write-Host "== MyWave Event App - reseed Kazan DB ==" -ForegroundColor Cyan

if (-not (Test-Path $VenvPython)) {
  throw "Venv not found: $VenvPython. Run scripts/dev.ps1 first."
}

Write-Host "Stopping MyWave API (port 8000 + orphan workers)..." -ForegroundColor Yellow
& (Join-Path $Root "scripts\stop-api.ps1")
if ($LASTEXITCODE -ne 0) {
  throw "Could not release DB lock. Close API/Web terminal windows from 'npm run dev', then retry."
}

$dbCandidates = @(
  (Join-Path $ApiDir "data\mywave_event.db"),
  (Join-Path $Root "data\mywave_event.db")
)
foreach ($db in $dbCandidates) {
  if (-not (Test-Path $db)) { continue }
  Write-Host "DB ready: $db" -ForegroundColor DarkGray
}

Write-Host "Running seed --reset-db..." -ForegroundColor Yellow
Push-Location $ApiDir
try {
  $env:PYTHONIOENCODING = "utf-8"
  $env:PYTHONPATH = $ApiDir
  & $VenvPython $Seed --reset-db
  if ($LASTEXITCODE -ne 0) {
    throw "Seed failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host "Starting API on http://127.0.0.1:8000 ..." -ForegroundColor Green
$apiCmd = @"
`$env:PYTHONPATH = '$ApiDir'
`$env:APP_ENV = 'development'
`$env:SECRET_KEY = 'local-dev-secret-change-me-32chars!!'
`$env:DATABASE_URL = 'sqlite:///./data/mywave_event.db'
`$env:CORS_ORIGINS = 'http://127.0.0.1:3000,http://localhost:3000'
`$env:OWNER_APPROVAL_EMAIL = 'y.valeev@gmail.com'
Set-Location '$ApiDir'
& '$VenvUvicorn' app.main:app --host 127.0.0.1 --port 8000
"@
$shell = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
  $shell = "pwsh"
}
Start-Process $shell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $apiCmd) | Out-Null
Start-Sleep -Seconds 3

try {
  $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 8
  Write-Host "API health: $($health.status) db_ok=$($health.db_ok)" -ForegroundColor Green
} catch {
  Write-Host "API started but health not ready yet - check the new terminal window." -ForegroundColor Yellow
}

Write-Host "Done. Web (if needed): npm run dev:web" -ForegroundColor Cyan

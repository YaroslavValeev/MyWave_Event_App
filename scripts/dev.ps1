#Requires -Version 5.1
<#
.SYNOPSIS
  One-command local start for MyWave Event App (API + Web).
.EXAMPLE
  powershell -File scripts/dev.ps1
#>
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $Root "services\api"
$WebDir = Join-Path $Root "apps\web"
$VenvPython = "C:\tmp\mw_event_api_venv\Scripts\python.exe"
$VenvUvicorn = "C:\tmp\mw_event_api_venv\Scripts\uvicorn.exe"

Write-Host "== MyWave Event App - local start ==" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $Root ".env"))) {
  Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
}
if (-not (Test-Path (Join-Path $WebDir ".env.local"))) {
  Copy-Item (Join-Path $WebDir ".env.example") (Join-Path $WebDir ".env.local")
}

if (-not (Test-Path $VenvUvicorn)) {
  Write-Host "Creating ASCII venv at C:\tmp\mw_event_api_venv ..." -ForegroundColor Yellow
  python -m venv "C:\tmp\mw_event_api_venv"
  & "C:\tmp\mw_event_api_venv\Scripts\python.exe" -m pip install --upgrade pip
  & "C:\tmp\mw_event_api_venv\Scripts\python.exe" -m pip install `
    --trusted-host pypi.org --trusted-host files.pythonhosted.org `
    -r (Join-Path $ApiDir "requirements.txt")
}

if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
  Write-Host "Installing web dependencies..." -ForegroundColor Yellow
  Push-Location $WebDir
  npm install
  Pop-Location
}

New-Item -ItemType Directory -Force -Path (Join-Path $ApiDir "data") | Out-Null

$apiCmd = @"
`$env:PYTHONPATH = '$ApiDir'
`$env:APP_ENV = 'development'
`$env:SECRET_KEY = 'local-dev-secret-change-me-32chars!!'
`$env:DATABASE_URL = 'sqlite:///./data/mywave_event.db'
`$env:CORS_ORIGINS = 'http://127.0.0.1:3000,http://localhost:3000'
Set-Location '$ApiDir'
& '$VenvUvicorn' app.main:app --host 127.0.0.1 --port 8000
"@

$webCmd = @"
Set-Location '$WebDir'
npm run dev -- --hostname 127.0.0.1 --port 3000
"@

Write-Host "API  -> http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "Web  -> http://127.0.0.1:3000" -ForegroundColor Green
Write-Host "Docs -> http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Stop: close both windows or Ctrl+C in each." -ForegroundColor DarkGray
Write-Host "Reseed DB: close API window first, then npm run reseed" -ForegroundColor DarkGray

# Prefer Windows PowerShell 5.1 (always present); pwsh if available.
$shell = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
  $shell = "pwsh"
}

Start-Process $shell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $apiCmd) | Out-Null
Start-Sleep -Seconds 2
Start-Process $shell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $webCmd) | Out-Null

Write-Host "Started API and Web in separate terminals." -ForegroundColor Cyan

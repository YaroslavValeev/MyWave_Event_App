#Requires -Version 5.1
<#
.SYNOPSIS
  One-command local start for MyWave Event App (API + Web).
  Auto-picks API port: 8000 if free, else 8010 (Docker often holds 8000).
.EXAMPLE
  powershell -File scripts/dev.ps1
#>
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $Root "services\api"
$WebDir = Join-Path $Root "apps\web"
$VenvPython = "C:\tmp\mw_event_api_venv\Scripts\python.exe"
$VenvUvicorn = "C:\tmp\mw_event_api_venv\Scripts\uvicorn.exe"

function Test-PortFree([int]$Port) {
  $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  return -not $c
}

Write-Host "== MyWave Event App - local start ==" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $Root ".env"))) {
  Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
}

$ApiPort = 8000
if (-not (Test-PortFree 8000)) {
  if (Test-PortFree 8010) {
    $ApiPort = 8010
    Write-Host "Port 8000 busy (often Docker) -> API on 8010" -ForegroundColor Yellow
  } else {
    throw "Ports 8000 and 8010 are busy. Free one, then retry."
  }
}

$ApiBase = "http://127.0.0.1:$ApiPort"
$webEnvLocal = Join-Path $WebDir ".env.local"
@(
  "NEXT_PUBLIC_API_BASE_URL=$ApiBase"
  "NEXT_PUBLIC_APP_NAME=MyWave Event App"
) | Set-Content -Path $webEnvLocal -Encoding UTF8
Write-Host "Wrote $webEnvLocal -> $ApiBase" -ForegroundColor DarkGray

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
& '$VenvUvicorn' app.main:app --host 127.0.0.1 --port $ApiPort
"@

$webCmd = @"
Set-Location '$WebDir'
npm run dev -- --hostname 127.0.0.1 --port 3000
"@

Write-Host "API  -> $ApiBase/health" -ForegroundColor Green
Write-Host "Web  -> http://127.0.0.1:3000" -ForegroundColor Green
Write-Host "Docs -> $ApiBase/docs" -ForegroundColor Green
Write-Host "Stop: close both windows or Ctrl+C in each." -ForegroundColor DarkGray
Write-Host "Dry-run: powershell -File .\scripts\dry_run_kazan.ps1 -ApiBase $ApiBase" -ForegroundColor DarkGray

$shell = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
  $shell = "pwsh"
}

Start-Process $shell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $apiCmd) | Out-Null
Start-Sleep -Seconds 2
Start-Process $shell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $webCmd) | Out-Null

Write-Host "Started API and Web in separate terminals." -ForegroundColor Cyan
